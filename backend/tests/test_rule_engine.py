"""
Unit Tests for Rule Engine Service
----------------------------------
Tests category score caps (+45 max), model signal caps (+10 max),
exact evidence substring verification, reducers, and score clamping.
"""

import pytest
from app.schemas import ExtractedData, Signal
from app.services.rule_engine import evaluate_rules


def make_extracted(text: str, urls=None, phones=None, upis=None) -> ExtractedData:
    return ExtractedData(
        document_type="sms",
        sender=None,
        message_text=text,
        urls=urls or [],
        phone_numbers=phones or [],
        upi_ids=upis or [],
        amounts=[],
        claimed_brand=None,
        detected_language="en",
        image_quality="sharp",
        visual_notes=[],
    )


class TestRuleEngineScoringAndCaps:
    def test_category_score_cap_at_45(self):
        """Even if multiple rules in the same category fire for +120, category contribution is capped at +45."""
        text = (
            "Congratulations! Shortlisted for job with high salary no interview. "
            "Guaranteed 100% daily returns on investment. You have won first prize lottery of Rs 1000000. "
            "Earn Rs 500 per like on YouTube videos. Double your Bitcoin in 24 hours."
        )
        extracted = make_extracted(text)
        score, band, signals, scam_type, confidence = evaluate_rules(extracted)

        # Confirm multiple too_good signals fired
        too_good_signals = [s for s in signals if s.category == "too_good"]
        assert len(too_good_signals) >= 3
        # Total sum of too_good signals exceeds 45, but overall category cap must hold
        raw_sum = sum(s.weight for s in too_good_signals)
        assert raw_sum > 45.0
        # If too_good is the only category fired, score cannot exceed 45
        assert score == 45
        assert band == "suspicious"

    def test_model_signals_capped_at_10(self):
        """Model-suggested signals are capped at +10 total and require exact substring evidence."""
        text = "Hello friend, meet me at the park tomorrow."
        extracted = make_extracted(text)

        # 3 model signals with total weight +40, but only 2 have exact substring evidence
        model_sigs = [
            Signal(
                id="MODEL_FLAG_1",
                label="Model Flag 1",
                category="other",
                weight=15.0,
                evidence="meet me",  # present in text
                source="model",
            ),
            Signal(
                id="MODEL_FLAG_2",
                label="Model Flag 2",
                category="other",
                weight=15.0,
                evidence="at the park",  # present in text
                source="model",
            ),
            Signal(
                id="MODEL_FLAG_3",
                label="Model Flag 3",
                category="other",
                weight=10.0,
                evidence="hallucinated phrase not in text",  # NOT in text, should be discarded
                source="model",
            ),
        ]

        score, band, signals, _, _ = evaluate_rules(extracted, model_signals=model_sigs)

        # The third signal must be discarded
        assert not any(s.id == "MODEL_FLAG_3" for s in signals)
        # Surviving model signals contribute max +10
        assert score == 10
        assert band == "low_risk"

    def test_exact_evidence_substring_validation(self):
        """Signals without verbatim evidence in input text are dropped."""
        text = "Simple text without any credentials or fees."
        extracted = make_extracted(text)
        score, band, signals, _, _ = evaluate_rules(extracted)
        for sig in signals:
            assert sig.evidence in text

    def test_reducers_subtract_points(self):
        """Reducers with negative weights decrease the risk score."""
        debit_text = "A/c **4589 debited by INR 450.00 at SWIGGY. Avl Bal: INR 12000. Report to 1800112211."
        extracted = make_extracted(debit_text)
        score, band, signals, _, _ = evaluate_rules(extracted)

        # Should fire REDUCER_STANDARD_MASKED_DEBIT_SMS with weight -20
        assert any(s.id == "REDUCER_STANDARD_MASKED_DEBIT_SMS" for s in signals)
        assert score == 0
        assert band == "low_risk"

    def test_score_clamped_strictly_between_0_and_100(self):
        """Score cannot drop below 0 or exceed 100."""
        # Genuine text with reducer
        text = "A/c **4589 debited by INR 450.00. Avl Bal: INR 12000."
        extracted = make_extracted(text)
        score, _, _, _, _ = evaluate_rules(extracted)
        assert score >= 0

        # Maximum threat text with signals across many categories
        max_threat = (
            "URGENT: SBI bank account is suspended today. Pay Rs 2000 registration fee to careers@okaxis "
            "or digital arrest warrant issued against you by police. Tell me the 6-digit OTP now. "
            "Congratulations you won Rs 2500000 lottery! Click http://sbi-fake-portal.xyz"
        )
        extracted_max = make_extracted(max_threat)
        score_max, band_max, _, _, _ = evaluate_rules(extracted_max)
        assert score_max <= 100
        assert band_max == "likely_scam"
