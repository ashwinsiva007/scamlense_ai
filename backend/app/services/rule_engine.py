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
    """Loads and validates all *.yaml rule definitions from backend/rules/ at startup."""
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
                if isinstance(pack_data, dict) and "rules" in pack_data and "category" in pack_data:
                    packs.append(pack_data)
                else:
                    logger.warning(f"Rule pack {yf} missing 'category' or 'rules'")
        except Exception as e:
            logger.error(f"Error loading rule pack {yf}: {e}")

    _RULE_PACKS = packs
    return _RULE_PACKS


def normalize_text(text: str) -> str:
    """Normalizes text with Unicode NFKC, lowercasing, and whitespace collapsing."""
    if not text:
        return ""
    nfkc = unicodedata.normalize("NFKC", text)
    lowered = nfkc.lower()
    collapsed = re.sub(r"\s+", " ", lowered)
    return collapsed.strip()


def find_exact_evidence_substring(raw_text: str, regex_pattern: str) -> Optional[str]:
    """
    Executes regex search on raw text and returns the exact verbatim substring match.
    Ensures that the evidence quote is an authentic, unmodified slice of user text.
    """
    if not raw_text:
        return None
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
def infer_scam_type(
    fired_rule_ids: Set[str],
    category_scores: Dict[str, float],
    extracted: ExtractedData,
) -> Optional[str]:
    """Infers the scam archetype based on strongest categories, fired signals, and extracted entities."""
    if not any(s > 0 for s in category_scores.values()) and not fired_rule_ids:
        return None

    # Find highest positive scoring category
    sorted_cats = sorted(category_scores.items(), key=lambda item: item[1], reverse=True)
    top_cat = sorted_cats[0][0] if sorted_cats and sorted_cats[0][1] > 0 else None
    msg_lower = (extracted.message_text or "").lower()

    # 1. Fake Payment Screenshot
    if top_cat == "payment_screenshot" or any(r.startswith("PAY_") for r in fired_rule_ids) or extracted.document_type == "payment_confirmation":
        return "fake_payment"

    # 2. Fake Job / Internship Fee
    if (
        any(r in fired_rule_ids for r in ("MONEY_JOB_REGISTRATION_FEE", "TOO_GOOD_HIGH_PAY_NO_INTERVIEW", "SENDER_MOVE_TO_PRIVATE_MESSAGING"))
        or (top_cat in ("money_demands", "too_good") and any(k in msg_lower for k in ("job", "internship", "salary", "hiring", "candidate", "interview")))
    ):
        return "fake_job_offer"

    # 3. OTP / KYC Phishing
    if (
        top_cat == "credentials"
        or any(r in fired_rule_ids for r in (
            "CRED_OTP_SOLICITATION", "CRED_UPI_PIN_RECEIVE_DECEPTION", "IMPERSONATION_BANK_KYC",
            "CRED_CARD_CVV_EXPIRY", "CRED_NETBANKING_PASSWORD", "CRED_AADHAAR_PAN_HARVESTING"
        ))
    ):
        return "otp_kyc_phishing"

    # 4. Courier Delivery Scam
    if (
        "IMPERSONATION_FAKE_COURIER" in fired_rule_ids
        or "MONEY_COURIER_REROUTE_FEE" in fired_rule_ids
        or any(k in msg_lower for k in ("parcel", "courier", "package", "india post", "delivery address"))
    ):
        return "courier_scam"

    # 5. Lottery / Prize Scheme
    if "TOO_GOOD_LOTTERY_PRIZE" in fired_rule_ids or "MONEY_PRIZE_CUSTOMS_FEE" in fired_rule_ids or "lottery" in msg_lower or "lucky draw" in msg_lower:
        return "lottery_prize"

    # 6. Investment / Task Scheme
    if any(r in fired_rule_ids for r in ("TOO_GOOD_DAILY_TASKS_YOUTUBE", "TOO_GOOD_GUARANTEED_RETURNS", "TOO_GOOD_CRYPTO_DOUBLING")) or "task" in msg_lower:
        return "investment_task_scam"

    # Other threats (utility disconnection, digital arrest, sim block)
    if any(r in fired_rule_ids for r in ("URGENCY_ELECTRICITY_POWER_CUT", "URGENCY_POLICE_LEGAL_ARREST", "URGENCY_SIM_DEACTIVATION", "IMPERSONATION_TELECOM_SIM", "IMPERSONATION_GOV_DEPARTMENT")):
        return "other"

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
    1. Check for insufficient readable content.
    2. Match rules against message_text, sender, urls, and visual_notes.
    3. Every fired rule must have exact substring evidence in extracted content; otherwise drop it.
    4. Per-category cap: maximum +45 points per category.
    5. Model-suggested signals capped at +10 points total.
    6. Reducers: link matches verified brand domain only applied if NO money or credential requests.
    7. Final score clamped 0 to 100.
    8. Band calibrated: 0-29 low_risk, 30-59 suspicious, 60-100 likely_scam.
    """
    raw_text = extracted.message_text or ""
    sender_text = extracted.sender or ""
    urls_text = " ".join(extracted.urls)
    visual_text = " ".join(extracted.visual_notes)

    # 1. Insufficient Information Check
    if len(raw_text.strip()) < 10 and extracted.image_quality == "low" and not extracted.urls and not extracted.upi_ids:
        return 0, "insufficient_info", [], None, "low"

    # Searchable text corpuses
    searchable_corpuses = [
        raw_text,
        sender_text,
        urls_text,
        visual_text,
        " ".join(extracted.phone_numbers),
        " ".join(extracted.upi_ids),
        " ".join(extracted.amounts),
    ]
    all_combined_text = " ".join(searchable_corpuses)

    packs = load_rule_packs()
    candidate_signals: List[Signal] = []
    fired_rule_ids: Set[str] = set()

    # 2. Evaluate YAML Rule Packs
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
                candidate_signals.append(sig)

    # 3. Integrate Tool Signals (source='tool')
    if tool_signals:
        for ts in tool_signals:
            if ts.id not in fired_rule_ids:
                fired_rule_ids.add(ts.id)
                candidate_signals.append(ts)

    # 4. Integrate Model Signals (source='model')
    model_score_contrib = 0.0
    if model_signals:
        for ms in model_signals:
            # Evidence MUST be an exact verbatim substring of message_text or corpuses
            if ms.evidence and ms.evidence in all_combined_text and ms.id not in fired_rule_ids:
                fired_rule_ids.add(ms.id)
                model_score_contrib += max(0.0, ms.weight)
                candidate_signals.append(ms)

    # Cap model contribution at +10 points total
    capped_model_points = min(10.0, model_score_contrib)

    # 5. Evidence Verification: Drop any signal whose evidence cannot be found in extracted text
    verified_signals: List[Signal] = []
    for sig in candidate_signals:
        if sig.evidence and (sig.evidence in all_combined_text or any(sig.evidence in c for c in searchable_corpuses)):
            verified_signals.append(sig)
        else:
            # For tool signals with formatted note (e.g. "example.com (verified official Google domain)"), check primary token
            evidence_key = sig.evidence.split()[0] if sig.evidence else ""
            if evidence_key and any(evidence_key in c for c in searchable_corpuses):
                sig.evidence = evidence_key
                verified_signals.append(sig)
            else:
                logger.debug(f"Dropping signal {sig.id}: evidence not found in extracted text")

    # 6. Compute Category Totals (to check for money_demands / credentials presence)
    preliminary_cat_scores: Dict[str, float] = {}
    for sig in verified_signals:
        if sig.source == "model":
            continue
        if sig.weight > 0:
            preliminary_cat_scores[sig.category] = preliminary_cat_scores.get(sig.category, 0.0) + sig.weight

    # Reducer Rule: link exactly matches verified brand domain AND no money or credential request (-15)
    has_money_or_credentials = (
        preliminary_cat_scores.get("money_demands", 0.0) > 0
        or preliminary_cat_scores.get("credentials", 0.0) > 0
    )

    fired_signals: List[Signal] = []
    category_scores: Dict[str, float] = {}
    reducer_total = 0.0

    for sig in verified_signals:
        if sig.id == "REDUCER_VERIFIED_BRAND_DOMAIN" and has_money_or_credentials:
            # Exclude reducer if money or credential demands were detected
            logger.info("Dropping REDUCER_VERIFIED_BRAND_DOMAIN: money or credentials demand present")
            continue

        fired_signals.append(sig)

        if sig.source == "model":
            continue

        if sig.weight < 0:
            reducer_total += abs(sig.weight)
        else:
            category_scores[sig.category] = category_scores.get(sig.category, 0.0) + sig.weight

    # 7. Apply Per-Category +45 Cap
    capped_rule_score = 0.0
    for cat, total in category_scores.items():
        capped_val = min(45.0, total)
        capped_rule_score += capped_val

    # Final raw score calculation clamped to 0-100
    raw_final_score = capped_rule_score + capped_model_points - reducer_total
    final_score = int(round(max(0.0, min(100.0, raw_final_score))))

    # 8. Calibrate Band
    if final_score < 30:
        band: BandType = "low_risk"
    elif final_score < 60:
        band: BandType = "suspicious"
    else:
        band: BandType = "likely_scam"

    # 9. Infer Scam Type from strongest categories
    active_fired_ids = {s.id for s in fired_signals}
    scam_type = infer_scam_type(active_fired_ids, category_scores, extracted)

    # 10. Calibrate Confidence Level
    tools_failed = any(tr.status == "error" for tr in (tool_results or []))
    is_short_text = len(raw_text.strip()) < 20
    is_low_quality = extracted.image_quality == "low"
    num_positive_categories = len([c for c, s in category_scores.items() if s > 0])

    if is_low_quality or is_short_text or tools_failed:
        confidence: ConfidenceType = "low"
    elif num_positive_categories >= 2 or (
        extracted.image_quality in ("high", "sharp", "text_only") and not tools_failed
    ):
        confidence = "high"
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
