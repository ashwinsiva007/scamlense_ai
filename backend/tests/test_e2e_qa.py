"""
End-to-End Comprehensive QA Test Suite
--------------------------------------
Validates all flows across the stack:
- Image uploads (PNG, JPEG, WebP)
- Pasted text (scam vs genuine)
- Multilingual outputs (en, ta, hi)
- Modes (mock, cloud key validation, local connectivity)
- Sample fixtures
- Error cases (empty payload, wrong filetype, oversized upload, rate limits)
- SSRF security protection
"""

import io
import os
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from app.api.limiter import limiter
from app.config import settings
from app.main import app
from app.services.verifiers import check_url_ssrf_safety, is_ip_safe

client = TestClient(app)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def generate_png(text: str, width: int = 500, height: int = 300) -> bytes:
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((25, 25), text, fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture(autouse=True)
def reset_limiter_state():
    """Ensure rate limiter is fresh before and after each test."""
    limiter.reset()
    yield
    limiter.reset()


# ==============================================================================
# 1. Image Upload Flows (Scam vs Genuine)
# ==============================================================================

def test_image_upload_scam_flow():
    """Validates end-to-end flow for scam offer letter image."""
    img_path = os.path.join(REPO_ROOT, "samples", "sample_internship_offer.png")
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            img_bytes = f.read()
    else:
        img_bytes = generate_png("Virtual Internship Deposit Rs 1500 to techcareers@okaxis within 24 hours")

    response = client.post(
        "/api/analyze",
        files={"image": ("internship.png", img_bytes, "image/png")},
        data={"mode": "mock", "language": "en"},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["band"] in ("suspicious", "likely_scam")
    assert res["score"] >= 30
    assert len(res["signals"]) > 0
    assert res["family_alert"]["title"] is not None
    assert len(res["next_steps"]) > 0
    assert "limitations" in res
    assert res["timings_ms"]["total"] >= 0


def test_image_upload_genuine_debit_flow():
    """Validates end-to-end flow for genuine bank transaction notification image."""
    genuine_text = "A/c *1234 debited by INR 450.00 on 26-OCT-26 at SWIGGY. UPI Ref 429812984123. If not done by you call 18001600."
    img_bytes = generate_png(genuine_text)

    response = client.post(
        "/api/analyze",
        files={"image": ("bank_debit.png", img_bytes, "image/png")},
        data={"text": genuine_text, "mode": "mock", "language": "en"},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["band"] == "low_risk"
    assert res["score"] <= 29


# ==============================================================================
# 2. Pasted Text Flows
# ==============================================================================

def test_pasted_text_scam_english():
    text = "Congratulations! You have won Rs 25,00,000 in KBC Lottery. Deposit registration fee Rs 5,000 to claim."
    response = client.post(
        "/api/analyze",
        data={"text": text, "mode": "mock", "language": "en"},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["band"] in ("suspicious", "likely_scam")
    assert res["score"] >= 40


def test_pasted_text_genuine_sms():
    text = "Dear Customer, INR 250.00 debited from A/c XX8923 on 26-OCT-26 at METRO STORE. Bal: INR 12,450.00."
    response = client.post(
        "/api/analyze",
        data={"text": text, "mode": "mock", "language": "en"},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["band"] == "low_risk"
    assert res["score"] == 0


# ==============================================================================
# 3. Multilingual Flow (English, Tamil, Hindi)
# ==============================================================================

def test_tamil_language_flow():
    text = "மின்சாரக் கட்டணம் செலுத்தவில்லை என்றால் உங்கள் இணைப்பு இன்று இரவு 9:30 மணிக்கு துண்டிக்கப்படும்."
    response = client.post(
        "/api/analyze",
        data={"text": text, "mode": "mock", "language": "ta"},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["language"] == "ta"
    # Check that family alert or explanation contains Tamil characters
    has_tamil = any("\u0b80" <= c <= "\u0bff" for c in res["explanation"] + res["family_alert"]["body"])
    assert has_tamil, "Expected Tamil script in localized output"


def test_hindi_language_flow():
    text = "घर बैठे पार्ट टाइम काम करें। यूट्यूब वीडियो लाइक करके रोजाना 5000 रुपये कमाएं।"
    response = client.post(
        "/api/analyze",
        data={"text": text, "mode": "mock", "language": "hi"},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["language"] == "hi"
    has_hindi = any("\u0900" <= c <= "\u097f" for c in res["explanation"] + res["family_alert"]["body"])
    assert has_hindi, "Expected Devanagari Hindi script in localized output"


# ==============================================================================
# 4. Mode Routing & Graceful Error Handling
# ==============================================================================

def test_cloud_mode_missing_api_key():
    """In cloud mode, missing GEMINI_API_KEY must return 401 with typed message."""
    if not settings.GEMINI_API_KEY:
        response = client.post(
            "/api/analyze",
            data={"text": "Test message", "mode": "cloud"},
        )
        assert response.status_code == 401
        assert "authentication failed" in response.json()["detail"].lower()


def test_local_mode_unreachable_daemon():
    """In local mode, unreachable daemon must return 503 or handled error."""
    response = client.post(
        "/api/analyze",
        data={"text": "Test message", "mode": "local"},
    )
    assert response.status_code in (200, 503, 504)


# ==============================================================================
# 5. Error Cases: Empty, Corrupt, Oversized, Wrong Type, Rate Limit
# ==============================================================================

def test_empty_input_error():
    """Calling /api/analyze without image and without text returns 400."""
    response = client.post("/api/analyze", data={"mode": "mock"})
    assert response.status_code == 400
    assert "At least one of 'image' or 'text' must be provided." in response.json()["detail"]


def test_corrupt_file_error():
    """Uploading random junk bytes disguised as PNG returns 400."""
    response = client.post(
        "/api/analyze",
        files={"image": ("broken.png", b"\x89PNG\r\n\x1a\ncorruptpayloadhere", "image/png")},
        data={"mode": "mock"},
    )
    assert response.status_code == 400
    assert "corrupt" in response.json()["detail"].lower() or "decode" in response.json()["detail"].lower()


def test_unsupported_filetype_error():
    """Uploading unsupported binary format returns 400."""
    response = client.post(
        "/api/analyze",
        files={"image": ("test.bin", b"\x00\x01\x02\x03\x04notasupportedfiletype", "application/octet-stream")},
        data={"mode": "mock"},
    )
    assert response.status_code == 400


def test_oversized_payload_error():
    """Uploading an image exceeding MAX_UPLOAD_MB returns 413."""
    oversize_bytes = b"X" * (settings.MAX_UPLOAD_MB * 1024 * 1024 + 512)
    response = client.post(
        "/api/analyze",
        files={"image": ("huge.png", oversize_bytes, "image/png")},
        data={"mode": "mock"},
    )
    assert response.status_code == 413
    assert "exceeds maximum allowed limit" in response.json()["detail"]


def test_sliding_window_rate_limiting():
    """Breaching rate limit returns HTTP 429."""
    limiter.reset()
    for _ in range(settings.RATE_LIMIT_PER_MIN):
        limiter.check_rate_limit("192.0.2.1")

    with pytest.raises(Exception) as excinfo:
        limiter.check_rate_limit("192.0.2.1")
    assert "429" in str(excinfo.value) or "Rate limit exceeded" in str(excinfo.value)


# ==============================================================================
# 6. SSRF Protection & Security Checks
# ==============================================================================

@pytest.mark.asyncio
async def test_ssrf_blocks_private_and_metadata_ips():
    assert not is_ip_safe("127.0.0.1")
    assert not is_ip_safe("169.254.169.254")
    assert not is_ip_safe("10.0.0.1")
    assert not is_ip_safe("192.168.1.1")
    assert not is_ip_safe("0.0.0.0")
    assert not is_ip_safe("::1")
    assert is_ip_safe("8.8.8.8")
    assert is_ip_safe("142.250.190.46")


@pytest.mark.asyncio
async def test_ssrf_blocks_metadata_urls():
    safe, reason = await check_url_ssrf_safety("http://169.254.169.254/latest/meta-data")
    assert not safe
    safe_loc, _ = await check_url_ssrf_safety("http://localhost:8000/api/health")
    assert not safe_loc


# ==============================================================================
# 7. Benchmarks & Health Endpoints
# ==============================================================================

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    res = response.json()
    assert res["status"] == "ok"
    assert "mode" in res
    assert "model" in res


def test_benchmarks_endpoint():
    response = client.get("/api/benchmarks")
    assert response.status_code == 200
    res = response.json()
    assert res["total_eval_samples"] >= 12
    assert 0.0 <= res["accuracy"] <= 1.0
    assert 0.0 <= res["precision"] <= 1.0
    assert 0.0 <= res["recall"] <= 1.0
    assert res["rule_packs_loaded"] == 10
