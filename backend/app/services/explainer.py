"""
Explainer Service
-----------------
Synthesizes structured findings, quoted signals, and tool results into plain-language
explanations, actionable next steps, and a shareable Family Alert card in en, ta, or hi.
Enforces non-absolving safety language, safety post-checks, and resilient fallback templates.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from app.schemas import BandType, FamilyAlert, LanguageType, Signal, ToolResult
from app.services.model_client import ModelClient, get_model_client

logger = logging.getLogger(__name__)

# Official Indian Helplines
CYBERCRIME_HELPLINE = "1930"
CYBERCRIME_PORTAL = "cybercrime.gov.in"
SANCHAR_SAATHI_PORTAL = "sancharsaathi.gov.in"

# ------------------------------------------------------------------------------
# Robust Multilingual Static Fallback Templates
# ------------------------------------------------------------------------------
FALLBACK_TEMPLATES: Dict[LanguageType, Dict[BandType, Dict[str, Any]]] = {
    "en": {
        "low_risk": {
            "explanation": (
                "No major red flags found. No known scam patterns, advance fee demands, or credential requests "
                "were detected in the analyzed message. However, the absence of obvious flags does not guarantee "
                "complete authenticity; always exercise routine caution."
            ),
            "next_steps": [
                "Verify official notifications directly inside your authorized mobile banking or official app.",
                "Never share your NetBanking password, OTP, or UPI PIN with anyone, even if they claim to be a bank official.",
                "If in doubt, contact customer support using verified numbers from official websites.",
            ],
            "family_alert": {
                "title": "ℹ️ Notice: No Major Red Flags Found",
                "body": "No common scam indicators were found in this message. However, stay vigilant and never share passwords or banking OTPs.",
                "tips": [
                    "Banks never ask for passwords, OTPs, or UPI PINs.",
                    "Always verify through official banking applications.",
                ],
            },
        },
        "suspicious": {
            "explanation": (
                "This message shows signs of suspicious activity. It contains potential red flags such as unusual urgency, "
                "unverified links, or requests to move communications to private channels. Exercise extreme caution."
            ),
            "next_steps": [
                "Do not click any embedded links or download attachments.",
                "Verify the claim independently by calling the official customer service number from the organization's verified website.",
                "Never share your OTP, PIN, or transfer token advance amounts.",
                f"If you suspect fraudulent activity, report it to the National Cybercrime Helpline at {CYBERCRIME_HELPLINE} or {CYBERCRIME_PORTAL}.",
            ],
            "family_alert": {
                "title": "⚠️ Caution: Suspicious Message Detected",
                "body": "A message was flagged with potential scam markers. Do not click links or send any money without independent verification.",
                "tips": [
                    "Do not click links or reply to the sender.",
                    "Call the company's verified official helpline to double check.",
                    "Never enter your UPI PIN to receive money.",
                ],
            },
        },
        "likely_scam": {
            "explanation": (
                "This message exhibits strong characteristics commonly associated with fraudulent scams. "
                "Multiple high-confidence red flags were detected, including direct requests for upfront money, "
                "coercive threats of account suspension, or unverified contact channels."
            ),
            "next_steps": [
                "Do NOT transfer any money, registration fees, or advance deposits under any circumstance.",
                "Never reveal your OTP, UPI PIN, NetBanking password, or Aadhaar/PAN details.",
                "Block and report the sender on your messaging app.",
                f"Report this incident immediately to the National Cybercrime Portal ({CYBERCRIME_PORTAL}) or call {CYBERCRIME_HELPLINE}.",
                "If payment screenshot is claimed, verify your official bank balance directly in your banking app.",
            ],
            "family_alert": {
                "title": "🚨 Warning: High Risk Scam Alert",
                "body": "Please be very careful! This message shows signs of a dangerous fraud or phishing attempt. Do NOT send money or click links.",
                "tips": [
                    "Never pay advance fees for jobs, gifts, or parcel deliveries.",
                    "Banks and police never ask for OTPs or issue arrest warrants on WhatsApp.",
                    f"Report fraud immediately to {CYBERCRIME_HELPLINE}.",
                ],
            },
        },
        "insufficient_info": {
            "explanation": (
                "The provided content contains insufficient legible information to make a confident assessment. "
                "The text is too brief, blurred, or cropped to inspect for authentic headers or red flags."
            ),
            "next_steps": [
                "Please upload a clearer, uncropped screenshot showing the full message and sender details.",
                "Never transfer funds or disclose passwords to unverified contacts.",
                "Confirm requests directly through official, recognized institutional helplines.",
            ],
            "family_alert": {
                "title": "⚠️ Notice: Incomplete or Unclear Message",
                "body": "We could not read enough details from this message to check for fraud markers. Take extra care and do not click unknown links.",
                "tips": [
                    "Ask the sender to verify via an official phone number.",
                    "Do not share passwords or payment details.",
                ],
            },
        },
    },
    "ta": {
        "low_risk": {
            "explanation": (
                "முக்கியமான மோசடி அறிகுறிகள் எதுவும் காணப்படவில்லை. பொதுவான மோசடி வடிவங்கள் எதுவும் இதில் இல்லை. "
                "ஆயினும் நிதி பரிவர்த்தனைகளில் எப்போதும் எச்சரிக்கையாக இருக்கவும்; இது 100% பாதுகாப்பானது என்று பொருள்படாது."
            ),
            "next_steps": [
                "உங்கள் வங்கி செயலியில் நேரடியாக விவரங்களைச் சரிபார்க்கவும்.",
                "ஓடிபி அல்லது பின் எண்களை யாரிடமும் ஒருபோதும் பகிராதீர்கள்.",
                "சந்தேகம் இருந்தால் உங்கள் வங்கி அட்டையின் பின்புறம் உள்ள அதிகாரப்பூர்வ வாடிக்கையாளர் சேவை எண்ணை அழைக்கவும்.",
            ],
            "family_alert": {
                "title": "ℹ️ தகவல்: முக்கியமான மோசடி அறிகுறிகள் இல்லை",
                "body": "இந்த செய்தியில் பொதுவான மோசடி அறிகுறிகள் எதுவும் இல்லை. எனினும் வங்கி கடவுச்சொற்களை யாரிடமும் பகிர வேண்டாம்.",
                "tips": [
                    "வங்கி அதிகாரிகள் ஒருபோதும் ஓடிபி கேட்க மாட்டார்கள்.",
                    "எந்தவொரு இணைப்பிலும் கார்டு விவரங்களை உள்ளிட வேண்டாம்.",
                ],
            },
        },
        "suspicious": {
            "explanation": (
                "இந்த செய்தி சந்தேகத்திற்கிடமான அறிகுறிகளைக் காட்டுகிறது. இதில் அவசரப்படுத்துதல், சரிபார்க்கப்படாத இணைப்புகள், "
                "அல்லது தனிப்பட்ட வாட்ஸ்அப் தொடர்புக்கு அழைப்பது போன்ற எச்சரிக்கைக் குறிகள் உள்ளன. எச்சரிக்கையாக இருக்கவும்."
            ),
            "next_steps": [
                "செய்தியில் உள்ள எந்த இணைப்பையும் கிளிக் செய்ய வேண்டாம்.",
                "நிறுவனத்தின் அதிகாரப்பூர்வ வலைத்தளத்தில் உள்ள வாடிக்கையாளர் சேவை எண்ணை அழைத்து சரிபார்க்கவும்.",
                "பணம் பெற ஒருபோதும் யூபிஐ பின்னை (UPI PIN) உள்ளிட வேண்டாம்.",
                f"மோசடி குறித்து தேசிய இணைய குற்ற உதவி எண் {CYBERCRIME_HELPLINE} அல்லது {CYBERCRIME_PORTAL} இல் புகார் செய்யவும்.",
            ],
            "family_alert": {
                "title": "⚠️ எச்சரிக்கை: சந்தேகத்திற்கிடமான செய்தி",
                "body": "இந்த செய்தியில் மோசடி அறிகுறிகள் உள்ளன. எவ்வித பணமும் அனுப்பாதீர்கள்; இணைப்புகளைத் திறக்காதீர்கள்.",
                "tips": [
                    "இணைப்புகளை கிளிக் செய்யாதீர்கள்.",
                    "அதிகாரப்பூர்வ எண்களை மட்டுமே தொடர்பு கொள்ளவும்.",
                    "பணம் வர பின் எண் போட வேண்டாம்.",
                ],
            },
        },
        "likely_scam": {
            "explanation": (
                "இந்த செய்தி ஆபத்தான மோசடி வடிவங்களின் வலுவான பண்புகளைக் காட்டுகிறது. "
                "முன்பணக் கோரிக்கை, கணக்கு முடக்கப்படும் என்ற மிரட்டல், அல்லது போலி இணைப்புகள் போன்ற தீவிர எச்சரிக்கைகள் இதில் கண்டறியப்பட்டுள்ளன."
            ),
            "next_steps": [
                "எந்தவொரு முன்பணம், பதிவுக் கட்டணம் அல்லது டெபாசிட் தொகையையும் எக்காரணம் கொண்டும் அனுப்ப வேண்டாம்.",
                "உங்கள் ஓடிபி, யூபிஐ பின், அல்லது ஆதார்/பான் விவரங்களை யாரிடமும் பகிராதீர்கள்.",
                "அனுப்பியவரை உடனடியாக பிளாக் செய்யவும்.",
                f"உடனடியாக {CYBERCRIME_HELPLINE} ஐ அழைக்கவும் அல்லது {CYBERCRIME_PORTAL} தளத்தில் புகார் பதிவு செய்யவும்.",
                "பணம் வந்துவிட்டதாகக் கூறினால், உங்கள் வங்கி கணக்கில் நேரடியாக இருப்புத் தொகையைச் சரிபார்க்கவும்.",
            ],
            "family_alert": {
                "title": "🚨 எச்சரிக்கை: மோசடி அபாயம்!",
                "body": "கவனம்! இந்த செய்தி தீவிர மோசடி முயற்சியாகத் தெரிகிறது. எக்காரணம் கொண்டும் பணம் அனுப்பாதீர்கள்.",
                "tips": [
                    "வேலை அல்லது பரிசுக்கு முன்பணம் செலுத்த வேண்டாம்.",
                    "காவல்துறை அல்லது வங்கி வாட்ஸ்அப்பில் கைது வாரண்ட் அனுப்பாது.",
                    f"உதவிக்கு உடனே {CYBERCRIME_HELPLINE} ஐ அழைக்கவும்.",
                ],
            },
        },
        "insufficient_info": {
            "explanation": (
                "பதிவேற்றப்பட்ட படம் அல்லது உரை தெளிவற்றதாக உள்ளது; துல்லியமான மதிப்பீட்டை வழங்க போதுமான விவரங்கள் இல்லை. "
                "படம் மங்கலாகவோ அல்லது வெட்டப்பட்டதாகவோ இருக்கலாம்."
            ),
            "next_steps": [
                "முழு செய்தி மற்றும் அனுப்பியவரின் எண் தெளிவாகத் தெரியும்படி புதிய திரைப்பிடிப்பைப் பதிவேற்றவும்.",
                "தெரியாத நபர்களுக்கு பணம் அல்லது தனிப்பட்ட வங்கி விவரங்களை ஒருபோதும் பகிர வேண்டாம்.",
                "அனுப்பியவரை அதிகாரப்பூர்வ வழியில் சரிபார்க்கவும்.",
            ],
            "family_alert": {
                "title": "⚠️ தகவல்: தெளிவற்ற செய்தி",
                "body": "இந்த செய்தியின் விவரங்கள் தெளிவாக இல்லை. கூடுதல் எச்சரிக்கையுடன் இருக்கவும்; முன்பின் அறியாத இணைப்புகளைத் திறக்காதீர்கள்.",
                "tips": [
                    "அனுப்பியவரை அதிகாரப்பூர்வ வழியில் சரிபார்க்கவும்.",
                    "ஓடிபி அல்லது கடவுச்சொற்களை யாரிடமும் பகிர வேண்டாம்.",
                ],
            },
        },
    },
    "hi": {
        "low_risk": {
            "explanation": (
                "कोई प्रमुख संदिग्ध संकेत नहीं मिले। इस संदेश में कोई सामान्य धोखाधड़ी पैटर्न या अवैध अनुरोध नहीं पाया गया। "
                "फिर भी सतर्क रहें; इसका यह अर्थ नहीं है कि यह संदेश पूरी तरह सुरक्षित या सत्यापित है।"
            ),
            "next_steps": [
                "अपने आधिकारिक बैंकिंग ऐप में जाकर सीधे विवरण की जांच करें।",
                "किसी के भी साथ अपना ओटीपी या नेटबैंकिंग पासवर्ड साझा न करें।",
                "संदेह होने पर बैंक के आधिकारिक टोल-फ्री नंबर पर कॉल करें।",
            ],
            "family_alert": {
                "title": "ℹ️ सूचना: कोई प्रमुख संदिग्ध संकेत नहीं",
                "body": "इस संदेश में कोई सामान्य धोखाधड़ी के संकेत नहीं मिले हैं। फिर भी किसी से अपना पासवर्ड साझा न करें।",
                "tips": [
                    "बैंक कभी भी आपका पासवर्ड या ओटीपी नहीं मांगते हैं।",
                    "पैसे भेजने से पहले हमेशा दोबारा पुष्टि करें।",
                ],
            },
        },
        "suspicious": {
            "explanation": (
                "यह संदेश संदिग्ध गतिविधि के लक्षण दिखाता है। इसमें गैर-जरूरी जल्दबाजी, असत्यापित लिंक, या "
                "टेलीग्राम/व्हाट्सएप पर संपर्क करने के निर्देश जैसे लाल झंडे पाए गए हैं। अत्यधिक सावधानी बरतें।"
            ),
            "next_steps": [
                "संदेश में दिए गए किसी भी लिंक पर क्लिक न करें।",
                "संबंधित कंपनी के आधिकारिक पोर्टल से नंबर लेकर स्वतंत्र रूप से पुष्टि करें।",
                "पैसे प्राप्त करने के लिए कभी भी अपना यूपीआई पिन दर्ज न करें।",
                f"संदिग्ध धोखाधड़ी की सूचना राष्ट्रीय साइबर अपराध हेल्पलाइन {CYBERCRIME_HELPLINE} या {CYBERCRIME_PORTAL} पर दें।",
            ],
            "family_alert": {
                "title": "⚠️ सावधानी: संदिग्ध संदेश मिला",
                "body": "इस संदेश में संभावित धोखाधड़ी के लक्षण हैं। कोई लिंक न खोलें और पैसे ट्रांसफर न करें।",
                "tips": [
                    "अज्ञात लिंक पर क्लिक न करें।",
                    "कंपनी के आधिकारिक हेल्पलाइन नंबर पर कॉल करके पुष्टि करें।",
                    "पैसे पाने के लिए कभी पिन न डालें।",
                ],
            },
        },
        "likely_scam": {
            "explanation": (
                "यह संदेश धोखाधड़ी या घोटाले की मजबूत विशेषताएं दिखाता है। इसमें अग्रिम पैसे की मांग, "
                "खाता बंद करने की धमकी, या नकली लिंक जैसे उच्च जोखिम वाले कई लाल झंडे पाए गए हैं।"
            ),
            "next_steps": [
                "किसी भी स्थिति में कोई पंजीकरण शुल्क, सुरक्षा जमा या अग्रिम राशि न भेजें।",
                "अपना ओटीपी, यूपीआई पिन, नेटबैंकिंग पासवर्ड या आधार/पैन विवरण कभी साझा न करें।",
                "भेजने वाले को तुरंत ब्लॉक करें और रिपोर्ट करें।",
                f"इस घटना की तुरंत {CYBERCRIME_PORTAL} पर रिपोर्ट करें या {CYBERCRIME_HELPLINE} पर कॉल करें।",
                "यदि भुगतान रसीद दिखाई गई है, तो सीधे अपने बैंक ऐप में खाता शेष की पुष्टि करें।",
            ],
            "family_alert": {
                "title": "🚨 चेतावनी: गंभीर धोखाधड़ी का खतरा!",
                "body": "सावधान रहें! यह संदेश एक खतरनाक फर्जीवाड़े का संकेत देता है। कोई पैसा न भेजें और न ही कोई विवरण साझा करें।",
                "tips": [
                    "नौकरी या लॉटरी के नाम पर कभी अग्रिम शुल्क न दें।",
                    "पुलिस या बैंक कभी व्हाट्सएप पर डिजिटल अरेस्ट या वारंट जारी नहीं करते।",
                    f"मदद के लिए तुरंत {CYBERCRIME_HELPLINE} पर कॉल करें।",
                ],
            },
        },
        "insufficient_info": {
            "explanation": (
                "अपलोड किया गया स्क्रीनशॉट या टेक्स्ट बहुत संक्षिप्त या अस्पष्ट है। "
                "सटीक धोखाधड़ी मूल्यांकन के लिए पर्याप्त जानकारी उपलब्ध नहीं है।"
            ),
            "next_steps": [
                "कृपया पूरा संदेश और भेजने वाले का विवरण दिखाने वाला स्पष्ट स्क्रीनशॉट अपलोड करें।",
                "अज्ञात संदेशों पर पैसे या ओटीपी कभी भी साझा न करें।",
                "संबंधित संस्थान से आधिकारिक नंबर पर संपर्क करके पुष्टि करें।",
            ],
            "family_alert": {
                "title": "⚠️ सूचना: अपूर्ण या अस्पष्ट संदेश",
                "body": "इस संदेश से धोखाधड़ी की पुष्टि के लिए पर्याप्त जानकारी नहीं मिल पाई है। किसी भी अज्ञात लिंक पर क्लिक न करें।",
                "tips": [
                    "आधिकारिक नंबर से कॉल करके ही पुष्टि करें।",
                    "किसी के साथ बैंक पासवर्ड या पिन साझा न करें।",
                ],
            },
        },
    },
}


# ------------------------------------------------------------------------------
# Safety Post-Check Validator
# ------------------------------------------------------------------------------
def validate_explanation_safety(
    explanation: str,
    band: BandType,
    scam_type: Optional[str],
    next_steps: List[str],
) -> Tuple[bool, str]:
    """
    Enforces mandatory safety rules on generated explanations:
    1. Must use cautious language ('shows signs of', 'may be', 'we found red flags').
       NEVER 'is definitely a scam', '100% fake', or 'guaranteed fraud'.
    2. Lowest band (low_risk) must state 'no major red flags found' and NEVER say 'safe' or 'verified genuine'.
    3. For fake_payment, must advise checking user's own bank app/account directly.
    4. Next steps must recommend verification via official portal/number.
    """
    exp_lower = explanation.lower()

    # Rule 1: No absolutes in scam declaration
    forbidden_absolutes = ["definitely a scam", "100% fake", "guaranteed fraud", "is definitely fake"]
    for phrase in forbidden_absolutes:
        if phrase in exp_lower:
            return False, f"Forbidden absolute declaration: '{phrase}'"

    # Rule 2: No absolutes in low_risk (must never say 'safe' or 'verified genuine')
    if band == "low_risk":
        forbidden_safe = ["this is safe", "is completely safe", "verified genuine", "100% safe", "guaranteed safe"]
        for phrase in forbidden_safe:
            if phrase in exp_lower:
                return False, f"Forbidden safe declaration in low_risk: '{phrase}'"

    # Rule 3: For fake_payment, ensure checking own bank app is advised
    combined_steps = " ".join(next_steps).lower()
    if scam_type == "fake_payment":
        payment_check_phrases = ["bank app", "bank account", "account balance", "own bank", "banking app"]
        if not any(p in combined_steps or p in exp_lower for p in payment_check_phrases):
            return False, "Missing bank app balance verification advice for payment transaction"

    # Rule 4: Verification via official channel
    official_check_phrases = ["official", "helpline", "website", "1930", "cybercrime", "branch"]
    if not any(p in combined_steps for p in official_check_phrases):
        return False, "Missing recommendation for official verification channel"

    return True, "Passed safety checks"


# ------------------------------------------------------------------------------
# Explainer Generation Prompt & LLM Caller
# ------------------------------------------------------------------------------
def build_explainer_prompt(
    band: BandType,
    score: int,
    scam_type: Optional[str],
    signals: List[Signal],
    tool_results: List[ToolResult],
    language: LanguageType,
) -> str:
    """Builds prompt containing ONLY structured findings (never raw images)."""
    lang_name = {"en": "English", "ta": "Tamil", "hi": "Hindi"}.get(language, "English")

    signals_summary = []
    for s in signals:
        signals_summary.append(f"- [{s.category.upper()}] {s.label} (+{s.weight}): \"{s.evidence}\" (source: {s.source})")

    tools_summary = []
    for tr in tool_results:
        tools_summary.append(f"- {tr.tool} [{tr.status}]: {tr.target} -> {tr.detail}")

    prompt = f"""You are ScamLens Explainer, an AI safety assistant.
