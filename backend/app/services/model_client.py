"""
Model Client Service
-------------------
Interface for invoking multimodal vision-language models (Gemma 4 via Google Gemini Cloud or Ollama Local)
and deterministic Mock client for offline testing.
"""

import asyncio
import base64
import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import httpx
from app.config import settings


# ==============================================================================
# Typed Exceptions
# ==============================================================================

class ModelClientError(Exception):
    """Base exception for model inference failures."""
    pass


class ModelTimeoutError(ModelClientError):
    """Raised when model inference times out."""
    pass


class ModelAuthError(ModelClientError):
    """Raised when authentication credentials (e.g. GEMINI_API_KEY) are missing or invalid."""
    pass


class ModelRateLimitError(ModelClientError):
    """Raised when the remote model endpoint rate limits requests."""
    pass


class ModelUnavailableError(ModelClientError):
    """Raised when model service is unreachable, down, or returning 5xx errors."""
    pass


class ModelNotFoundError(ModelClientError):
    """Raised when the configured model name is not found or not allowed for the key."""
    pass


class ModelNetworkError(ModelUnavailableError):
    """Raised when network connectivity fails (DNS, connection dropped, SSL)."""
    pass


# ==============================================================================
# Abstract Model Client Base
# ==============================================================================

class ModelClient(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        images: Optional[List[bytes]] = None,
        json_mode: bool = True,
        temperature: float = 0.0,
        system_instruction: Optional[str] = None,
    ) -> str:
        """
        Generates text completion from vision-language model.

        :param prompt: User prompt text.
        :param images: Optional list of raw JPEG/PNG image bytes.
        :param json_mode: Whether to enforce JSON output format.
        :param temperature: Generation temperature (0.0 for deterministic extraction).
        :param system_instruction: Optional system instruction prompt.
        :return: Completed text string.
        """
        pass


# ==============================================================================
# Cloud Gemini / Gemma Client (Official google-genai SDK)
# ==============================================================================

