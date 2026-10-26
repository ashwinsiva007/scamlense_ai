#!/usr/bin/env python3
"""
ScamLens End-to-End Smoke Test Script
-------------------------------------
Executes a rapid smoke test verifying upload to result for:
1. One scam sample (Fake Internship Offer with advance UPI fee)
2. One genuine sample (Legitimate Bank Debit Alert with masked account)
3. Multilingual rendering check (Tamil & Hindi)
4. Health & Benchmarks endpoint check
"""

import io
import os
import sys

# Configure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(repo_root, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw
from app.main import app

client = TestClient(app)


def generate_test_image(text: str, width: int = 600, height: int = 400) -> bytes:
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 30), text, fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def run_smoke_test():
    print("=" * 65)
    print("🚀 ScamLens Automated End-to-End Smoke Test")
    print("=" * 65)

    passed = 0
    total = 4

    # 1. Health check
    print("\n[1/4] Testing GET /api/health...")
    resp = client.get("/api/health")
    assert resp.status_code == 200, f"Health check failed: {resp.status_code}"
    health = resp.json()
    print(f"      Status: {health['status']} | Mode: {health['mode']} | Model: {health['model']}")
    passed += 1

    # 2. Scam Sample Upload to Result
    print("\n[2/4] Testing Scam Sample Flow (Fake Internship Offer)...")
    sample_img_path = os.path.join(repo_root, "frontend", "public", "samples", "fake_internship_offer.png")
    if os.path.exists(sample_img_path):
        with open(sample_img_path, "rb") as f:
            img_bytes = f.read()
    else:
        img_bytes = generate_test_image("Google Internship Offer: Pay refundable security fee Rs 1500 to techcareers@okaxis within 24 hours.")

    resp = client.post(
        "/api/analyze",
        files={"image": ("internship.png", img_bytes, "image/png")},
        data={"mode": "mock", "language": "en"},
    )
    assert resp.status_code == 200, f"Scam upload failed with HTTP {resp.status_code}: {resp.text}"
    scam_res = resp.json()
    print(f"      Verdict: {scam_res['band']} (Score: {scam_res['score']})")
    print(f"      Quoted Evidence: {[s['evidence'] for s in scam_res['signals'][:2]]}")
    print(f"      Family Alert: {scam_res['family_alert']['title']}")
    assert scam_res["band"] in ("suspicious", "likely_scam"), f"Expected scam band, got {scam_res['band']}"
    assert scam_res["score"] >= 30, f"Expected score >= 30, got {scam_res['score']}"
    assert len(scam_res["signals"]) > 0, "Expected signals to fire"
    passed += 1

    # 3. Genuine Sample Upload to Result
    print("\n[3/4] Testing Genuine Sample Flow (Masked Bank Debit Alert)...")
    debit_text = "A/c *1234 debited by INR 450.00 on 26-OCT-26 at SWIGGY BANGALORE. UPI Ref 429812984123. If not done by you, forward to 9223008333 or call 18001600."
    gen_img_bytes = generate_test_image(debit_text)

    resp = client.post(
        "/api/analyze",
        files={"image": ("debit.png", gen_img_bytes, "image/png")},
        data={"text": debit_text, "mode": "mock", "language": "en"},
    )
    assert resp.status_code == 200, f"Genuine upload failed with HTTP {resp.status_code}: {resp.text}"
    gen_res = resp.json()
    print(f"      Verdict: {gen_res['band']} (Score: {gen_res['score']})")
    print(f"      Reducers/Signals Count: {len(gen_res['signals'])}")
    assert gen_res["band"] == "low_risk", f"Expected low_risk band, got {gen_res['band']}"
    assert gen_res["score"] <= 29, f"Expected score <= 29, got {gen_res['score']}"
    passed += 1

    # 4. Multilingual Rendering (Tamil & Hindi)
    print("\n[4/4] Testing Multilingual Explanations (Tamil & Hindi)...")
    ta_resp = client.post(
        "/api/analyze",
        data={"text": "மின் கட்டணம் செலுத்தவில்லை என்றால் உங்கள் மின் இணைப்பு இன்று இரவு துண்டிக்கப்படும்.", "language": "ta", "mode": "mock"},
    )
    assert ta_resp.status_code == 200
    ta_json = ta_resp.json()
    print(f"      Tamil Explainer Title: {ta_json['family_alert']['title']}")

    hi_resp = client.post(
        "/api/analyze",
        data={"text": "पार्ट टाइम काम करके रोजाना 5000 कमाएं। टेलीग्राम ग्रुप जॉइन करें।", "language": "hi", "mode": "mock"},
    )
    assert hi_resp.status_code == 200
    hi_json = hi_resp.json()
    print(f"      Hindi Explainer Title: {hi_json['family_alert']['title']}")
    passed += 1

    print("\n" + "=" * 65)
    print(f"✅ Smoke Test Complete: {passed}/{total} flows verified successfully!")
    print("=" * 65)


if __name__ == "__main__":
    run_smoke_test()
