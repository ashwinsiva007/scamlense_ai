import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw
from app.api.limiter import limiter
from app.config import settings
from app.main import app
from app.schemas import ExtractedData
from app.services.extractor import extract_content
from app.services.image_utils import validate_and_process_image, ImageValidationError
from app.services.model_client import MockClient

client = TestClient(app)


def create_test_image(
    width: int = 400,
    height: int = 300,
    format_name: str = "PNG",
    color: tuple = (255, 255, 255),
    text: str = "Test Image",
) -> bytes:
    """Helper to generate in-memory synthetic image bytes for testing."""
    img = Image.new("RGB", (width, height), color=color)
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), text, fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format=format_name)
    return buf.getvalue()


# ==============================================================================
# 1. Valid Image Upload Test
# ==============================================================================

def test_valid_image_upload():
    img_bytes = create_test_image(
        width=500,
        height=400,
        format_name="PNG",
        text="Offer letter deposit Rs 1500 to techcareers@okaxis within 24 hours",
    )
    files = {"image": ("offer.png", img_bytes, "image/png")}
    data = {"mode": "mock", "language": "en"}

    response = client.post("/api/analyze", files=files, data=data)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["band"] in ["low_risk", "suspicious", "likely_scam", "insufficient_info"]
    assert "extracted" in res_json
    assert res_json["extracted"]["document_type"] is not None
    assert res_json["timings_ms"]["validation"] >= 0
    assert res_json["timings_ms"]["extraction"] >= 0


# ==============================================================================
# 2. Wrong Image Type Test
# ==============================================================================

def test_wrong_image_type():
    # Attempt to upload plain text disguised as image
    files = {"image": ("fake.png", b"This is just a text file, not an image.", "image/png")}
    response = client.post("/api/analyze", files=files, data={"mode": "mock"})
    assert response.status_code == 400
    assert "Corrupt" in response.json()["detail"] or "decode" in response.json()["detail"]


def test_unsupported_image_format():
    # BMP is not in {JPEG, PNG, WEBP}
    img = Image.new("RGB", (200, 200), (255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="BMP")
    bmp_bytes = buf.getvalue()

    files = {"image": ("test.bmp", bmp_bytes, "image/bmp")}
    response = client.post("/api/analyze", files=files, data={"mode": "mock"})
    assert response.status_code == 400
    assert "Unsupported image format" in response.json()["detail"]


# ==============================================================================
# 3. Oversize Image Test
# ==============================================================================

def test_oversize_image_upload():
    # Construct a byte stream that exceeds MAX_UPLOAD_MB
    oversize_bytes = b"0" * (settings.MAX_UPLOAD_MB * 1024 * 1024 + 1024)
    files = {"image": ("huge.png", oversize_bytes, "image/png")}

    response = client.post("/api/analyze", files=files, data={"mode": "mock"})
    assert response.status_code == 413
    assert "exceeds maximum allowed limit" in response.json()["detail"]


# ==============================================================================
# 4. Corrupt File Test
# ==============================================================================

def test_corrupt_image_upload():
    # Valid PNG header followed by truncated/corrupt bytes
    corrupt_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"garbage" * 10
    files = {"image": ("corrupted.png", corrupt_bytes, "image/png")}

    response = client.post("/api/analyze", files=files, data={"mode": "mock"})
    assert response.status_code == 400
    assert "Corrupt" in response.json()["detail"] or "decode" in response.json()["detail"]


# ==============================================================================
# 5. Empty Request Test (neither image nor text)
# ==============================================================================

def test_empty_request_rejected():
    response = client.post("/api/analyze", data={"language": "en", "mode": "mock"})
    assert response.status_code == 400
    assert "At least one of 'image' or 'text' must be provided." in response.json()["detail"]


# ==============================================================================
# 6. Malformed Model JSON Then Repaired Test
# ==============================================================================

class FlakyMockClient(MockClient):
    """Fails on first invocation with malformed JSON, then succeeds on repair invocation."""
    def __init__(self):
        super().__init__()
        self.call_count = 0

    async def generate(self, prompt: str, images=None, json_mode=True, temperature=0.0, system_instruction=None) -> str:
        self.call_count += 1
        if self.call_count == 1:
            # First attempt: invalid broken JSON
            return '{"document_type": "offer_letter", "message_text": "Deposit fee'
        else:
            # Repair attempt: valid JSON
            return (
                '{"document_type": "offer_letter", "sender": "hr@test.com", '
                '"message_text": "Deposit refundable fee Rs 1500 to techcareers@okaxis within 24 hours.", '
                '"urls": ["http://test.com"], "phone_numbers": ["+919876543210"], '
                '"upi_ids": ["techcareers@okaxis"], "amounts": ["Rs 1500"], '
                '"claimed_brand": "TestCorp", "detected_language": "en", '
                '"image_quality": "sharp", "visual_notes": ["Repaired successfully"]}'
            )


@pytest.mark.asyncio
async def test_malformed_model_json_repair():
    flaky_client = FlakyMockClient()
    extracted = await extract_content(
        image_bytes=None,
        raw_text="Deposit refundable fee Rs 1500",
        image_quality="text_only",
        model_client=flaky_client,
    )

    # Verify repair succeeded on second attempt
    assert flaky_client.call_count == 2
    assert extracted.document_type == "offer_letter"
    assert "techcareers@okaxis" in extracted.upi_ids
    assert "Rs 1500" in extracted.amounts
    assert extracted.visual_notes == ["Repaired successfully"]


# ==============================================================================
# 7. Text-Only Input Test
# ==============================================================================

def test_text_only_input():
    payload = {
        "text": "India Post Alert: Your parcel #IN892348 is stopped at sorting hub. Update at http://indiapost-parcel-update.top",
        "language": "en",
        "mode": "mock",
    }
    response = client.post("/api/analyze", data=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["extracted"]["image_quality"] == "text_only"
    assert len(res_json["extracted"]["urls"]) > 0
    assert "http://indiapost-parcel-update.top" in res_json["extracted"]["urls"]
    assert res_json["confidence"] == "high"


# ==============================================================================
# 8. In-Memory Rate Limiting Test
# ==============================================================================

def test_rate_limiting():
    limiter.reset()
    test_ip = "192.168.1.99"
    headers = {"X-Forwarded-For": test_ip}

    # Execute RATE_LIMIT_PER_MIN requests
    for i in range(settings.RATE_LIMIT_PER_MIN):
        res = client.post(
            "/api/analyze",
            data={"text": f"Test message {i}", "mode": "mock"},
            headers=headers,
        )
        assert res.status_code == 200, f"Request {i} failed with {res.status_code}"

    # The (RATE_LIMIT_PER_MIN + 1)-th request must be rejected with 429
    blocked_res = client.post(
        "/api/analyze",
        data={"text": "Rate limited request", "mode": "mock"},
        headers=headers,
    )
    assert blocked_res.status_code == 429
    assert "Rate limit exceeded" in blocked_res.json()["detail"]

    # Reset limiter after test
    limiter.reset()


# ==============================================================================
# 9. Health Endpoint Status & Cloud Key Flag
# ==============================================================================

def test_health_reports_cloud_key_status():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "cloud_key_set" in data
    assert "ollama_reachable" in data
    assert data["status"] == "ok"
