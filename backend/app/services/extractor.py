"""
Multimodal Extractor Service
----------------------------
Extracts verbatim text, structural layout features, and normalized entities
(URLs, phone numbers, UPI IDs, amounts, claimed brands) using vision-language models
and reinforces them via deterministic regex post-processing.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional
from pydantic import ValidationError
from app.schemas import ExtractedData
from app.services.model_client import ModelClient, get_model_client


PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "extract.txt")


def load_extraction_prompt() -> str:
    """Loads the base extraction prompt from disk."""
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()


def clean_code_fences(raw_text: str) -> str:
    """Strips markdown code fences and whitespace from model output."""
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def regex_extract_urls(text: str) -> List[str]:
    """Finds URLs and web links in text."""
    pattern = r'(?:https?://[^\s<>"\'\)]+|www\.[^\s<>"\'\)]+)'
    matches = re.findall(pattern, text)
    cleaned = []
    for m in matches:
        clean = m.rstrip(".,;:!?)'\"")
        if clean and clean not in cleaned:
            cleaned.append(clean)
    return cleaned


def regex_extract_phone_numbers(text: str) -> List[str]:
    """Finds Indian mobile numbers (+91), 10-digit numbers, and bank toll-free numbers."""
    phone_patterns = [
        r'(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}\b',  # Indian 10-digit mobile
        r'\b1800[\s-]?\d{3,4}[\s-]?\d{3,4}\b',        # Toll-free 1800
        r'\b\d{5}[\s-]?\d{5}\b',                      # 5-5 split
    ]
    results: List[str] = []
    for pat in phone_patterns:
        for match in re.findall(pat, text):
            norm = match.strip()
            if norm and norm not in results:
                results.append(norm)
    return results


def regex_extract_upi_ids(text: str) -> List[str]:
    """Finds UPI VPAs (e.g. user@okaxis, merchant@ybl) while avoiding standard webmail addresses."""
    # Exclude common email TLDs (.com, .org, .edu, .net, .in, .gov) from being treated as UPI bank handles
    email_tlds = {"com", "org", "net", "edu", "gov", "in", "io", "ai", "co"}
    pattern = r'\b([a-zA-Z0-9.\-_]{2,256}@([a-zA-Z0-9]{2,64}))\b'
    results: List[str] = []
    for full_vpa, handle in re.findall(pattern, text):
        if handle.lower() not in email_tlds and full_vpa not in results:
            results.append(full_vpa)
    return results


def regex_extract_amounts(text: str) -> List[str]:
    """Finds monetary amounts formatted with INR, Rs, or ₹ symbols."""
    pattern = r'(?:(?:INR|Rs\.?|₹)\s*[\d,]+(?:\.\d{1,2})?|\b[\d,]+(?:\.\d{1,2})?\s*(?:INR|rupees|Rs\.?|₹))\b'
    matches = re.findall(pattern, text, flags=re.IGNORECASE)
    results: List[str] = []
    for m in matches:
        clean = m.strip()
        if clean and clean not in results:
            results.append(clean)
    return results


def merge_and_deduplicate(model_list: List[str], regex_list: List[str]) -> List[str]:
    """Combines model extracted items with regex findings without duplicates."""
    seen = set()
    merged: List[str] = []
    for item in model_list + regex_list:
        clean = str(item).strip()
        if clean and clean.lower() not in seen:
            seen.add(clean.lower())
            merged.append(clean)
    return merged


async def extract_content(
    image_bytes: Optional[bytes] = None,
    raw_text: Optional[str] = None,
    image_quality: str = "sharp",
    mode: Optional[str] = None,
    model_client: Optional[ModelClient] = None,
) -> ExtractedData:
    """
    Orchestrates entity extraction from image and/or text input:
    1. Prepares prompt and calls model client.
    2. Parses JSON output with Pydantic validation.
    3. Retries once with a repair prompt on validation failure.
    4. Post-processes message_text with regular expressions to ensure no entities are dropped.
    """
    client = model_client or get_model_client(mode)
    base_prompt = load_extraction_prompt()

    # Build prompt input
    if raw_text and raw_text.strip():
        user_prompt = f"{base_prompt}\n\nINPUT MESSAGE TEXT TO EXTRACT:\n\"\"\"\n{raw_text.strip()}\n\"\"\""
    else:
        user_prompt = f"{base_prompt}\n\nPlease transcribe and extract structured fields from the attached image."

    images = [image_bytes] if image_bytes else None

    # Step 1: Model inference
    raw_output = await client.generate(
        prompt=user_prompt,
        images=images,
        json_mode=True,
        temperature=0.0,
    )

    # Step 2: Robust parsing & Pydantic validation
    cleaned_json_str = clean_code_fences(raw_output)
    parsed_dict: Optional[Dict[str, Any]] = None
    validation_error_str = ""

    try:
        parsed_dict = json.loads(cleaned_json_str)
        # Validate through schema
        extracted_model = ExtractedData(**parsed_dict)
    except (json.JSONDecodeError, ValidationError) as err:
        validation_error_str = str(err)
        parsed_dict = None

    # Step 3: Repair retry (1 attempt) if parsing failed
    if parsed_dict is None:
        repair_prompt = (
            f"The previous output failed JSON validation with error:\n{validation_error_str}\n\n"
            f"Faulty output received:\n{cleaned_json_str}\n\n"
            "Please fix the syntax and return ONLY the valid JSON object adhering strictly to the required schema."
        )
        try:
            repair_output = await client.generate(
                prompt=repair_prompt,
                images=None,
                json_mode=True,
                temperature=0.0,
            )
            repaired_str = clean_code_fences(repair_output)
            parsed_dict = json.loads(repaired_str)
            extracted_model = ExtractedData(**parsed_dict)
        except Exception:
            # If repair still fails, construct a safe fallback object from raw text or mark insufficient_info
            fallback_text = raw_text or ""
            return ExtractedData(
                document_type="other",
                sender=None,
                message_text=fallback_text,
                urls=regex_extract_urls(fallback_text),
                phone_numbers=regex_extract_phone_numbers(fallback_text),
                upi_ids=regex_extract_upi_ids(fallback_text),
                amounts=regex_extract_amounts(fallback_text),
                claimed_brand=None,
                detected_language="en",
                image_quality="low" if image_bytes else "text_only",
                visual_notes=["Model extraction parsing failed, entity regex fallback applied"],
            )

    # Step 4: Deterministic Regex Post-Processing
    # When raw_text is directly provided, preserve it as the authentic verbatim message_text
    if raw_text and raw_text.strip():
        msg_text = raw_text.strip()
    else:
        msg_text = extracted_model.message_text or ""

    reg_urls = regex_extract_urls(msg_text)
    reg_phones = regex_extract_phone_numbers(msg_text)
    reg_upis = regex_extract_upi_ids(msg_text)
    reg_amounts = regex_extract_amounts(msg_text)

    final_urls = merge_and_deduplicate(extracted_model.urls, reg_urls)
    final_phones = merge_and_deduplicate(extracted_model.phone_numbers, reg_phones)
    final_upis = merge_and_deduplicate(extracted_model.upi_ids, reg_upis)
    final_amounts = merge_and_deduplicate(extracted_model.amounts, reg_amounts)

    # Respect image quality calculated during validation
    final_quality = image_quality if image_bytes else "text_only"

    return ExtractedData(
        document_type=extracted_model.document_type or "other",
        sender=extracted_model.sender,
        message_text=msg_text,
        urls=final_urls,
        phone_numbers=final_phones,
        upi_ids=final_upis,
        amounts=final_amounts,
        claimed_brand=extracted_model.claimed_brand,
        detected_language=extracted_model.detected_language or "en",
        image_quality=final_quality,
        visual_notes=extracted_model.visual_notes or [],
    )
