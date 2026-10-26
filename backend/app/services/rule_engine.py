"""
Rule Engine Service
-------------------
Evaluates declarative YAML rule packs against extracted entities, message text, and verifier outputs.
Computes a deterministic, explainable risk score (0-100) using transparent weights,
per-category caps (+45 max per category), exact substring evidence extraction,
reducer signals, and model signal capping (+10 max total).
"""

import glob
import logging
import os
import re
import unicodedata
from typing import Dict, List, Optional, Tuple, Set

import yaml

from app.schemas import BandType, ConfidenceType, ExtractedData, Signal, ToolResult

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Rule Pack Cache & Loader
# ------------------------------------------------------------------------------
_RULE_PACKS: Optional[List[Dict]] = None

def load_rule_packs() -> List[Dict]:
    """Loads all *.yaml rule definitions from backend/rules/."""
    global _RULE_PACKS
    if _RULE_PACKS is not None:
        return _RULE_PACKS

    rules_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "rules"))
    yaml_files = glob.glob(os.path.join(rules_dir, "*.yaml"))

    packs = []
    for yf in sorted(yaml_files):
        try:
            with open(yf, "r", encoding="utf-8") as f:
                pack_data = yaml.safe_load(f)
                if isinstance(pack_data, dict) and "rules" in pack_data:
                    packs.append(pack_data)
        except Exception as e:
            logger.error(f"Error loading rule pack {yf}: {e}")

    _RULE_PACKS = packs
    return _RULE_PACKS


def normalize_text(text: str) -> str:
    """Normalizes text with NFKC, lowercasing, and whitespace collapsing."""
    if not text:
        return ""
    nfkc = unicodedata.normalize("NFKC", text)
    # Collapse multiple whitespace characters into single space
    collapsed = re.sub(r"\s+", " ", nfkc)
    return collapsed.strip()


def find_exact_evidence_substring(raw_text: str, regex_pattern: str) -> Optional[str]:
    """
    Executes regex search on raw text and returns the exact verbatim substring match.
    Ensures that the evidence quote is an authentic, unmodified slice of user text.
    """
    try:
        match = re.search(regex_pattern, raw_text, re.IGNORECASE)
        if match:
            # Return the exact verbatim slice from the original text
            return raw_text[match.start():match.end()]
    except re.error:
        pass
    return None


# ------------------------------------------------------------------------------
# Archetype Inference
# ------------------------------------------------------------------------------
def infer_scam_type(fired_rule_ids: Set[str], extracted: ExtractedData) -> Optional[str]:
    """Infers the scam archetype based on fired signals and extracted entities."""
    # Fake Job Offer
    if any(r in fired_rule_ids for r in ("MD_JOB_REGISTRATION_FEE", "TOO_GOOD_HIGH_PAY_NO_INTERVIEW", "SENDER_MOVE_TO_PRIVATE_MESSAGING")):
        return "fake_job_offer"

    # Task Scam / Investment Scheme
    if any(r in fired_rule_ids for r in ("TOO_GOOD_DAILY_TASKS_YOUTUBE", "TOO_GOOD_GUARANTEED_RETURNS", "TOO_GOOD_CRYPTO_DOUBLING")):
        return "investment_task_scam"

    # Fake Payment Screenshot
    if any(r.startswith("PAY_") for r in fired_rule_ids) or extracted.document_type == "payment_confirmation":
        return "fake_payment"

    # OTP / KYC Phishing
    if any(r in fired_rule_ids for r in ("CRED_OTP_SOLICITATION", "CRED_UPI_PIN_RECEIVE_DECEPTION", "IMPERSONATION_BANK_KYC", "CRED_CARD_CVV_EXPIRY", "CRED_NETBANKING_PASSWORD")):
        return "otp_kyc_phishing"

    # Courier Delivery Scam
    if "IMPERSONATION_FAKE_COURIER" in fired_rule_ids or "UT_PACKAGE_RETURN_FEES" in fired_rule_ids or "MD_PARCEL_CUSTOMS_RELEASE" in fired_rule_ids:
        return "courier_scam"

    # Lottery / Lucky Draw
    if "TOO_GOOD_LOTTERY_PRIZE" in fired_rule_ids:
        return "lottery_prize"

    # Electricity / Utility Threat
    if "UT_POWER_ELECTRICITY_DISCONNECT" in fired_rule_ids:
        return "electricity_disconnection"

    # Digital Arrest / Law Enforcement
    if "UT_DIGITAL_ARREST_LEGAL" in fired_rule_ids or "IMPERSONATION_GOV_DEPARTMENT" in fired_rule_ids:
        return "digital_arrest_scam"

    # Telecom / SIM Block
    if "IMPERSONATION_TELECOM_SIM" in fired_rule_ids or "UT_SIM_CARD_DEACTIVATION" in fired_rule_ids:
        return "telecom_sim_scam"

    if len(fired_rule_ids) > 0:
        return "other"

    return None


