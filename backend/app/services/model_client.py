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

class CloudGeminiClient(ModelClient):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMMA_MODEL
        if not self.api_key or not self.api_key.strip():
            raise ModelAuthError("GEMINI_API_KEY is not configured or is empty.")

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

        # Build contents list
        contents: List[Any] = []
        if images:
            for img_bytes in images:
                contents.append(
                    types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
                )
        contents.append(prompt)

        async def _execute_call(use_system_instruction: bool, user_prompt: str) -> str:
            call_contents = []
            if images:
                for img_bytes in images:
                    call_contents.append(
                        types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
                    )
            call_contents.append(user_prompt)

            config_kwargs: Dict[str, Any] = {
                "temperature": temperature,
            }
            if json_mode:
                config_kwargs["response_mime_type"] = "application/json"

            if use_system_instruction and system_instruction:
                config_kwargs["system_instruction"] = system_instruction

            config = types.GenerateContentConfig(**config_kwargs)

            # Enforce 30s timeout per attempt
            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=self.model_name,
                    contents=call_contents,
                    config=config,
                ),
                timeout=30.0,
            )

            if not response or not response.text:
                raise ModelClientError("Model returned an empty response.")
            return response.text

        # First attempt (with 1 retry on transient error)
        for attempt in range(2):
            try:
                try:
                    return await _execute_call(
                        use_system_instruction=bool(system_instruction),
                        user_prompt=prompt,
                    )
                except Exception as inner_err:
                    err_msg = str(inner_err).lower()
                    # If model deployment rejects system_instruction, automatically merge into user prompt
                    if system_instruction and (
                        "system instruction" in err_msg
                        or "system_instruction" in err_msg
                        or "unsupported field" in err_msg
                    ):
                        merged = f"System Instruction:\n{system_instruction}\n\nTask:\n{prompt}"
                        return await _execute_call(
                            use_system_instruction=False,
                            user_prompt=merged,
                        )
                    raise inner_err
            except asyncio.TimeoutError as te:
                if attempt == 0:
                    await asyncio.sleep(1.5)
                    continue
                raise ModelTimeoutError("Cloud Gemini request timed out after 30 seconds.") from te
            except Exception as e:
                err_msg = str(e).lower()
                if "429" in err_msg or "resource_exhausted" in err_msg:
                    raise ModelRateLimitError(f"Cloud Gemini rate limit exceeded: {e}") from e
                if "401" in err_msg or "403" in err_msg or "api_key" in err_msg:
                    raise ModelAuthError(f"Cloud Gemini authentication error: {e}") from e
                if attempt == 0 and ("503" in err_msg or "500" in err_msg or "connection" in err_msg):
                    await asyncio.sleep(1.5)
                    continue
                raise ModelUnavailableError(f"Cloud Gemini inference failed: {e}") from e

        raise ModelUnavailableError("Cloud Gemini inference failed after retry.")


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
                async with httpx.AsyncClient(timeout=30.0) as client:
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

        # Handle Extraction prompts with user text between triple quotes
        extracted_text = ""
        if '"""' in prompt:
            parts = prompt.split('"""')
            if len(parts) >= 3:
                extracted_text = parts[1].strip()

        if extracted_text:
            urls = re.findall(r'https?://[^\s<>"\'\)]+', extracted_text)
            phones = re.findall(
                r'(?:\+?91[\s-]?)?[6-9]\d{9}|\b1800[\s-]?\d{3,4}[\s-]?\d{3,4}\b|\b\+92\d{10}\b',
                extracted_text,
            )
            upis = re.findall(r'\b[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}\b', extracted_text)
            amounts = re.findall(r'(?:Rs\.?|INR|₹)\s*[\d,]+(?:\.\d{2})?', extracted_text, re.IGNORECASE)

            visual_notes: List[str] = []
            if "visual notes:" in extracted_text.lower():
                v_part = extracted_text.lower().split("visual notes:")[-1]
                visual_notes = [n.strip() for n in v_part.split(",") if n.strip()]

            claimed_brand = None
            for b in ["Google", "SBI", "HDFC", "Amazon", "India Post", "PhonePe", "Paytm"]:
                if b.lower() in extracted_text.lower():
                    claimed_brand = b
                    break

            doc_type = "sms"
            if "internship" in extracted_text.lower() or "joining letter" in extracted_text.lower():
                doc_type = "offer_letter"
            elif "debited" in extracted_text.lower() or "credited" in extracted_text.lower():
                doc_type = "bank_alert"
            elif "paid" in extracted_text.lower() and "utr" in extracted_text.lower():
                doc_type = "payment_screenshot"

            return json.dumps({
                "document_type": doc_type,
                "sender": phones[0] if phones else None,
                "message_text": extracted_text,
                "urls": urls,
                "phone_numbers": phones,
                "upi_ids": upis,
                "amounts": amounts,
                "claimed_brand": claimed_brand,
                "detected_language": "en",
                "image_quality": "sharp",
                "visual_notes": visual_notes,
            })

        # Default realistic mock extraction matching schema
        if "input message text to extract" in p_lower:
            user_part = p_lower.split("input message text to extract")[-1]
        else:
            user_part = p_lower

        if any(k in user_part for k in ["courier", "parcel", "indiapost", "delivery", "track"]):
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
        elif any(k in user_part for k in ["debited", "hdfc", "swiggy", "debit alert"]):
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
    """
    key = settings.GEMINI_API_KEY.strip()
    return bool(key and key != "your_gemini_api_key_here" and len(key) > 8)