Explain the following analysis results in clear, helpful {lang_name}.

CRITICAL SAFETY RULES:
1. Use cautious, non-absolving language: say "shows signs of", "may be", "contains red flags". NEVER declare "is definitely a scam" or "100% fake".
2. If band is low_risk, explain that "no major red flags found", but NEVER declare it is "safe" or "verified genuine". Remind user to remain vigilant.
3. If scam_type is fake_payment, you MUST include advice to "Always check your own bank account/app to confirm funds arrived."
4. Next steps MUST include verifying through official portals/numbers or National Cybercrime Helpline 1930.
5. Return ONLY a valid JSON object matching this schema:
{{
  "explanation": "2-4 sentences explaining why the message was flagged, quoting the evidence verbatim.",
  "next_steps": [
    "3-4 concrete actionable steps for the user"
  ],
  "family_alert": {{
    "title": "Short title with emoji (e.g. ⚠️ Caution: ...)",
    "body": "Simple conversational summary suitable to forward on WhatsApp family groups.",
    "tips": ["2-3 bullet tips"]
  }}
}}

ANALYSIS INPUT:
- Calibrated Band: {band}
- Risk Score: {score}/100
- Detected Scam Type: {scam_type or 'None'}
- Fired Red Flags:
{chr(10).join(signals_summary) if signals_summary else 'None detected'}
- External Verifier Checks:
{chr(10).join(tools_summary) if tools_summary else 'None performed'}
"""
    return prompt


async def generate_explanation_with_model(
    band: BandType,
    score: int,
    scam_type: Optional[str],
    signals: List[Signal],
    tool_results: List[ToolResult],
    language: LanguageType,
    model_client: ModelClient,
) -> Optional[Tuple[str, List[str], FamilyAlert]]:
    """Invokes ModelClient and performs safety validation with up to 1 retry."""
    prompt = build_explainer_prompt(band, score, scam_type, signals, tool_results, language)

    for attempt in range(2):
        try:
            raw_response = await model_client.generate(prompt=prompt, json_mode=True, temperature=0.0)
            clean_json = raw_response.strip()
            if clean_json.startswith("```"):
                clean_json = re.sub(r"^```(?:json)?\s*", "", clean_json)
                clean_json = re.sub(r"\s*```$", "", clean_json)

            data = json.loads(clean_json)
            explanation = data.get("explanation", "").strip()
            next_steps = [s.strip() for s in data.get("next_steps", []) if s.strip()]
            alert_dict = data.get("family_alert", {})
            family_alert = FamilyAlert(
                title=alert_dict.get("title", "⚠️ Family Alert"),
                body=alert_dict.get("body", "Stay cautious."),
                tips=alert_dict.get("tips", []),
            )

            is_safe, reason = validate_explanation_safety(explanation, band, scam_type, next_steps)
            if is_safe:
                return explanation, next_steps, family_alert
            else:
                logger.warning(f"Safety check failed on attempt {attempt+1}: {reason}")
        except Exception as e:
            logger.warning(f"LLM explanation generation error on attempt {attempt+1}: {e}")

    return None


# ------------------------------------------------------------------------------
# Main Explainer Entrypoint
# ------------------------------------------------------------------------------
async def hook_explain(
    band: BandType,
    score: int,
    signals: List[Signal],
    tool_results: List[ToolResult],
    language: LanguageType = "en",
    mode: str = "mock",
    scam_type: Optional[str] = None,
    model_client: Optional[ModelClient] = None,
) -> Tuple[str, List[str], FamilyAlert]:
    """
    Generates explanation, next steps, and Family Alert card.
    Uses LLM with safety post-validation in cloud/local mode, or resilient static templates.
    """
    lang = language if language in ("en", "ta", "hi") else "en"

    # In cloud or local mode, attempt LLM explanation first
    if mode in ("cloud", "local") and band != "insufficient_info":
        client = model_client or get_model_client(mode=mode)
        llm_result = await generate_explanation_with_model(
            band=band,
            score=score,
            scam_type=scam_type,
            signals=signals,
            tool_results=tool_results,
            language=lang,
            model_client=client,
        )
        if llm_result:
            return llm_result

    # Fallback to high-quality deterministic multilingual templates
    template_pack = FALLBACK_TEMPLATES.get(lang, FALLBACK_TEMPLATES["en"])
    band_template = template_pack.get(band, template_pack["low_risk"])

    explanation = band_template["explanation"]

    # If signals are present, enrich the template explanation with verbatim quotes
    if signals and band in ("suspicious", "likely_scam"):
        quoted_flags = [f'"{s.evidence}"' for s in signals[:3] if s.evidence]
        if quoted_flags:
            if lang == "ta":
                explanation += f" கண்டறியப்பட்ட ஆதாரங்கள்: {', '.join(quoted_flags)}."
            elif lang == "hi":
                explanation += f" पाए गए संदिग्ध अंश: {', '.join(quoted_flags)}."
            else:
                explanation += f" Detected red flags include: {', '.join(quoted_flags)}."

    next_steps = list(band_template["next_steps"])

    # If scam_type is fake_payment, ensure bank app verification is always in next_steps
    if scam_type == "fake_payment":
        payment_step = {
            "en": "Always verify funds arrival directly in your own mobile banking app or SMS from your bank.",
            "ta": "உங்கள் வங்கி கணக்கிற்கு பணம் வந்துவிட்டதா என்பதை உங்கள் வங்கி செயலியில் நேரடியாகச் சரிபார்க்கவும்.",
            "hi": "हमेशा अपने आधिकारिक मोबाइल बैंकिंग ऐप में सीधे जाकर खाते में पैसे आने की पुष्टि करें।",
        }[lang]
        if not any("banking app" in s.lower() or "வங்கி செயலி" in s or "बैंकिंग ऐप" in s for s in next_steps):
            next_steps.insert(0, payment_step)

    alert_data = band_template["family_alert"]
    family_alert = FamilyAlert(
        title=alert_data["title"],
        body=alert_data["body"],
        tips=list(alert_data["tips"]),
    )

    return explanation, next_steps, family_alert