# ------------------------------------------------------------------------------
# Core Rule Engine Evaluation
# ------------------------------------------------------------------------------
def evaluate_rules(
    extracted: ExtractedData,
    tool_results: Optional[List[ToolResult]] = None,
    tool_signals: Optional[List[Signal]] = None,
    model_signals: Optional[List[Signal]] = None,
) -> Tuple[int, BandType, List[Signal], Optional[str], ConfidenceType]:
    """
    Evaluates YAML rules, integrates tool signals and model suggestions.

    Rules applied:
    1. Every fired rule must have exact substring evidence in extracted content.
    2. Per-category cap: maximum +45 points per category.
    3. Model-suggested signals capped at +10 points total.
    4. Negative reducer signals applied.
    5. Final score clamped 0 to 100.
    6. Band calibrated: 0-29 low_risk, 30-59 suspicious, 60-100 likely_scam.
    """
    raw_text = extracted.message_text or ""
    sender_text = extracted.sender or ""
    urls_text = " ".join(extracted.urls)
    visual_text = " ".join(extracted.visual_notes)

    # Searchable text corpuses
    searchable_corpuses = [
        raw_text,
        sender_text,
        urls_text,
        visual_text,
    ]

    packs = load_rule_packs()
    fired_signals: List[Signal] = []
    fired_rule_ids: Set[str] = set()

    # Category score accumulator for positive weights
    category_scores: Dict[str, float] = {}
    reducer_total = 0.0

    # 1. Evaluate YAML Rule Packs
    for pack in packs:
        pack_category = pack.get("category", "other")
        rules = pack.get("rules", [])

        for rule in rules:
            rid = rule["id"]
            if rid in fired_rule_ids:
                continue

            patterns_dict = rule.get("patterns", {})
            rule_weight = float(rule.get("weight", 0.0))

            matched_evidence: Optional[str] = None

            # Check patterns across all languages
            for lang, patterns in patterns_dict.items():
                if matched_evidence:
                    break
                for pat in patterns:
                    for corpus in searchable_corpuses:
                        if not corpus:
                            continue
                        ev = find_exact_evidence_substring(corpus, pat)
                        if ev:
                            matched_evidence = ev
                            break
                    if matched_evidence:
                        break

            if matched_evidence:
                fired_rule_ids.add(rid)
                sig = Signal(
                    id=rid,
                    label=rule["label"],
                    category=pack_category,
                    weight=rule_weight,
                    evidence=matched_evidence,
                    source="rule",
                )
                fired_signals.append(sig)

    # 2. Integrate Tool Signals (source='tool')
    if tool_signals:
        for ts in tool_signals:
            if ts.id not in fired_rule_ids:
                fired_rule_ids.add(ts.id)
                fired_signals.append(ts)

    # 3. Integrate Model Signals (source='model')
    # Filter: evidence MUST be an exact verbatim substring of message_text
    model_score_contrib = 0.0
    if model_signals:
        for ms in model_signals:
            if ms.evidence and ms.evidence in raw_text and ms.id not in fired_rule_ids:
                fired_rule_ids.add(ms.id)
                # Keep original weight on signal object for display, but track capped score contribution
                model_score_contrib += max(0.0, ms.weight)
                fired_signals.append(ms)

    # Cap model contribution at +10 points total
    capped_model_points = min(10.0, model_score_contrib)

    # 4. Compute Per-Category Scores with +45 Cap
    for sig in fired_signals:
        if sig.source == "model":
            continue  # Handled separately via capped_model_points

        cat = sig.category
        if sig.weight < 0:
            # Reducer
            reducer_total += abs(sig.weight)
        else:
            current_cat_sum = category_scores.get(cat, 0.0)
            category_scores[cat] = current_cat_sum + sig.weight

    # Apply per-category +45 cap
    capped_rule_score = 0.0
    for cat, total in category_scores.items():
        capped_val = min(45.0, total)
        capped_rule_score += capped_val

    # Final raw score calculation
    raw_final_score = capped_rule_score + capped_model_points - reducer_total
    final_score = int(round(max(0.0, min(100.0, raw_final_score))))

    # 5. Calibrate Band
    if final_score < 30:
        band: BandType = "low_risk"
    elif final_score < 60:
        band: BandType = "suspicious"
    else:
        band: BandType = "likely_scam"

    # 6. Infer Scam Type
    scam_type = infer_scam_type(fired_rule_ids, extracted)

    # 7. Calibrate Confidence Level
    # High confidence: multiple independent categories fired, or high image quality with definitive checks
    num_positive_categories = len([c for c, s in category_scores.items() if s > 0])
    if num_positive_categories >= 2 or (final_score == 0 and extracted.image_quality in ("high", "sharp", "text_only")):
        confidence: ConfidenceType = "high"
    elif extracted.image_quality == "low":
        confidence = "low"
    else:
        confidence = "medium"

    return final_score, band, fired_signals, scam_type, confidence


def hook_rules(
    extracted: ExtractedData,
    tool_results: Optional[List[ToolResult]] = None,
    tool_signals: Optional[List[Signal]] = None,
    model_signals: Optional[List[Signal]] = None,
) -> Tuple[int, BandType, List[Signal]]:
    """
    Backward-compatible hook signature returning (score, band, signals).
    """
    score, band, signals, _, _ = evaluate_rules(
        extracted=extracted,
        tool_results=tool_results,
        tool_signals=tool_signals,
        model_signals=model_signals,
    )
    return score, band, signals
