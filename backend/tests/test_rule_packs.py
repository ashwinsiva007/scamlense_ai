"""
Unit Tests for Rule Packs & Threat Detection
--------------------------------------------
Validates positive and negative test cases for all 10 rule categories:
1. money_demands
2. credentials
3. urgency_threat
4. too_good
5. impersonation
6. links
7. sender
8. document_quality
9. payment_screenshot
10. reducers

SPEC REQUIREMENT: At least 2 positive and 2 negative cases per category.
Genuine bank alerts and transactional updates must NEVER be flagged as suspicious or scam.
"""

import pytest
from app.schemas import ExtractedData
from app.services.pipeline import run_pipeline
from app.services.rule_engine import evaluate_rules


def make_extracted(
    text: str,
    sender: str = None,
    urls: list = None,
    phones: list = None,
    upis: list = None,
    visual_notes: list = None,
    image_quality: str = "sharp",
) -> ExtractedData:
    return ExtractedData(
        document_type="sms",
        sender=sender,
        message_text=text,
        urls=urls or [],
        phone_numbers=phones or [],
        upi_ids=upis or [],
        amounts=[],
        claimed_brand=None,
        detected_language="en",
        image_quality=image_quality,
        visual_notes=visual_notes or [],
    )


# ==============================================================================
# 1. MONEY DEMANDS (2 Positive, 2 Negative)
# ==============================================================================

