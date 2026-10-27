"""
Automated Test Suite for Section 14 Requirements
------------------------------------------------
Tests all 18 specific scenarios mandated in Section 14:
 1. A genuine-looking successful payment screenshot with no visible suspicious indicators.
 2. A legitimate payment screenshot with a readable transaction reference.
 3. A fake-looking payment receipt containing conflicting amounts.
 4. A screenshot claiming a payment succeeded, but with no independent transaction verification.
 5. An internship offer demanding an upfront registration fee.
 6. A suspicious bank message asking for an OTP.
 7. A legitimate routine bank notification.
 8. A suspicious URL confirmed by a threat-intelligence service.
 9. A URL that cannot be verified because the service is unavailable.
10. An unreadable or corrupted image.
11. A screenshot with no visible URL.
12. An image containing Tamil text.
13. An image containing Hindi text.
14. An invalid or malformed AI response.
15. A missing or invalid API key.
16. A timeout or rate-limit error.
17. A request made while local mode is unavailable.
18. A request made while cloud mode is unavailable.
"""

import io
import os
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from app.api.limiter import limiter
from app.config import settings
from app.main import app
from app.schemas import AnalyzeResponse, ExtractedData, ToolResult, Signal
from app.services.model_client import (
    ModelAuthError,
    ModelClient,
    ModelRateLimitError,
    ModelTimeoutError,
    ModelUnavailableError,
)
from app.services.pipeline import run_pipeline

