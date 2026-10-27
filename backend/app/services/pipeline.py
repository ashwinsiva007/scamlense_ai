"""
Pipeline Service
----------------
Orchestrates the end-to-end multi-stage fraud analysis pipeline:
Validate Input -> Multimodal Entity Extraction -> External Verifiers ->
Deterministic Rule Engine -> Localized Explainer -> Safety Verification.

Stateless execution: uploads are processed strictly in memory and zero images or text are stored.
"""

import time
from typing import List, Optional
import uuid

from app.config import settings
from app.schemas import (
    AnalyzeResponse,
    ConfidenceType,
    ExtractedData,
    LanguageType,
    ModeType,
    Signal,
    ToolResult,
)
from app.services.explainer import hook_explain
from app.services.extractor import extract_content
from app.services.file_utils import process_uploaded_file
from app.services.image_utils import validate_and_process_image
from app.services.link_checker import is_likely_url, run_link_checker
from app.services.model_client import ModelClient, get_model_client
from app.services.rule_engine import evaluate_rules
from app.services.verifiers import run_verifiers


LIMITATIONS_BY_LANG = {
    "en": (
        "This assessment is based exclusively on the provided text and imagery. "
        "Absence of detected red flags does not guarantee authenticity. "
        "ScamLens never stores uploads or logs personal data."
    ),
    "ta": (
        "இந்த மதிப்பீடு வழங்கப்பட்ட உரை மற்றும் படங்களின் அடிப்படையில் மட்டுமே அமைந்துள்ளது. "
        "மோசடி அறிகுறிகள் இல்லாதது முழுமையான நம்பகத்தன்மைக்கு உத்தரவாதம் அளிக்காது. "
        "ஸ்கேம்லென்ஸ் உங்கள் பதிவேற்றங்களை ஒருபோதும் சேமிப்பதில்லை."
    ),
    "hi": (
        "यह मूल्यांकन केवल दिए गए टेक्स्ट और स्क्रीनशॉट पर आधारित है। "
        "किसी भी लाल झंडे की अनुपस्थिति पूर्ण प्रामाणिकता की गारंटी नहीं देती है। "
        "स्कैम लेंस आपके डेटा को कभी भी सहेजता या संग्रहीत नहीं करता है।"
    ),
}