class TestMoneyDemandsPack:
    @pytest.mark.asyncio
    async def test_pos_job_registration_fee(self):
        text = "Selected for Virtual Internship. Pay registration fee of Rs 1499 to confirm seat."
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band in ("suspicious", "likely_scam")
        assert any(s.id == "MONEY_JOB_REGISTRATION_FEE" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_pos_pay_to_receive_parcel_or_prize(self):
        text = "Your parcel is on hold. Customs fee required: Pay Rs 750 for delivery."
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band in ("suspicious", "likely_scam")
        assert any(s.category == "money_demands" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_neg_broadband_bill_payment_receipt(self):
        text = "Payment received of INR 999 for your Airtel Xstream fiber account 102938475. Ref 892182910291."
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band == "low_risk"
        assert not any(s.category == "money_demands" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_neg_ecommerce_refund_credit(self):
        text = "Refund of INR 450 for returned item has been successfully processed to your bank account."
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band == "low_risk"
        assert not any(s.category == "money_demands" for s in resp.signals)


# ==============================================================================
# 2. CREDENTIALS (2 Positive, 2 Negative)
# ==============================================================================

class TestCredentialsPack:
    @pytest.mark.asyncio
    async def test_pos_otp_solicitation(self):
        text = "Dear customer, your card is blocked. Send 6 digit OTP to reactivate immediately."
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band in ("suspicious", "likely_scam")
        assert any(s.id == "CRED_OTP_SOLICITATION" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_pos_aadhaar_pan_harvesting(self):
        text = "Urgent: share photo of aadhaar and pan card to prevent immediate account closure."
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band in ("suspicious", "likely_scam")
        assert any(s.id == "CRED_AADHAAR_PAN_HARVESTING" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_neg_genuine_login_otp(self):
        text = "548921 is your secret OTP for login to your SBI NetBanking portal. Bank never asks for OTP. Do not share with anyone."
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band == "low_risk"
        assert resp.score == 0

    @pytest.mark.asyncio
    async def test_neg_branch_kyc_reminder(self):
        text = "Dear Customer, please visit your nearest home branch with original KYC documents to complete periodic re-KYC before 30-Nov."
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band == "low_risk"
        assert not any(s.category == "credentials" for s in resp.signals)


# ==============================================================================
# 3. URGENCY & THREAT (2 Positive, 2 Negative)
# ==============================================================================

class TestUrgencyThreatPack:
    @pytest.mark.asyncio
    async def test_pos_electricity_disconnection_tonight(self):
        text = "Electricity power will be disconnected tonight. Pay registration fee of Rs 1450 to avoid power cut."
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band in ("suspicious", "likely_scam")
        assert any(s.id == "URGENCY_ELECTRICITY_POWER_CUT" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_pos_police_digital_arrest_warrant(self):
        text = "Digital arrest warrant issued against you by police. Pay verification fee Rs 5000 now."
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band in ("suspicious", "likely_scam")
        assert any(s.id == "URGENCY_POLICE_LEGAL_ARREST" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_neg_scheduled_server_maintenance(self):
        text = "Dear customer, NetBanking will be temporarily unavailable due to scheduled maintenance on Sunday from 2 AM to 4 AM."
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band == "low_risk"
        assert not any(s.category == "urgency_threat" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_neg_normal_bill_due_date_notice(self):
        text = "Your electricity bill of INR 1,240 is generated. Due date is 25-Nov-2026. Pay online at official portal tnebltd.gov.in"
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band == "low_risk"
        assert not any(s.category == "urgency_threat" for s in resp.signals)


# ==============================================================================
# 4. TOO GOOD TO BE TRUE (2 Positive, 2 Negative)
# ==============================================================================

class TestTooGoodPack:
    @pytest.mark.asyncio
    async def test_pos_kbc_lottery_prize_winnings(self):
        text = "Congratulations! Your mobile number won first prize of Rs 25,00,000 in KBC All India SIM Lucky Draw. Pay processing fee Rs 5000."
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band in ("suspicious", "likely_scam")
        assert any(s.id == "TOO_GOOD_LOTTERY_PRIZE" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_pos_daily_youtube_like_tasks(self):
        text = "Earn Rs 500 per like on YouTube videos. Daily salary credited instantly up to Rs 8,000. Contact admin on Telegram for part time work."
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band in ("suspicious", "likely_scam")
        assert any(s.id == "TOO_GOOD_DAILY_TASKS_YOUTUBE" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_neg_genuine_career_job_vacancy(self):
        text = "Job Opportunity: Junior Software Engineer at Infosys. Qualifications: B.Tech in CS. Apply on careers.infosys.com"
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band == "low_risk"
        assert not any(s.category == "too_good" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_neg_routine_shopping_cashback(self):
        text = "Cashback of INR 25 credited to your account for shopping at Reliance Fresh with UPI."
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band == "low_risk"
        assert not any(s.category == "too_good" for s in resp.signals)


# ==============================================================================
# 5. IMPERSONATION (2 Positive, 2 Negative)
# ==============================================================================

class TestImpersonationPack:
    @pytest.mark.asyncio
    async def test_pos_bank_spoofing(self):
        text = "Dear customer, your SBI account KYC is expired. Update pan immediately to avoid account block at http://sbi-secure-portal.com"
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band in ("suspicious", "likely_scam")
        assert any(s.id == "IMPERSONATION_BANK_KYC" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_pos_courier_spoofing(self):
        text = "India Post: Your parcel is on hold due to wrong address. Update delivery address within 24 hours at http://bit.ly/indiapost-update"
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band in ("suspicious", "likely_scam")
        assert any(s.id == "IMPERSONATION_FAKE_COURIER" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_neg_genuine_bank_security_alert(self):
        text = "HDFC Bank: NetBanking password successfully changed. If this was not done by you, call 18002026161."
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band == "low_risk"
        assert not any(s.category == "impersonation" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_neg_genuine_courier_delivery(self):
        text = "Blue Dart: Shipment 123456789 is out for delivery with courier associate Ramesh."
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band == "low_risk"
        assert not any(s.category == "impersonation" for s in resp.signals)


# ==============================================================================
# 6. LINKS (2 Positive, 2 Negative)
# ==============================================================================

class TestLinksPack:
    @pytest.mark.asyncio
    async def test_pos_shortened_bitly_link(self):
        text = "Claim your electricity subsidy refund now: http://bit.ly/eb-subsidy-refund"
        resp = await run_pipeline(text=text, mode="mock")
        assert any(s.id == "LINK_SHORTENED_URL" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_pos_ip_address_port_link(self):
        text = "Login to your banking portal: http://192.168.1.1:8080/ebanking to verify documents."
        resp = await run_pipeline(text=text, mode="mock")
        assert any(s.id == "LINK_IP_OR_ODD_PORT" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_neg_official_amazon_store_link(self):
        text = "Your Amazon order is shipped. Track delivery on official site https://www.amazon.in/orders"
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band == "low_risk"
        assert not any(s.category == "links" and s.weight > 0 for s in resp.signals)

    @pytest.mark.asyncio
    async def test_neg_official_incometax_gov_link(self):
        text = "Income Tax Department: File your tax return before the deadline on https://www.incometax.gov.in"
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band == "low_risk"
        assert not any(s.category == "links" and s.weight > 0 for s in resp.signals)


# ==============================================================================
# 7. SENDER (2 Positive, 2 Negative)
# ==============================================================================

class TestSenderPack:
    @pytest.mark.asyncio
    async def test_pos_official_offer_from_freemail(self):
        text = "Official Google HR Recruitment offer letter from hr-recruitment@gmail.com with salary Rs 90,000/month."
        resp = await run_pipeline(text=text, mode="mock")
        assert any(s.id == "SENDER_FREE_WEBMAIL_OFFICIAL" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_pos_move_to_whatsapp_telegram(self):
        text = "Hi, this is HR. Contact us on WhatsApp at +919876543210 for interview."
        resp = await run_pipeline(text=text, mode="mock")
        assert any(s.id == "SENDER_MOVE_TO_PRIVATE_MESSAGING" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_neg_corporate_email_domain(self):
        text = "Interview scheduled for Junior Developer role from recruiting@hdfcbank.com on Monday."
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band == "low_risk"
        assert not any(s.category == "sender" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_neg_official_bank_sms_sender_id(self):
        text = "VM-HDFCBK: Your monthly account statement for October 2026 is ready."
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band == "low_risk"
        assert not any(s.category == "sender" for s in resp.signals)


# ==============================================================================
# 8. DOCUMENT QUALITY (2 Positive, 2 Negative)
# ==============================================================================

class TestDocumentQualityPack:
    def test_pos_visual_font_inconsistency(self):
        ext = make_extracted(
            text="Offer Letter for Management Trainee",
            visual_notes=["Inconsistent typography or letterhead distortion"],
        )
        score, band, signals, _, _ = evaluate_rules(ext)
        assert any(s.id == "DOC_VISUAL_FONT_INCONSISTENCY" for s in signals)

    def test_pos_missing_company_details(self):
        ext = make_extracted(
            text="Appointment Letter for Tech Analyst",
            visual_notes=["Missing CIN corporate registration details"],
        )
        score, band, signals, _, _ = evaluate_rules(ext)
        assert any(s.id == "DOC_MISSING_REGISTRATION_CIN" for s in signals)

    def test_neg_verified_cin_and_registered_office(self):
        ext = make_extracted(
            text="Official Corporate Letter. CIN: L65110MH1994PLC080618, Registered Office: Mumbai, Maharashtra.",
            visual_notes=["Clean professional letterhead"],
        )
        score, band, signals, _, _ = evaluate_rules(ext)
        assert score == 0
        assert not any(s.category == "document_quality" for s in signals)

    def test_neg_sharp_typography_and_barcode(self):
        ext = make_extracted(
            text="Tax Invoice #INV-2026-9812. GSTIN: 27AAACH7409R1ZZ.",
            visual_notes=["Clean official invoice"],
        )
        score, band, signals, _, _ = evaluate_rules(ext)
        assert score == 0
        assert not any(s.category == "document_quality" for s in signals)


# ==============================================================================
# 9. PAYMENT SCREENSHOT (2 Positive, 2 Negative)
# ==============================================================================

class TestPaymentScreenshotPack:
    @pytest.mark.asyncio
    async def test_pos_pending_status_presented_as_paid(self):
        text = "Payment status is pending. Awaiting bank confirmation. Money will reach within 24 hours."
        resp = await run_pipeline(text=text, mode="mock")
        assert any(s.id == "PAY_PENDING_STATUS_AS_PAID" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_pos_invalid_upi_utr(self):
        text = "Payment received. UTR: 12345 (5 digits only). Paid successfully."
        resp = await run_pipeline(text=text, mode="mock")
        assert any(s.id == "PAY_INVALID_UPI_UTR" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_neg_valid_12digit_upi_payment(self):
        text = "Paid to Swiggy INR 450.00. UPI Ref 429812984123. Status: Completed."
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band == "low_risk"
        assert not any(s.category == "payment_screenshot" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_neg_genuine_bank_debit_with_upi_ref(self):
        text = "A/c **4589 debited for INR 1,200 on 26-Oct-26. UPI Ref 628912345678. Avl Bal INR 15,000."
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band == "low_risk"
        assert not any(s.category == "payment_screenshot" for s in resp.signals)


# ==============================================================================
# 10. WEAK SIGNALS & REDUCERS (2 Positive, 2 Negative)
# ==============================================================================

class TestWeakSignalsAndReducers:
    @pytest.mark.asyncio
    async def test_pos_poor_grammar_scam(self):
        text = "Congratulation dear customer, kindly revert back urgent to claim prize money."
        resp = await run_pipeline(text=text, mode="mock")
        assert any(s.id == "DOC_POOR_GRAMMAR_TYPOS" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_pos_urgency_with_broken_grammar(self):
        text = "Congratulation you have won lottery kindly send fee."
        resp = await run_pipeline(text=text, mode="mock")
        assert any(s.id == "DOC_POOR_GRAMMAR_TYPOS" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_neg_grammatically_clean_notification(self):
        text = "Your fixed deposit account has matured. Amount credited to savings account."
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band == "low_risk"
        assert not any(s.id == "DOC_POOR_GRAMMAR_TYPOS" for s in resp.signals)

    @pytest.mark.asyncio
    async def test_neg_clean_official_brand_domain_reducer(self):
        text = "Explore fixed deposit interest rates at official website https://www.hdfcbank.com"
        resp = await run_pipeline(text=text, mode="mock")
        assert resp.band == "low_risk"
        assert resp.score == 0
        assert any(s.id == "REDUCER_VERIFIED_BRAND_DOMAIN" for s in resp.signals)


# ==============================================================================
# MULTILINGUAL TRANSLITERATED TESTS (Hinglish & Tanglish)
# ==============================================================================

class TestMultilingualTransliteratedThreats:
    @pytest.mark.asyncio
    async def test_hinglish_kyc_fraud(self):
        hinglish_text = "Sir aapka bank account block ho jayega aaj raat tak. Jaldi kyc update kare aur otp share kare."
        resp = await run_pipeline(text=hinglish_text, mode="mock")
        assert resp.band in ("suspicious", "likely_scam")

    @pytest.mark.asyncio
    async def test_tanglish_account_threat(self):
        tanglish_text = "Account block aagirum. OTP share pannunga to avoid cancellation."
        resp = await run_pipeline(text=tanglish_text, mode="mock")
        assert resp.band in ("suspicious", "likely_scam")