client = TestClient(app)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def generate_png(text: str, width: int = 720, height: int = 1560) -> bytes:
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((25, 25), text, fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture(autouse=True)
def reset_limiter_state():
    limiter.reset()
    yield
    limiter.reset()


# ==============================================================================
# 1. Genuine-looking successful payment screenshot with no suspicious indicators
# ==============================================================================
def test_case_1_genuine_payment_screenshot():
    # Use real asset if present, or generate PNG
    img_path = os.path.join(REPO_ROOT, "test_assets", "paytm_1000.png")
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            img_bytes = f.read()
    else:
        img_bytes = generate_png("Paid ₹1,000 to Merchant. Successful. UPI Ref 429812984123")

    response = client.post(
        "/api/analyze",
        files={"image": ("paytm_1000.png", img_bytes, "image/png")},
        data={"mode": "mock", "language": "en"},
    )
    assert response.status_code == 200
    res = response.json()

    # Must be low risk (0-24)
    assert res["band"] == "low_risk"
    assert res["risk_score"] <= 24
    assert res["risk_level"] == "low"
    assert res["category"] == "payment_receipt"

    # Must include Outcome 1 unverified payment disclaimer
    assert "not been independently verified" in res["summary"]
    # Must NOT automatically flag genuine payment as scam
    assert res["band"] != "likely_scam"


# ==============================================================================
# 2. Legitimate payment screenshot with a readable transaction reference
# ==============================================================================
def test_case_2_payment_with_readable_transaction_reference():
    receipt_text = "Payment to Swiggy INR 450.00 Successful. UPI Ref: 429812984123. Txn ID: PT429812984"
    img_bytes = generate_png(receipt_text)

    response = client.post(
        "/api/analyze",
        files={"image": ("receipt.png", img_bytes, "image/png")},
        data={"text": receipt_text, "mode": "mock", "language": "en"},
    )
    assert response.status_code == 200
    res = response.json()

    assert res["band"] == "low_risk"
    assert res["extracted_details"]["transaction_status"] == "successful"
    assert len(res["extracted"]["amounts"]) > 0
    # No upfront fee or phishing flags
    assert not any("upfront" in rf.lower() for rf in res["red_flags"])


# ==============================================================================
# 3. Fake-looking payment receipt containing conflicting amounts
# ==============================================================================
def test_case_3_fake_payment_conflicting_amounts():
    # Conflicting amounts in text: claims Paid 1000, but Due is 5000 and total 200
    conflicting_text = (
        "Transaction Receipt: Paid ₹1000 to Shop. "
        "Original bill amount: ₹5000. Subtotal: ₹200. "
        "Warning: Total billed amount conflicts with payment confirmation amount."
    )
    img_bytes = generate_png(conflicting_text)

    response = client.post(
        "/api/analyze",
        files={"image": ("conflicting.png", img_bytes, "image/png")},
        data={"text": conflicting_text, "mode": "mock", "language": "en"},
    )
    assert response.status_code == 200
    res = response.json()
    assert len(res["extracted"]["amounts"]) >= 2


# ==============================================================================
# 4. Screenshot claiming payment succeeded, but with no independent verification
# ==============================================================================
def test_case_4_payment_succeeded_unverified():
    payment_claim = "Payment Successful ₹1,000 to merchant@upi. Time: 12:30 PM."
    img_bytes = generate_png(payment_claim)

    response = client.post(
        "/api/analyze",
        files={"image": ("success.png", img_bytes, "image/png")},
        data={"text": payment_claim, "mode": "mock", "language": "en"},
    )
    assert response.status_code == 200
    res = response.json()

    # Confirms payment succeeded per screenshot, but states unverified
    assert res["extracted_details"]["transaction_status"] == "successful"
    assert "not been independently verified" in res["summary"]
    assert "limitations" in res


# ==============================================================================
# 5. Internship offer demanding an upfront registration fee
# ==============================================================================
def test_case_5_internship_offer_upfront_fee():
    internship_text = (
        "Offer Letter: Congratulations! You are selected for Virtual Web Development Internship. "
        "You must pay a refundable registration fee of Rs 1500 to hr@okaxis within 24 hours to secure your seat."
    )
    img_bytes = generate_png(internship_text)

    response = client.post(
        "/api/analyze",
        files={"image": ("internship.png", img_bytes, "image/png")},
        data={"text": internship_text, "mode": "mock", "language": "en"},
    )
    assert response.status_code == 200
    res = response.json()

    assert res["band"] in ("suspicious", "likely_scam")
    assert res["risk_score"] >= 30
    assert any("fee" in rf.lower() or "job" in rf.lower() or "internship" in rf.lower() for rf in res["red_flags"])


# ==============================================================================
# 6. Suspicious bank message asking for an OTP
# ==============================================================================
def test_case_6_suspicious_bank_otp():
    bank_otp_text = (
        "Dear Customer, your State Bank account will be blocked immediately due to incomplete KYC. "
        "Please share the OTP 849201 sent to your mobile or login at http://sbi-verify-kyc.top to update PAN."
    )
    img_bytes = generate_png(bank_otp_text)

    response = client.post(
        "/api/analyze",
        files={"image": ("bank_otp.png", img_bytes, "image/png")},
        data={"text": bank_otp_text, "mode": "mock", "language": "en"},
    )
    assert response.status_code == 200
    res = response.json()

    assert res["band"] in ("suspicious", "likely_scam")
    assert res["risk_score"] >= 30
    assert any("otp" in rf.lower() or "credential" in rf.lower() or "kyc" in rf.lower() for rf in res["red_flags"])


# ==============================================================================
# 7. Legitimate routine bank notification
# ==============================================================================
def test_case_7_legitimate_bank_notification():
    genuine_notification = (
        "A/c *1234 debited by INR 450.00 on 26-OCT-26 at SWIGGY. "
        "UPI Ref 429812984123. If not done by you call 18001600."
    )
    img_bytes = generate_png(genuine_notification)

    response = client.post(
        "/api/analyze",
        files={"image": ("bank_debit.png", img_bytes, "image/png")},
        data={"text": genuine_notification, "mode": "mock", "language": "en"},
    )
    assert response.status_code == 200
    res = response.json()

    assert res["band"] == "low_risk"
    assert res["risk_score"] <= 24
    assert len(res["red_flags"]) == 0


# ==============================================================================
# 8. Suspicious URL confirmed by a threat-intelligence service
# ==============================================================================
def test_case_8_suspicious_url_confirmed_threat_intel():
    malicious_text = "Click http://sbi-kyc-update.com/login to update your KYC and prevent suspension."

    response = client.post(
        "/api/analyze",
        data={"text": malicious_text, "mode": "mock", "language": "en"},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["score"] >= 25
    assert len(res["signals"]) > 0


# ==============================================================================
# 9. URL that cannot be verified because the service is unavailable
# ==============================================================================
@pytest.mark.asyncio
async def test_case_9_url_verifier_service_unavailable():
    # If RDAP or threat feed fails or times out, the pipeline MUST NOT crash
    from app.services.verifiers import run_verifiers
    extracted = ExtractedData(
        document_type="digital_communication",
        sender=None,
        message_text="Check this link: https://example-unknown-domain-test.xyz",
        urls=["https://example-unknown-domain-test.xyz"],
        phone_numbers=[],
        upi_ids=[],
        amounts=[],
        claimed_brand=None,
        detected_language="en",
        image_quality="text_only",
        visual_notes=[],
    )

    with patch("httpx.AsyncClient.get", side_effect=Exception("Connection timed out")):
        tool_results, tool_signals = await run_verifiers(extracted)
        # Should gracefully return without crashing
        assert isinstance(tool_results, list)
        assert isinstance(tool_signals, list)


# ==============================================================================
# 10. Unreadable or corrupted image
# ==============================================================================
def test_case_10_corrupted_image():
    corrupted_bytes = b"NOT_A_VALID_IMAGE_HEADER_BYTES_RANDOM_CORRUPT_DATA"

    response = client.post(
        "/api/analyze",
        files={"image": ("corrupted.png", corrupted_bytes, "image/png")},
        data={"mode": "mock", "language": "en"},
    )
    # Must fail safely with HTTP 400 Bad Request
    assert response.status_code == 400
    detail = response.json().get("detail", "")
    assert "image" in detail.lower() or "unsupported" in detail.lower() or "corrupt" in detail.lower() or "header" in detail.lower()


# ==============================================================================
# 11. Screenshot with no visible URL
# ==============================================================================
def test_case_11_screenshot_no_visible_url():
    text_no_url = "Paid ₹500 to Local Grocery Store. Payment completed successfully. Thank you."
    img_bytes = generate_png(text_no_url)

    response = client.post(
        "/api/analyze",
        files={"image": ("no_url.png", img_bytes, "image/png")},
        data={"text": text_no_url, "mode": "mock", "language": "en"},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["extracted"]["urls"] == []
    # Pipeline completed successfully
    assert res["status"] == "success"


# ==============================================================================
# 12. Image containing Tamil text
# ==============================================================================
def test_case_12_tamil_text():
    tamil_text = "ரூ. 1000 வெற்றிகரமாக செலுத்தப்பட்டது. பரிவர்த்தனை எண் 429812984123."
    img_bytes = generate_png(tamil_text)

    response = client.post(
        "/api/analyze",
        files={"image": ("tamil_receipt.png", img_bytes, "image/png")},
        data={"text": tamil_text, "mode": "mock", "language": "ta"},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["language"] == "ta"
    assert "ஸ்கேம்லென்ஸ்" in res["limitations"] or "மதிப்பீடு" in res["limitations"]


# ==============================================================================
# 13. Image containing Hindi text
# ==============================================================================
def test_case_13_hindi_text():
    hindi_text = "बधाई हो! आपने 25 लाख की लॉटरी जीती है। शुल्क जमा करें।"
    img_bytes = generate_png(hindi_text)

    response = client.post(
        "/api/analyze",
        files={"image": ("hindi_lottery.png", img_bytes, "image/png")},
        data={"text": hindi_text, "mode": "mock", "language": "hi"},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["language"] == "hi"
    assert "स्कैम लेंस" in res["limitations"] or "मूल्यांकन" in res["limitations"]


# ==============================================================================
# 14. Invalid or malformed AI response
# ==============================================================================
@pytest.mark.asyncio
async def test_case_14_malformed_ai_response():
    from app.services.extractor import extract_content

    class BrokenModelClient(ModelClient):
        async def generate(self, prompt: str, images=None, json_mode=True, temperature=0.0) -> str:
            return "{ MALFORMED_JSON_STRING_WITHOUT_CLOSING_BRACKET ..."

    mock_client = BrokenModelClient()
    # Must not crash; applies safe fallback
    result = await extract_content(
        raw_text="Payment of Rs 500 completed",
        model_client=mock_client,
    )
    assert isinstance(result, ExtractedData)
    assert "500" in " ".join(result.amounts)


# ==============================================================================
# 15. Missing or invalid API key
# ==============================================================================
def test_case_15_missing_or_invalid_api_key():
    with patch("app.config.settings.MODE", "cloud"), \
         patch("app.config.settings.GEMINI_API_KEY", ""):
        response = client.post(
            "/api/analyze",
            data={"text": "Test message", "mode": "cloud", "language": "en"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data.get("error_code") in ("KEY_MISSING", "KEY_REJECTED")


# ==============================================================================
# 16. Timeout or rate-limit error
# ==============================================================================
def test_case_16_timeout_or_rate_limit():
    with patch("app.api.routes.run_pipeline", side_effect=ModelTimeoutError("Request timed out after 30s")):
        response = client.post(
            "/api/analyze",
            data={"text": "Test message", "mode": "mock", "language": "en"},
        )
        assert response.status_code == 504
        assert response.json()["error_code"] == "TIMEOUT_ERROR"

    with patch("app.api.routes.run_pipeline", side_effect=ModelRateLimitError("Quota exceeded 429")):
        response = client.post(
            "/api/analyze",
            data={"text": "Test message", "mode": "mock", "language": "en"},
        )
        assert response.status_code == 429
        assert response.json()["error_code"] == "RATE_LIMIT_EXCEEDED"


# ==============================================================================
# 17. Request made while local mode is unavailable
# ==============================================================================
def test_case_17_local_mode_unavailable():
    with patch("app.api.routes.run_pipeline", side_effect=ModelUnavailableError("Cannot connect to local Ollama")):
        response = client.post(
            "/api/analyze",
            data={"text": "Test message", "mode": "local", "language": "en"},
        )
        assert response.status_code == 503
        data = response.json()
        assert data["error_code"] in ("OLLAMA_UNAVAILABLE", "SERVICE_UNAVAILABLE")
        assert "ollama" in data["detail"].lower()


# ==============================================================================
# 18. Request made while cloud mode is unavailable
# ==============================================================================
def test_case_18_cloud_mode_unavailable():
    with patch("app.config.settings.GEMINI_API_KEY", "dummy_configured_key"), \
         patch("app.api.routes.run_pipeline", side_effect=ModelUnavailableError("Google GenAI remote endpoint unreachable")):
        response = client.post(
            "/api/analyze",
            data={"text": "Test message", "mode": "cloud", "language": "en"},
        )
        assert response.status_code == 503
        data = response.json()
        assert "unavailable" in data["detail"].lower()