async def run_pipeline(
    image_bytes: Optional[bytes] = None,
    filename: Optional[str] = None,
    text: Optional[str] = None,
    language: LanguageType = "en",
    mode: Optional[ModeType] = None,
    model_client: Optional[ModelClient] = None,
) -> AnalyzeResponse:
    """
    Executes the end-to-end analysis pipeline:
    1. Validates and preprocesses image bytes in memory (or handles text-only).
    2. Runs multimodal AI entity extraction (Gemma 4 / Gemini Cloud / Ollama / Mock).
    3. Runs external verifiers (SSRF-protected unshortener, RDAP, threat feeds, lookalike check).
    4. Evaluates declarative YAML rules + tool signals + capped model signals in Rule Engine.
    5. Generates localized explanations, next steps, and Family Alert card.
    6. Assembles strict AnalyzeResponse with microsecond timing benchmarks.
    """
    t_start = time.perf_counter()
    active_mode = (mode or settings.MODE).lower()
    active_lang = language if language in ("en", "ta", "hi") else "en"

    timings = {
        "validation": 0,
        "extraction": 0,
        "verifiers": 0,
        "rules": 0,
        "explanation": 0,
        "total": 0,
    }

    # Step 1: Input Validation & Image / Document Processing
    t_val_start = time.perf_counter()
    processed_image_bytes: Optional[bytes] = None
    image_quality: str = "text_only"
    extracted_doc_text: str = ""
    doc_urls: List[str] = []
    doc_notes: List[str] = []
    doc_sender: Optional[str] = None
    doc_type: Optional[str] = None

    if image_bytes is not None and len(image_bytes) > 0:
        file_input = process_uploaded_file(raw_bytes=image_bytes, filename=filename)
        if file_input.images:
            processed_image_bytes, image_quality = file_input.images[0]
        if file_input.extracted_text:
            extracted_doc_text = file_input.extracted_text
        if file_input.hyperlinks:
            doc_urls = file_input.hyperlinks
        if file_input.notes:
            doc_notes = file_input.notes
        if file_input.sender:
            doc_sender = file_input.sender
        if file_input.document_type:
            doc_type = file_input.document_type

    effective_text: Optional[str] = None
    if extracted_doc_text and text:
        effective_text = f"{extracted_doc_text}\n\n{text}".strip()
    elif extracted_doc_text:
        effective_text = extracted_doc_text
    elif text:
        effective_text = text.strip()

    timings["validation"] = max(1, int((time.perf_counter() - t_val_start) * 1000))

    # Step 2: Multimodal Extraction
    t_ext_start = time.perf_counter()
    extracted = await extract_content(
        image_bytes=processed_image_bytes,
        raw_text=effective_text,
        image_quality=image_quality,
        mode=active_mode,
        model_client=model_client,
    )

    # Post-process extracted fields with document metadata
    if doc_type and (not extracted.document_type or extracted.document_type in ("unknown", "other")):
        extracted.document_type = doc_type
    if doc_sender and not extracted.sender:
        extracted.sender = doc_sender
    if doc_urls:
        for u in doc_urls:
            if u not in extracted.urls:
                extracted.urls.append(u)
    if doc_notes:
        for n in doc_notes:
            if n not in extracted.visual_notes:
                extracted.visual_notes.append(n)

    timings["extraction"] = max(1, int((time.perf_counter() - t_ext_start) * 1000))

    # Step 3: Check for Insufficient Information
    # If extraction yielded very little text (<10 chars) without any links or image quality is deemed low
    has_urls = bool(extracted.urls) or is_likely_url(extracted.message_text)
    is_sparse_text = len(extracted.message_text.strip()) < 10 and not has_urls
    is_low_quality = extracted.image_quality == "low"

    if is_sparse_text or is_low_quality:
        band = "insufficient_info"
        score = 0
        confidence: ConfidenceType = "low"
        scam_type = None
        signals: List[Signal] = []
        tool_results: List[ToolResult] = []

        t_exp_start = time.perf_counter()
        explanation, next_steps, family_alert = await hook_explain(
            band=band,
            score=score,
            signals=signals,
            tool_results=tool_results,
            language=active_lang,
            mode=active_mode,
            scam_type=scam_type,
            model_client=model_client,
            extracted=extracted,
        )
        timings["explanation"] = max(1, int((time.perf_counter() - t_exp_start) * 1000))
    else:
        # Step 4: External Verifiers & Heuristic Link Checker
        t_ver_start = time.perf_counter()
        tool_results, tool_signals = await run_verifiers(
            extracted,
            image_bytes=processed_image_bytes or image_bytes,
        )
        link_results, link_signals = run_link_checker(extracted)
        tool_results.extend(link_results)
        tool_signals.extend(link_signals)
        timings["verifiers"] = max(1, int((time.perf_counter() - t_ver_start) * 1000))

        # Step 5: Deterministic Rule Engine Scoring
        t_rule_start = time.perf_counter()
        score, band, signals, scam_type, confidence = evaluate_rules(
            extracted=extracted,
            tool_results=tool_results,
            tool_signals=tool_signals,
            model_signals=None,
        )
        timings["rules"] = max(1, int((time.perf_counter() - t_rule_start) * 1000))

        # Step 6: Explainer & Safety Post-Check
        t_exp_start = time.perf_counter()
        explanation, next_steps, family_alert = await hook_explain(
            band=band,
            score=score,
            signals=signals,
            tool_results=tool_results,
            language=active_lang,
            mode=active_mode,
            scam_type=scam_type,
            model_client=model_client,
            extracted=extracted,
        )
        timings["explanation"] = max(1, int((time.perf_counter() - t_exp_start) * 1000))

    timings["total"] = max(1, int((time.perf_counter() - t_start) * 1000))

    # Map risk_level and summary per Section 8 & 9
    risk_level = (
        "low" if score < 25
        else "caution" if score < 50
        else "high" if score < 75
        else "very_high"
    )

    msg_lower = (extracted.message_text or "").lower()
    is_payment = (
        extracted.document_type in ("payment_screenshot", "payment_receipt", "payment_confirmation")
        or bool(scam_type and "payment" in scam_type.lower())
        or any(s.category == "payment_screenshot" for s in signals)
        or any(w in msg_lower for w in ["payment", "paid", "receipt", "upi ref", "transaction"])
    )

    if band == "insufficient_info":
        summary = (
            "We could not reliably assess this screenshot. Upload a clearer image or provide additional context."
            if active_lang == "en" else explanation
        )
        category = "unknown_evidence"
    elif band == "low_risk":
        if is_payment:
            summary = (
                "Low risk indicators found. We did not identify significant scam indicators in the available evidence. "
                "This does not prove the message or transaction is genuine. The screenshot appears consistent with a payment "
                "confirmation, but the actual transaction has not been independently verified."
                if active_lang == "en" else explanation
            )
            category = "payment_receipt"
        else:
            summary = (
                "Low risk indicators found. We did not identify significant scam indicators in the available evidence. "
                "This does not prove the message or transaction is genuine."
                if active_lang == "en" else explanation
            )
            category = extracted.document_type or "digital_communication"
    elif band == "suspicious":
        summary = (
            "Caution: Some details are suspicious. Verify independently before paying, clicking links or sharing personal information."
            if active_lang == "en" else explanation
        )
        category = "payment_receipt" if is_payment else (extracted.document_type or "digital_communication")
    else:  # likely_scam
        summary = (
            "Scam alert: The available evidence contains significant warning signs. Do not send money or share sensitive "
            "information until you verify independently."
            if active_lang == "en" else explanation
        )
        category = "payment_receipt" if is_payment else (extracted.document_type or "digital_communication")

    # Extract transaction and entity details for structured consumption
    tx_status = (
        "failed" if any(w in (extracted.message_text or "").lower() for w in ["failed", "declined", "unsuccessful"])
        else "pending" if any(w in (extracted.message_text or "").lower() for w in ["pending", "processing", "in progress"])
        else "successful" if any(w in (extracted.message_text or "").lower() for w in ["successful", "completed", "paid", "sent", "received"])
        else "unknown"
    )

    extracted_details = {
        "amount": extracted.amounts[0] if extracted.amounts else None,
        "amounts": extracted.amounts,
        "currency": "INR" if any("₹" in a or "rs" in a.lower() or "inr" in a.lower() for a in extracted.amounts) else None,
        "transaction_status": tx_status,
        "transaction_id": next((s.evidence for s in signals if "UTR" in s.id or "TXN" in s.id), None),
        "sender": extracted.sender,
        "recipient": None,
        "claimed_brand": extracted.claimed_brand,
        "upi_ids": extracted.upi_ids,
        "phone_numbers": extracted.phone_numbers,
        "urls": extracted.urls,
    }

    visible_claims = [c for c in [
        f"Status: {tx_status}" if tx_status != "unknown" else None,
        f"Amount: {extracted.amounts[0]}" if extracted.amounts else None,
        f"Claimed Brand: {extracted.claimed_brand}" if extracted.claimed_brand else None,
        f"Sender: {extracted.sender}" if extracted.sender else None,
    ] if c]

    red_flags = [f"{s.label}: {s.evidence}" for s in signals if s.weight > 0]
    positive_signals = [f"{s.label}: {s.evidence}" for s in signals if s.weight <= 0]
    verification_results = [tr.model_dump() for tr in tool_results]

    return AnalyzeResponse(
        request_id=str(uuid.uuid4()),
        status="success",
        category=category,
        verdict=band,
        risk_score=score,
        risk_level=risk_level,
        summary=summary,
        visible_claims=visible_claims,
        extracted_details=extracted_details,
        red_flags=red_flags,
        positive_signals=positive_signals,
        verification_results=verification_results,
        recommended_actions=next_steps,
        band=band,
        score=score,
        confidence=confidence,
        scam_type=scam_type,
        language=active_lang,
        extracted=extracted,
        signals=signals,
        tool_results=tool_results,
        explanation=explanation,
        next_steps=next_steps,
        family_alert=family_alert,
        limitations=LIMITATIONS_BY_LANG.get(active_lang, LIMITATIONS_BY_LANG["en"]),
        mode=active_mode if active_mode in ["cloud", "local", "mock"] else "mock",
        timings_ms=timings,
    )
