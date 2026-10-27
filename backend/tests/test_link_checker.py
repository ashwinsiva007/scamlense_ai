from fastapi.testclient import TestClient
from app.main import app
from app.services.link_checker import analyze_link, is_likely_url

client = TestClient(app)

def test_analyze_link_brand_impersonation():
    res = analyze_link("http://paytm-kyc-update.top/verify?acc=1")
    assert res is not None
    assert res["score"] >= 60
    assert res["level"] == "bad"
    assert any("PAYTM" in f["title"] for f in res["findings"])

def test_analyze_link_official_domain():
    res = analyze_link("https://www.amazon.in")
    assert res is not None
    assert res["score"] == 0
    assert res["level"] == "good"
    assert res["trusted"] is True

def test_analyze_link_raw_ip():
    res = analyze_link("http://192.168.4.20/sbi/login.php")
    assert res is not None
    assert res["score"] >= 40
    assert any("number" in f["title"].lower() for f in res["findings"])

def test_is_likely_url():
    assert is_likely_url("https://example.com/test")
    assert is_likely_url("http://paytm-kyc.top")
    assert not is_likely_url("hello dear please call me tomorrow")

def test_check_link_api():
    response = client.post("/api/check-link", json={"url": "http://paytm-kyc-update.top/verify"})
    assert response.status_code == 200
    data = response.json()
    assert data["host"] == "paytm-kyc-update.top"
    assert data["score"] >= 60
