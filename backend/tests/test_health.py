import pytest
from fastapi.testclient import TestClient
from app.api.limiter import limiter
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    limiter.reset()
    yield
    limiter.reset()


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["service"] == "ScamLens API"


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "mode" in data
    assert "model" in data
    assert "ollama_reachable" in data
    assert "cloud_key_set" in data


def test_benchmarks_endpoint():
    response = client.get("/api/benchmarks")
    assert response.status_code == 200
    data = response.json()
    assert data["rule_packs_loaded"] >= 9


def test_analyze_requires_input():
    response = client.post("/api/analyze", data={})
    assert response.status_code == 400
    assert "At least one of 'image' or 'text' must be provided." in response.json()["detail"]


def test_analyze_real_pipeline_mock_mode():
    payload = {
        "text": "Deposit refundable security fee of Rs. 1500 to secure your seat at techcareers@okaxis",
        "language": "en",
        "mode": "mock",
    }
    response = client.post("/api/analyze", data=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["band"] in ["low_risk", "suspicious", "likely_scam", "insufficient_info"]
    assert "extracted" in data
    assert "techcareers@okaxis" in data["extracted"]["upi_ids"]
    assert "Family Alert" in data["family_alert"]["title"] or "Notice" in data["family_alert"]["title"] or "Alert" in data["family_alert"]["title"]


def test_analyze_multilingual_tamil():
    payload = {
        "text": "Deposit refundable security fee Rs 1500 to secure your seat",
        "language": "ta",
        "mode": "mock",
    }
    response = client.post("/api/analyze", data=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "ta"
    assert "தகவல்" in data["family_alert"]["title"] or "எச்சரிக்கை" in data["family_alert"]["title"]


def test_analyze_multilingual_hindi():
    payload = {
        "text": "Deposit refundable security fee Rs 1500 to secure your seat",
        "language": "hi",
        "mode": "mock",
    }
    response = client.post("/api/analyze", data=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "hi"
    assert "सूचना" in data["family_alert"]["title"] or "चेतावनी" in data["family_alert"]["title"]