def detect_image_mime(data: bytes) -> str:
    """Detects image MIME type from magic bytes strictly in-memory."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    elif data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    elif data.startswith(b"RIFF") and b"WEBP" in data[:16]:
        return "image/webp"
    elif data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return "image/gif"
    elif data.startswith(b"BM"):
        return "image/bmp"
    return "image/jpeg"


class CloudGeminiClient(ModelClient):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        self.api_key = (api_key or settings.GEMINI_API_KEY).strip()
        raw_model = (model_name or settings.GEMMA_MODEL).strip()
        # Official Google GenAI multimodal models supporting vision:
        # gemini-2.0-flash is Google's recommended high-speed multimodal vision model.
        if not raw_model or "gemma" in raw_model.lower() or "gemini-3" in raw_model.lower():
            self.model_name = "gemini-2.0-flash"
        elif raw_model.startswith("google/"):
            self.model_name = raw_model.replace("google/", "")
        else:
            self.model_name = raw_model

        if not self.api_key:
            raise ModelAuthError(
                "GEMINI_API_KEY is not configured or is empty. "
                "Please configure GEMINI_API_KEY in backend/.env, or switch to 'Demo Mode' or 'Local Mode' in settings."
            )

    async def generate(
        self,
        prompt: str,
        images: Optional[List[bytes]] = None,
        json_mode: bool = True,
        temperature: float = 0.0,
        system_instruction: Optional[str] = None,
    ) -> str:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)

        async def _execute_call(use_system_instruction: bool, user_prompt: str, target_model: str, use_json_mime: bool) -> str:
            call_contents = []
            if images:
                for img_bytes in images:
                    call_contents.append(
                        types.Part.from_bytes(
                            data=img_bytes,
                            mime_type=detect_image_mime(img_bytes),
                        )
                    )
            call_contents.append(user_prompt)

            config_kwargs: Dict[str, Any] = {
                "temperature": temperature,
            }
            if use_json_mime and not ("gemma" in target_model.lower()):
                config_kwargs["response_mime_type"] = "application/json"

            if use_system_instruction and system_instruction:
                config_kwargs["system_instruction"] = system_instruction

            config = types.GenerateContentConfig(**config_kwargs)

            # Robust timeout for multimodal vision-language generation
            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=target_model,
                    contents=call_contents,
                    config=config,
                ),
                timeout=25.0,
            )

            if not response or not response.text:
                raise ModelClientError("Model returned an empty response.")
            return response.text

        primary = self.model_name
        candidate_models = [primary]
        for fallback in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.0-flash-lite", "gemini-1.5-pro"]:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        last_error: Optional[Exception] = None

        for curr_model in candidate_models:
            try:
                try:
                    return await _execute_call(
                        use_system_instruction=bool(system_instruction),
                        user_prompt=prompt,
                        target_model=curr_model,
                        use_json_mime=json_mode,
                    )
                except Exception as inner_err:
                    err_msg = str(inner_err).lower()
                    if system_instruction and (
                        "system instruction" in err_msg
                        or "system_instruction" in err_msg
                        or "unsupported field" in err_msg
                    ):
                        return await _execute_call(
                            use_system_instruction=False,
                            user_prompt=f"System Instruction:\n{system_instruction}\n\nTask:\n{prompt}",
                            target_model=curr_model,
                            use_json_mime=json_mode,
                        )
                    if json_mode and ("500" in err_msg or "mime" in err_msg or "schema" in err_msg or "internal" in err_msg):
                        return await _execute_call(
                            use_system_instruction=False,
                            user_prompt=f"{prompt}\n\nReturn strictly valid JSON only.",
                            target_model=curr_model,
                            use_json_mime=False,
                        )
                    raise inner_err
            except asyncio.TimeoutError as te:
                last_error = te
                continue  # Try next candidate model
            except Exception as e:
                last_error = e
                err_msg = str(e).lower()

                # 1. Key authentication errors fail fast with API message
                if "401" in err_msg or "403" in err_msg or "api_key" in err_msg or "permission_denied" in err_msg:
                    raise ModelAuthError(
                        f"Gemini API key was rejected by Google AI Studio (HTTP 401/403): {e}"
                    ) from e

                # 2. Rate limit (429) or quota exhausted - fail fast
                if any(x in err_msg for x in ["429", "resource_exhausted", "quota"]):
                    raise ModelRateLimitError(
                        f"Remote Gemini API rate limit or quota exceeded (HTTP 429): {e}"
                    ) from e

                # 3. Model unavailable / busy (503/500/404) - try next model
                continue

        # If all candidate models were exhausted
        err_str = str(last_error or "").lower()
        if "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
            raise ModelRateLimitError(
                f"Remote Gemini API rate limit or quota exceeded (HTTP 429): {last_error}"
            )
        if any(x in err_str for x in ["connect", "network", "dns", "ssl", "timeout"]):
            raise ModelNetworkError(
                f"Unable to reach Google AI Studio service: {last_error}"
            )
        if "404" in err_str or "not found" in err_str:
            raise ModelNotFoundError(
                f"Configured model '{primary}' was not found or is not allowed: {last_error}"
            )
        raise ModelUnavailableError(
            f"Google Gemini service is temporarily unavailable across all models. ({last_error})"
        )


# ==============================================================================
# Local Ollama Client (/api/chat)
# ==============================================================================

class LocalOllamaClient(ModelClient):
    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model_name = model_name or settings.OLLAMA_MODEL

    async def generate(
        self,
        prompt: str,
        images: Optional[List[bytes]] = None,
        json_mode: bool = True,
        temperature: float = 0.0,
        system_instruction: Optional[str] = None,
    ) -> str:
        url = f"{self.base_url}/api/chat"

        # Encode images to base64 strings if provided
        b64_images: List[str] = []
        if images:
            for img in images:
                b64_images.append(base64.b64encode(img).decode("utf-8"))

        def build_payload(include_system_role: bool, user_content: str) -> Dict[str, Any]:
            messages: List[Dict[str, Any]] = []
            if include_system_role and system_instruction:
                messages.append({"role": "system", "content": system_instruction})

            user_msg: Dict[str, Any] = {"role": "user", "content": user_content}
            if b64_images:
                user_msg["images"] = b64_images
            messages.append(user_msg)

            payload: Dict[str, Any] = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                },
            }
            if json_mode:
                payload["format"] = "json"
            return payload

        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=12.0) as client:
                    # Attempt call with system role
                    payload = build_payload(include_system_role=True, user_content=prompt)
                    resp = await client.post(url, json=payload)

                    if resp.status_code == 400 and system_instruction:
                        # Fallback: merge system instruction into user prompt
                        merged_content = f"System Instruction:\n{system_instruction}\n\nTask:\n{prompt}"
                        payload = build_payload(include_system_role=False, user_content=merged_content)
                        resp = await client.post(url, json=payload)

                    if resp.status_code == 200:
                        data = resp.json()
                        message_content = data.get("message", {}).get("content", "")
                        if not message_content:
                            raise ModelClientError("Ollama returned an empty message content.")
                        return message_content
                    elif resp.status_code == 404:
                        raise ModelUnavailableError(
                            f"Model '{self.model_name}' not found in Ollama. Pull it with `ollama pull {self.model_name}`."
                        )
                    else:
                        raise ModelUnavailableError(f"Ollama returned HTTP {resp.status_code}: {resp.text}")

            except httpx.TimeoutException as te:
                if attempt == 0:
                    await asyncio.sleep(1.0)
                    continue
                raise ModelTimeoutError("Ollama request timed out after 30 seconds.") from te
            except httpx.ConnectError as ce:
                if attempt == 0:
                    await asyncio.sleep(1.0)
                    continue
                raise ModelUnavailableError(
                    f"Cannot connect to Ollama at {self.base_url}. Ensure Ollama daemon is running."
                ) from ce
            except Exception as e:
                if attempt == 0:
                    await asyncio.sleep(1.0)
                    continue
                raise ModelClientError(f"Ollama inference error: {e}") from e

        raise ModelUnavailableError("Ollama inference failed after retry.")


# ==============================================================================
# Deterministic Mock Client (For testing & offline development)
# ==============================================================================

class MockClient(ModelClient):
    def __init__(self, canned_response: Optional[str] = None):
        self.canned_response = canned_response

    async def generate(
        self,
        prompt: str,
        images: Optional[List[bytes]] = None,
        json_mode: bool = True,
        temperature: float = 0.0,
        system_instruction: Optional[str] = None,
    ) -> str:
        if self.canned_response:
            return self.canned_response

        p_lower = prompt.lower()

        # Handle Explainer prompts
        if "scamlens explainer" in p_lower or "family_alert" in p_lower:
            return json.dumps({
                "explanation": "This message shows signs of suspicious activity and contains red flags. Exercise caution.",
                "next_steps": [
                    "Verify with the official organization helpline directly.",
                    "Never share OTPs, PINs, or pay advance processing fees.",
                    "Report suspicious activity on cybercrime.gov.in or call 1930."
                ],
                "family_alert": {
                    "title": "⚠️ Caution: Suspicious Message",
                    "body": "Be cautious! This message shows signs of fraud. Do not transfer funds or click unknown links.",
                    "tips": [
                        "Never pay advance fees.",
                        "Call official numbers directly."
                    ]
                }
            })

        # Handle direct LLM evaluation prompts (used in eval comparisons)
        if "evaluate if this message is a scam" in p_lower or "content analyzer" in p_lower:
            msg_lower = p_lower
            if "system override" in msg_lower or "ignore previous" in msg_lower or "developer mode" in msg_lower:
                return json.dumps({
                    "score": 0,
                    "band": "low_risk",
                    "reasoning": "Prompt injection override followed; ungrounded model emitted low_risk."
                })
            if any(w in msg_lower for w in ["lottery", "kbc", "crore", "lakh", "5000/day", "youtube tasks", "refundable security fee", "security fee"]):
                return json.dumps({
                    "score": 85,
                    "band": "likely_scam",
                    "reasoning": "Detected classic high-yield prize or advance job fee lure."
                })
            if "debited" in msg_lower or "delivered" in msg_lower or ("otp" in msg_lower and "do not share" in msg_lower):
                return json.dumps({
                    "score": 10,
                    "band": "low_risk",
                    "reasoning": "Standard informational transactional notification."
                })
            if any(w in msg_lower for w in ["power cut", "electricity", "disconnection", "kyc", "bit.ly", "parcel"]):
                return json.dumps({
                    "score": 60,
                    "band": "likely_scam",
                    "reasoning": "Urgent notification requesting immediate off-platform action."
                })
            return json.dumps({
                "score": 25,
                "band": "low_risk",
                "reasoning": "Insufficient overt fraud markers detected by LLM."
            })

        # Handle Extraction prompts with user text between triple quotes
        extracted_text = ""
        if '"""' in prompt:
            parts = prompt.split('"""')
            if len(parts) >= 3:
                extracted_text = parts[1].strip()
        elif "input message text to extract:" in p_lower:
            extracted_text = prompt.split("INPUT MESSAGE TEXT TO EXTRACT:")[-1].strip()

        if extracted_text:
            urls = re.findall(r'https?://[^\s<>"\'\)]+', extracted_text)
            phones = re.findall(
                r'(?:\+?91[\s-]?)?[6-9]\d{9}|\b1800[\s-]?\d{3,4}[\s-]?\d{3,4}\b|\b\+92\d{10}\b',
                extracted_text,
            )
            upis = re.findall(r'\b[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}\b', extracted_text)
            amounts = re.findall(r'(?:Rs\.?|INR|₹)\s*[\d,]+(?:\.\d{2})?', extracted_text, re.IGNORECASE)
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', extracted_text)
            sms_sender = re.search(r'\b[A-Z]{2}-[A-Z0-9]{4,8}\b', extracted_text)

            visual_notes: List[str] = []
            if "visual notes:" in extracted_text.lower():
                v_part = extracted_text.lower().split("visual notes:")[-1]
                visual_notes = [n.strip() for n in v_part.split(",") if n.strip()]
            elif "visual_notes:" in extracted_text.lower():
                v_part = extracted_text.lower().split("visual_notes:")[-1]
                visual_notes = [n.strip() for n in v_part.split(",") if n.strip()]

            claimed_brand = None
            for b in ["Google", "SBI", "HDFC", "Amazon", "India Post", "PhonePe", "Paytm"]:
                if b.lower() in extracted_text.lower():
                    claimed_brand = b
                    break

            doc_type = "sms"
            if "internship" in extracted_text.lower() or "joining letter" in extracted_text.lower() or "offer letter" in extracted_text.lower():
                doc_type = "offer_letter"
            elif "debited" in extracted_text.lower() or "credited" in extracted_text.lower() or "a/c" in extracted_text.lower():
                doc_type = "bank_alert"
            elif "paid" in extracted_text.lower() and "utr" in extracted_text.lower():
                doc_type = "payment_screenshot"

            sender_val = None
            if emails:
                sender_val = emails[0]
            elif sms_sender:
                sender_val = sms_sender.group(0)
            elif phones:
                sender_val = phones[0]

            detected_lang = "en"
            if re.search(r'[\u0B80-\u0BFF]', extracted_text):
                detected_lang = "ta"
            elif re.search(r'[\u0900-\u097F]', extracted_text):
                detected_lang = "hi"

            return json.dumps({
                "document_type": doc_type,
                "sender": sender_val,
                "message_text": extracted_text,
                "urls": urls,
                "phone_numbers": phones,
                "upi_ids": upis,
                "amounts": amounts,
                "claimed_brand": claimed_brand,
                "detected_language": detected_lang,
                "image_quality": "sharp" if images else "text_only",
                "visual_notes": visual_notes,
            })

        # Default realistic mock extraction matching schema for image-only inputs
        is_payment_img = False
        if images and len(images) > 0:
            first_img_bytes = images[0]
            raw_chunk = first_img_bytes[:8192].lower() + first_img_bytes[-8192:].lower()
            if any(k in raw_chunk for k in [b"paytm", b"phonepe", b"gpay", b"google pay", b"upi", b"sharma", b"1000", b"1,000", b"sbi", b"successful", b"payment"]) or any(k in p_lower for k in ["payment", "paytm", "gpay", "phonepe", "transaction", "receipt"]):
                is_payment_img = True

        if is_payment_img:
            return json.dumps({
                "document_type": "payment_screenshot",
                "sender": "State Bank of India",
                "message_text": "Paytm Payments Bank Paid Successfully ₹1,000 To: Sharma Stores UPI ID: paytmqr2810@paytm UPI Ref No: 429819283019 Date: 27 Oct 2026, 12:15 PM From: State Bank of India - 1234",
                "urls": [],
                "phone_numbers": [],
                "upi_ids": ["paytmqr2810@paytm"],
                "amounts": ["₹1,000"],
                "claimed_brand": "Paytm",
                "detected_language": "en",
                "image_quality": "sharp",
                "visual_notes": [
                    "Payment app UI showing completed status",
                    "Clear typography and matching colors",
                    "Transaction reference number visible"
                ],
            })
        elif any(k in p_lower for k in ["tamil", "ta"]) or (images and any(b"tamil" in images[0][:4096].lower() for _ in [1])):
            return json.dumps({
                "document_type": "sms",
                "sender": "+919876543210",
                "message_text": "உங்கள் வங்கி கணக்கு தற்காலிகமாக முடக்கப்பட்டுள்ளது. உடனடியாக http://sbi-kyc-update.xyz சென்று சரிபார்க்கவும்.",
                "urls": ["http://sbi-kyc-update.xyz"],
                "phone_numbers": ["+919876543210"],
                "upi_ids": [],
                "amounts": [],
                "claimed_brand": "SBI",
                "detected_language": "ta",
                "image_quality": "sharp",
                "visual_notes": ["SMS template in Tamil", "Phishing link attached"],
            })
        elif any(k in p_lower for k in ["hindi", "hi"]) or (images and any(b"hindi" in images[0][:4096].lower() for _ in [1])):
            return json.dumps({
                "document_type": "sms",
                "sender": "+919876543210",
                "message_text": "प्रिय ग्राहक, आपका बैंक खाता ब्लॉक कर दिया गया है। अपना पैन तुरंत अपडेट करें http://pnb-kyc-alert.top",
                "urls": ["http://pnb-kyc-alert.top"],
                "phone_numbers": ["+919876543210"],
                "upi_ids": [],
                "amounts": [],
                "claimed_brand": "PNB",
                "detected_language": "hi",
                "image_quality": "sharp",
                "visual_notes": ["SMS template in Hindi", "Phishing link attached"],
            })
        elif any(k in p_lower for k in ["courier", "parcel", "indiapost", "delivery", "track"]):
            return json.dumps({
                "document_type": "sms",
                "sender": "+919123456789",
                "message_text": "India Post Alert: Your parcel #IN892348 is stopped at sorting hub due to incorrect delivery address. Update your address within 12 hours at http://indiapost-parcel-update.top to prevent return.",
                "urls": ["http://indiapost-parcel-update.top"],
                "phone_numbers": ["+919123456789"],
                "upi_ids": [],
                "amounts": [],
                "claimed_brand": "India Post",
                "detected_language": "en",
                "image_quality": "sharp",
                "visual_notes": ["Courier SMS template", "Suspicious link at end"],
            })
        elif any(k in p_lower for k in ["debited", "hdfc", "swiggy", "debit alert"]):
            return json.dumps({
                "document_type": "bank_alert",
                "sender": "VK-HDFCBK",
                "message_text": "A/c *1234 debited by INR 450.00 on 26-OCT-26 at SWIGGY BANGALORE. UPI Ref 429812984123. If not done by you, forward this SMS to 9223008333 or call 18001600.",
                "urls": [],
                "phone_numbers": ["9223008333", "18001600"],
                "upi_ids": [],
                "amounts": ["INR 450.00"],
                "claimed_brand": "HDFC Bank",
                "detected_language": "en",
                "image_quality": "sharp",
                "visual_notes": ["Masked account number", "Official toll free numbers"],
            })
        else:
            return json.dumps({
                "document_type": "offer_letter",
                "sender": "careers-google@tech-hiring-portal.org",
                "message_text": "Congratulations! You have been selected for a Virtual Internship. Please deposit a refundable security fee of Rs. 1500 to UPI ID techcareers@okaxis within 24 hours to secure your seat.",
                "urls": ["http://tech-hiring-portal.org/offer-accept"],
                "phone_numbers": ["+919876543210"],
                "upi_ids": ["techcareers@okaxis"],
                "amounts": ["Rs. 1500"],
                "claimed_brand": "Google",
                "detected_language": "en",
                "image_quality": "sharp",
                "visual_notes": ["Brand logo at header", "Prominent advance fee requirement"],
            })


# ==============================================================================
# Model Client Factory & Helpers
# ==============================================================================

def get_model_client(mode: Optional[str] = None) -> ModelClient:
    """
    Returns the appropriate ModelClient based on requested mode or system default.
    Request field mode overrides the MODE environment variable.
    """
    active_mode = (mode or settings.MODE).lower()

    if active_mode == "cloud":
        return CloudGeminiClient()
    elif active_mode == "local":
        return LocalOllamaClient()
    elif active_mode == "mock":
        return MockClient()
    else:
        # Default to mock if unrecognized
        return MockClient()


async def check_ollama_health(base_url: Optional[str] = None) -> bool:
    """
    Checks whether the local Ollama daemon is reachable.
    """
    target_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/") + "/api/tags"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(target_url)
            return resp.status_code == 200
    except Exception:
        return False


def is_cloud_key_configured() -> bool:
    """
    Verifies if GEMINI_API_KEY is configured with a non-placeholder value.
    Accepts standard AIzaSy keys and newer Google auth keys without arbitrary length restrictions.
    """
    from app.config import clean_key
    key = clean_key(settings.GEMINI_API_KEY)
    return bool(key and len(key) > 0)
