"""
Unit Tests for Rule Packs & Threat Detection
--------------------------------------------
Validates positive and negative test cases for all 10 rule packs.
Ensures standard informative bank debit alerts and genuine login OTPs NEVER trigger false positives.
"""

import pytest
from app.services.pipeline import run_pipeline


class TestRulePacksThreatDetection:
    """Verifies that high-threat scam messages trigger suspicious or likely_scam bands."""

    @pytest.mark.asyncio
    async def test_fake_job_offer_with_registration_fee(self):
        text = (
            "Congratulations! You are shortlisted for Google Virtual Internship. "
            "Daily salary Rs 4500 without interview or experience. "
            "Pay registration fee of Rs 1499 to confirm seat."
        )
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band in ("suspicious", "likely_scam")
        assert resp.score >= 30
        fired_ids = [s.id for s in resp.signals]
        assert "MONEY_JOB_REGISTRATION_FEE" in fired_ids or "TOO_GOOD_HIGH_PAY_NO_INTERVIEW" in fired_ids

    @pytest.mark.asyncio
    async def test_fake_payment_pending_screenshot(self):
        text = (
            "Transaction status: Pending. Awaiting bank confirmation. "
            "Money will reach within 24 hours. UTR: 98124."
        )
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band in ("suspicious", "likely_scam")
        fired_ids = [s.id for s in resp.signals]
        assert "PAY_PENDING_STATUS_AS_PAID" in fired_ids or "PAY_INVALID_UPI_UTR" in fired_ids

    @pytest.mark.asyncio
    async def test_electricity_power_cut_threat(self):
        text = (
            "Dear Consumer, electricity power will be disconnected tonight from the power station "
            "because your previous month bill was not updated. Call electricity officer now."
        )
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band in ("suspicious", "likely_scam")
        fired_ids = [s.id for s in resp.signals]
        assert "URGENCY_ELECTRICITY_POWER_CUT" in fired_ids

    @pytest.mark.asyncio
    async def test_kbc_lottery_prize(self):
        text = (
            "Congratulations! Your mobile number won first prize of Rs 25,00,000 in KBC All India SIM Lucky Draw. "
            "Pay processing fee Rs 5000 to receive prize."
        )
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band in ("suspicious", "likely_scam")
        fired_ids = [s.id for s in resp.signals]
        assert "TOO_GOOD_LOTTERY_PRIZE" in fired_ids

    @pytest.mark.asyncio
    async def test_telegram_youtube_tasks(self):
        text = (
            "Earn Rs 500 per like on YouTube videos. Daily salary credited instantly up to Rs 8,000. "
            "Contact admin on Telegram for part time work."
        )
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band in ("suspicious", "likely_scam")
        fired_ids = [s.id for s in resp.signals]
        assert "TOO_GOOD_DAILY_TASKS_YOUTUBE" in fired_ids

    @pytest.mark.asyncio
    async def test_transliterated_hinglish_and_tanglish(self):
        hinglish_text = "Sir aapka bank account block ho jayega aaj raat tak. Jaldi kyc update kare aur otp share kare."
        resp_hi = await run_pipeline(text=hinglish_text, mode="mock")
        assert resp_hi.band in ("suspicious", "likely_scam")

        tanglish_text = "Account block aagirum. OTP share pannunga to avoid cancellation."
        resp_ta = await run_pipeline(text=tanglish_text, mode="mock")
        assert resp_ta.band in ("suspicious", "likely_scam")


class TestGenuineNotificationsZeroFalsePositives:
    """CRITICAL: Verifies that genuine transactional notifications NEVER evaluate to suspicious or scam."""

    @pytest.mark.asyncio
    async def test_genuine_bank_masked_debit_sms(self):
        text = (
            "Dear Customer, A/c **4589 has been debited for INR 450.00 at SWIGGY BANGALORE "
            "on 26-Oct-2026. Avl Bal: INR 18,250.00. Report unauthorized transactions to 1800112211."
        )
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band == "low_risk"
        assert resp.score == 0
        assert "no major red flags found" in resp.explanation.lower()

    @pytest.mark.asyncio
    async def test_genuine_login_otp_sms(self):
        text = (
            "548921 is your secret OTP for login to your SBI NetBanking portal. "
            "Valid for 10 minutes. Bank never asks for OTP. Do not share with anyone."
        )
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band == "low_risk"
        assert resp.score == 0

    @pytest.mark.asyncio
    async def test_genuine_delivery_notification(self):
        text = (
            "Your Amazon order 402-9832711-291823 has been delivered to your doorstep. "
            "Thank you for shopping with us. Manage your orders on amazon.in"
        )
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band == "low_risk"
        assert resp.score < 30
