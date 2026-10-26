import uuid
from typing import Optional
from app.schemas import AnalyzeResponse, ExtractedData, FamilyAlert, Signal, ToolResult


MOCK_SCENARIOS = {
    "internship": {
        "band": "likely_scam",
        "score": 85,
        "confidence": "high",
        "scam_type": "fake_internship_fee",
        "extracted": {
            "document_type": "offer_letter",
            "sender": "careers-google@tech-hiring-portal.org",
            "message_text": "Congratulations! You have been selected for a Virtual Internship. Please deposit a refundable security fee of Rs. 1500 to UPI ID techcareers@okaxis within 24 hours to secure your seat.",
            "urls": ["http://tech-hiring-portal.org/offer-accept"],
            "phone_numbers": ["+919876543210"],
            "upi_ids": ["techcareers@okaxis"],
            "amounts": ["Rs. 1500"],
            "claimed_brand": "Google",
            "detected_language": "en",
            "image_quality": "sharp",
        },
        "signals": [
            {
                "id": "MONEY_ADVANCE_FEE",
                "label": "Advance Security Fee Demanded",
                "category": "money_demands",
                "weight": 40.0,
                "evidence": "refundable security fee of Rs. 1500",
                "source": "rule",
            },
            {
                "id": "URGENCY_DEADLINE_24H",
                "label": "Artificial Urgency Deadline",
                "category": "urgency_threat",
                "weight": 25.0,
                "evidence": "within 24 hours to secure your seat",
                "source": "rule",
            },
            {
                "id": "SENDER_DOMAIN_MISMATCH",
                "label": "Unofficial Sender Domain",
                "category": "impersonation",
                "weight": 20.0,
                "evidence": "tech-hiring-portal.org claiming to represent Google",
                "source": "tool",
            },
        ],
        "tool_results": [
            {
                "tool": "domain_verifier",
                "target": "tech-hiring-portal.org",
                "status": "warn",
                "detail": "Domain registered 4 days ago. Not associated with Google LLC.",
            },
            {
                "tool": "upi_verifier",
                "target": "techcareers@okaxis",
                "status": "warn",
                "detail": "Individual VPA format used instead of registered corporate merchant.",
            },
        ],
        "i18n": {
            "en": {
                "explanation": "This offer letter shows strong signs of an internship recruitment scam. Legitimate employers never require applicants to pay a 'refundable security fee' or deposit money via UPI to confirm an offer. Furthermore, the sender domain (tech-hiring-portal.org) is not affiliated with Google.",
                "next_steps": [
                    "Do NOT transfer any money or pay the requested Rs. 1500 via UPI.",
                    "Do not share your Aadhaar, bank details, or personal ID documents.",
                    "Verify genuine vacancies directly on the official careers page at careers.google.com.",
                    "Report this fraudulent incident to the National Cybercrime Portal at cybercrime.gov.in or dial 1930.",
                ],
                "family_alert": {
                    "title": "⚠️ Caution: Fake Internship / Job Deposit Alert",
                    "body": "If anyone sends you a job or internship offer asking for an upfront registration or equipment fee via UPI, DO NOT PAY. Genuine companies never charge candidates money to start work.",
                    "tips": [
                        "Never pay money to get a job or internship.",
                        "Check the company email address carefully (@company.com).",
                        "Discuss with a family member before transferring funds.",
                    ],
                },
            },
            "ta": {
                "explanation": "இந்த சலுகைக் கடிதம் போலி வேலைவாய்ப்பு மோசடியின் வலுவான அறிகுறிகளைக் காட்டுகிறது. உண்மையான நிறுவனங்கள் ஒருபோதும் வேலையை உறுதிப்படுத்த 'திரும்பப்பெறக்கூடிய பாதுகாப்பு வைப்புத்தொகை' அல்லது UPI மூலம் பணம் செலுத்துமாறு கேட்காது. மேலும் அனுப்பிய இணைய முகவரி கூகுளுடன் தொடர்புடையது அல்ல.",
                "next_steps": [
                    "கோரப்பட்ட ரூ. 1500 தொகையை UPI அல்லது வேறு எந்த வழியிலும் செலுத்த வேண்டாம்.",
                    "உங்கள் ஆதார் அட்டை, வங்கி விவரங்கள் அல்லது தனிப்பட்ட ஆவணங்களைப் பகிர வேண்டாம்.",
                    "உண்மையான வேலை வாய்ப்புகளை அதிகாரப்பூர்வ இணையதளத்தில் (careers.google.com) மட்டுமே சரிபார்க்கவும்.",
                    "இத்தகைய இணைய மோசடிகளை 1930 என்ற உதவி எண்ணில் அல்லது cybercrime.gov.in தளத்தில் புகார் அளிக்கவும்.",
                ],
                "family_alert": {
                    "title": "⚠️ எச்சரிக்கை: போலி வேலைவாய்ப்பு முன்வைப்புத் தொகை மோசடி",
                    "body": "வேலை அல்லது இன்டர்ன்ஷிப் தருவதாகக் கூறி யாராவது முன்கூட்டியே UPI மூலம் பணம் கேட்டால் ஒருபோதும் செலுத்தாதீர்கள். உண்மையான நிறுவனங்கள் வேலை தருவதற்கு பணம் வாங்குவதில்லை.",
                    "tips": [
                        "வேலைக்காக யாரிடமும் பணம் கொடுக்க வேண்டாம்.",
                        "நிறுவனத்தின் மின்னஞ்சல் முகவரியைக் கவனமாகச் சரிபார்க்கவும்.",
                        "பணம் அனுப்பும் முன் குடும்பத்தினரிடம் கலந்தாலோசிக்கவும்.",
                    ],
                },
            },
            "hi": {
                "explanation": "यह प्रस्ताव पत्र फर्जी इंटर्नशिप भर्ती घोटाले के स्पष्ट संकेत दिखाता है। कोई भी वास्तविक कंपनी नौकरी या इंटर्नशिप की पुष्टि के लिए कभी भी 'रिफंडेबल सिक्योरिटी फीस' या UPI द्वारा पैसे नहीं मांगती है। इसके अलावा, भेजने वाला ईमेल डोमेन गूगल से संबद्ध नहीं है।",
                "next_steps": [
                    "मांगी गई 1500 रुपये की राशि किसी भी UPI माध्यम से बिल्कुल न भेजें।",
                    "अपना आधार कार्ड, बैंक विवरण या अन्य पहचान पत्र साझा न करें।",
                    "असली नौकरियों की जांच सीधे careers.google.com जैसी आधिकारिक वेबसाइट पर करें।",
                    "साइबर धोखाधड़ी की शिकायत राष्ट्रीय पोर्टल cybercrime.gov.in या हेल्पलाइन 1930 पर दर्ज करें।",
                ],
                "family_alert": {
                    "title": "⚠️ चेतावनी: फर्जी इंटर्नशिप व नौकरी फीस का अलर्ट",
                    "body": "यदि कोई नौकरी या इंटर्नशिप के नाम पर आपसे पहले UPI द्वारा पैसे या सिक्योरिटी डिपॉजिट मांगता है, तो बिल्कुल न दें। असली कंपनियां नौकरी देने के लिए कभी पैसे नहीं लेती हैं।",
                    "tips": [
                        "नौकरी पाने के लिए कभी किसी को पैसे न दें।",
                        "कंपनी के आधिकारिक ईमेल पते की ध्यानपूर्वक जांच करें।",
                        "पैसे भेजने से पहले परिवार के किसी सदस्य से अवश्य बात करें।",
                    ],
                },
            },
        },
    },
    "courier": {
        "band": "suspicious",
        "score": 45,
        "confidence": "medium",
        "scam_type": "courier_delivery_scam",
        "extracted": {
            "document_type": "sms_notification",
            "sender": "+919123456789",
            "message_text": "India Post Alert: Your parcel #IN892348 is stopped at sorting hub due to incorrect delivery address. Update your address within 12 hours at http://indiapost-parcel-update.top to prevent return.",
            "urls": ["http://indiapost-parcel-update.top"],
            "phone_numbers": ["+919123456789"],
            "upi_ids": [],
            "amounts": [],
            "claimed_brand": "India Post",
            "detected_language": "en",
            "image_quality": "sharp",
        },
        "signals": [
            {
                "id": "LINK_TYPOSQUATTING",
                "label": "Unofficial Courier Domain",
                "category": "links",
                "weight": 30.0,
                "evidence": "indiapost-parcel-update.top is not official indiapost.gov.in",
                "source": "tool",
            },
            {
                "id": "URGENCY_DEADLINE_12H",
                "label": "Short Time Window Urgency",
                "category": "urgency_threat",
                "weight": 15.0,
                "evidence": "Update your address within 12 hours",
                "source": "rule",
            },
        ],
        "tool_results": [
            {
                "tool": "domain_verifier",
                "target": "indiapost-parcel-update.top",
                "status": "warn",
                "detail": "Domain registered 2 days ago using suspicious .top TLD.",
            },
        ],
        "i18n": {
            "en": {
                "explanation": "This message exhibits patterns of a courier phishing delivery scam. India Post notifications never arrive from standard 10-digit mobile numbers, and official government portals always use the .gov.in domain, never third-party .top domains.",
                "next_steps": [
                    "Do NOT click on the link in the message.",
                    "Track any real postal consignments only via the official portal at indiapost.gov.in.",
                    "Do not enter your credit/debit card or banking credentials on external forms.",
                    "Report deceptive SMS messages to Sanchar Saathi (Chakshu facility) at sancharsaathi.gov.in.",
                ],
                "family_alert": {
                    "title": "⚠️ Caution: Fake Parcel Delivery Link Alert",
                    "body": "Scammers are sending SMS messages claiming your parcel is stuck and asking you to update your address on a link. Government courier services only use .gov.in websites.",
                    "tips": [
                        "Never click links in delivery SMS messages from 10-digit phone numbers.",
                        "Track parcels directly on official apps or indiapost.gov.in.",
                        "Do not pay even small amounts (like Rs 5 or Rs 10) to update addresses.",
                    ],
                },
            },
            "ta": {
                "explanation": "இந்த செய்தி கூரியர் பார்சல் ஃபிஷிங் மோசடியின் தன்மைகளைக் கொண்டுள்ளது. இந்தியா போஸ்ட் ஒருபோதும் 10 இலக்க மொபைல் எண்ணிலிருந்து குறுஞ்செய்தி அனுப்பாது. மேலும் அரசு இணையதளங்கள் .gov.in என்றே முடியும்; .top போன்ற முகவரிகளைப் பயன்படுத்தாது.",
                "next_steps": [
                    "செய்தியில் உள்ள இணைப்பை ஒருபோதும் கிளிக் செய்யாதீர்கள்.",
                    "உங்கள் பார்சலை indiapost.gov.in என்ற அதிகாரப்பூர்வ இணையதளத்தில் மட்டுமே கண்காணிக்கவும்.",
                    "எந்தவொரு இணைய இணைப்பிலும் உங்கள் வங்கி அல்லது கார்டு விவரங்களை உள்ளிட வேண்டாம்.",
                    "மோசடி குறுஞ்செய்திகளை sancharsaathi.gov.in தளத்தின் சக்ஷு (Chakshu) பிரிவில் புகாரளிக்கவும்.",
                ],
                "family_alert": {
                    "title": "⚠️ எச்சரிக்கை: போலி தபால் பார்சல் இணைப்பு மோசடி",
                    "body": "உங்கள் பார்சல் நிறுத்தி வைக்கப்பட்டுள்ளது என்றும், இணைப்பைத் திறந்து முகவரியைப் புதுப்பிக்கவும் கூறி வரும் குறுஞ்செய்திகளை நம்பாதீர்கள். அது உங்கள் வங்கிப் பணத்தைத் திருடும் மோசடியாகும்.",
                    "tips": [
                        "சாதாரண மொபைல் எண்களிலிருந்து வரும் கூரியர் இணைப்புகளைக் கிளிக் செய்யாதீர்கள்.",
                        "அரசு தபால் சேவைகள் .gov.in என்ற முகவரியை மட்டுமே பயன்படுத்தும்.",
                        "முகவரி மாற்ற சிறிய தொகையை கூட (ரூ. 5) செலுத்த வேண்டாம்.",
                    ],
                },
            },
            "hi": {
                "explanation": "यह संदेश कूरियर डिलीवरी फ़िशिंग घोटाले के लक्षण दिखाता है। भारतीय डाक कभी भी व्यक्तिगत 10-अंकों के मोबाइल नंबर से एसएमएस नहीं भेजता है, और सरकारी पोर्टल हमेशा .gov.in डोमेन का उपयोग करते हैं, न कि .top जैसे संदेहास्पद डोमेन का।",
                "next_steps": [
                    "संदेश में दिए गए लिंक पर बिल्कुल क्लिक न करें।",
                    "पार्सल की वास्तविक स्थिति केवल indiapost.gov.in पर ही ट्रैक करें।",
                    "किसी अज्ञात लिंक पर अपने बैंक कार्ड या ओटीपी की जानकारी न भरें।",
                    "संदिग्ध एसएमएस की शिकायत संचार साथी (चक्षु) पोर्टल sancharsaathi.gov.in पर करें।",
                ],
                "family_alert": {
                    "title": "⚠️ चेतावनी: फर्जी पार्सल डिलीवरी लिंक से सावधान",
                    "body": "पार्सल रुकने और पता अपडेट करने के नाम पर आने वाले लिंक से सावधान रहें। सरकारी डाक सेवा कभी भी निजी मोबाइल नंबर से लिंक नहीं भेजती है।",
                    "tips": [
                        "10-अंकों के नंबर से आए डिलीवरी लिंक पर क्लिक न करें।",
                        "सरकारी डाक की आधिकारिक वेबसाइट indiapost.gov.in ही है।",
                        "पता बदलने के नाम पर ₹5 या ₹10 भी ऑनलाइन न भरें।",
                    ],
                },
            },
        },
    },
    "bank_alert": {
        "band": "low_risk",
        "score": 10,
        "confidence": "high",
        "scam_type": None,
        "extracted": {
            "document_type": "transactional_sms",
            "sender": "VK-HDFCBK",
            "message_text": "A/c *1234 debited by INR 450.00 on 26-OCT-26 at SWIGGY BANGALORE. UPI Ref 429812984123. If not done by you, forward this SMS to 9223008333 or call 18001600.",
            "urls": [],
            "phone_numbers": ["9223008333", "18001600"],
            "upi_ids": [],
            "amounts": ["INR 450.00"],
            "claimed_brand": "HDFC Bank",
            "detected_language": "en",
            "image_quality": "sharp",
        },
        "signals": [
            {
                "id": "REDUCER_STANDARD_DEBIT_ALERT",
                "label": "Standard Masked Debit Notification",
                "category": "reducers",
                "weight": -20.0,
                "evidence": "A/c *1234 debited by INR 450.00",
                "source": "rule",
            },
            {
                "id": "REDUCER_NO_HYPERLINKS",
                "label": "Absence of Suspicious Hyperlinks",
                "category": "reducers",
                "weight": -10.0,
                "evidence": "No external URLs present in message",
                "source": "rule",
            },
        ],
        "tool_results": [
            {
                "tool": "sender_verifier",
                "target": "VK-HDFCBK",
                "status": "ok",
                "detail": "Sender header matches registered DLT banking header for HDFC Bank.",
            },
        ],
        "i18n": {
            "en": {
                "explanation": "No major red flags found. This message matches standard transactional debit notifications sent by licensed banks in India. It includes a masked account number (*1234), a legitimate UTR reference number, official toll-free helpline numbers, and no suspicious external hyperlinks.",
                "next_steps": [
                    "Verify your transaction history inside your official mobile banking app.",
                    "If you did not authorize this payment of INR 450.00, immediately contact the bank via the official number on the back of your debit card.",
                    "Never share your debit card PIN, CVV, or OTP with anyone calling you.",
                ],
                "family_alert": {
                    "title": "ℹ️ Notice: Standard Bank Transaction Alert",
                    "body": "This appears to be a normal bank debit notification. As a standard safety practice, never share OTPs or banking PINs with anyone, even if they claim to call from your bank.",
                    "tips": [
                        "Banks will never ask for your NetBanking password, OTP, or UPI PIN.",
                        "Always call the number on the back of your card for banking help.",
                    ],
                },
            },
            "ta": {
                "explanation": "முக்கியமான மோசடி அறிகுறிகள் எதுவும் காணப்படவில்லை. இந்த செய்தி இந்தியாவின் அங்கீகரிக்கப்பட்ட வங்கியால் அனுப்பப்படும் வழக்கமான பரிவர்த்தனை குறுஞ்செய்தியைப் போன்றே உள்ளது. இதில் மறைக்கப்பட்ட கணக்கு எண் (*1234), முறையான UTR எண் மற்றும் அதிகாரப்பூர்வ உதவி எண்கள் உள்ளன; சந்தேகத்திற்கிடமான இணைப்புகள் எதுவும் இல்லை.",
                "next_steps": [
                    "உங்கள் அதிகாரப்பூர்வ வங்கி செயலியில் பரிவர்த்தனை வரலாற்றைச் சரிபார்க்கவும்.",
                    "இந்த INR 450.00 பரிவர்த்தனையை நீங்கள் செய்யவில்லை என்றால், உடனடியாக உங்கள் ஏடிஎம் கார்டின் பின்புறம் உள்ள வங்கி எண்ணைத் தொடர்புகொள்ளவும்.",
                    "உங்கள் ஏடிஎம் பின், சிவிவி அல்லது ஓடிபியை யாரிடமும் ஒருபோதும் பகிர வேண்டாம்.",
                ],
                "family_alert": {
                    "title": "ℹ️ தகவல்: வழக்கமான வங்கி பரிவர்த்தனை அறிவிப்பு",
                    "body": "இது ஒரு வழக்கமான வங்கி பரிவர்த்தனை அறிவிப்பாகத் தெரிகிறது. பாதுகாப்பிற்காக உங்கள் ஓடிபி அல்லது வங்கி கடவுச்சொற்களை யாரிடமும் பகிராதீர்கள்.",
                    "tips": [
                        "வங்கி அதிகாரிகள் ஒருபோதும் ஓடிபி அல்லது பின் கேட்க மாட்டார்கள்.",
                        "உதவிக்கு உங்கள் ஏடிஎம் கார்டின் பின்னால் உள்ள எண்ணை மட்டுமே அழைக்கவும்.",
                    ],
                },
            },
            "hi": {
                "explanation": "कोई प्रमुख संदिग्ध संकेत नहीं मिले। यह संदेश भारत के पंजीकृत बैंक द्वारा भेजे जाने वाले सामान्य डेबिट अलर्ट के समान है। इसमें आंशिक खाता संख्या (*1234), वैध यूटीआर नंबर और आधिकारिक टोल-फ्री हेल्पलाइन नंबर शामिल हैं, और कोई संदेहास्पद लिंक नहीं है।",
                "next_steps": [
                    "अपने आधिकारिक मोबाइल बैंकिंग ऐप में लेन-देन के इतिहास की पुष्टि करें।",
                    "यदि आपने यह ₹450.00 का भुगतान नहीं किया है, तो अपने डेबिट कार्ड के पीछे दिए गए आधिकारिक नंबर पर बैंक से तुरंत संपर्क करें।",
                    "अपना एटीएम पिन, सीवीवी या ओटीपी फोन करने वाले किसी भी व्यक्ति के साथ साझा न करें।",
                ],
                "family_alert": {
                    "title": "ℹ️ सूचना: सामान्य बैंक लेन-देन सूचना",
                    "body": "यह एक सामान्य बैंक लेन-देन संदेश प्रतीत होता है। सुरक्षा के तौर पर कभी भी किसी के साथ अपना ओटीपी या बैंक पिन साझा न करें।",
                    "tips": [
                        "बैंक कभी भी आपका नेटबैंकिंग पासवर्ड या ओटीपी नहीं मांगते हैं।",
                        "सहायता के लिए हमेशा अपने डेबिट कार्ड के पीछे दिए गए नंबर पर ही कॉल करें।",
                    ],
                },
            },
        },
    },
    "payment": {
        "band": "suspicious",
        "score": 55,
        "confidence": "high",
        "scam_type": "fake_payment_screenshot",
        "extracted": {
            "document_type": "payment_screenshot",
            "sender": "Rahul Verma",
            "message_text": "Paid Successfully ₹ 12,500.00 to Dharshika S dharshika@okaxis. UPI Ref No: 429910482910. Payment Note: Advance laptop fee sent. Dispatch courier immediately within 1 hour or legal police complaint will be filed.",
            "urls": [],
            "phone_numbers": [],
            "upi_ids": ["dharshika@okaxis"],
            "amounts": ["₹ 12,500.00", "₹500"],
            "claimed_brand": "Paytm / UPI",
            "detected_language": "en",
            "image_quality": "sharp",
            "visual_notes": [
                "Mismatched font weight on amount field",
                "Urgent coercive payment note",
                "Unverified transaction status"
            ],
        },
        "signals": [
            {
                "id": "PAYMENT_COERCIVE_NOTE",
                "label": "Coercive Police Threat in Payment Note",
                "category": "urgency_threat",
                "weight": 35.0,
                "evidence": "Dispatch courier immediately within 1 hour or legal police complaint will be filed",
                "source": "rule",
            },
            {
                "id": "PAYMENT_SCREENSHOT_INCONSISTENCY",
                "label": "Visual Font Irregularity in Amount",
                "category": "payment_screenshot",
                "weight": 20.0,
                "evidence": "Mismatched font kerning and weight in amount field",
                "source": "rule",
            },
        ],
        "tool_results": [
            {
                "tool": "upi_verifier",
                "target": "dharshika@okaxis",
                "status": "ok",
                "detail": "Valid VPA format.",
            },
        ],
        "i18n": {
            "en": {
                "explanation": "This payment screenshot exhibits high risk of digital tampering. A screenshot alone cannot prove a genuine transfer, as fake receipt generator apps and edited images are common. The threat of police action within 1 hour is a classic psychological pressure tactic.",
                "next_steps": [
                    "A screenshot cannot prove a payment. Confirm in your bank app or official bank SMS.",
                    "Do NOT dispatch any goods or courier parcels until money is reflected in your bank account.",
                    "Do not engage with coercive threats of police complaints.",
                    "If pressured, block the sender and file an inquiry on cybercrime.gov.in or call 1930.",
                ],
                "family_alert": {
                    "title": "⚠️ Caution: Fake Payment Screenshot Scam",
                    "body": "Never trust an image or screenshot as proof of money transfer. Scammers use fake receipt maker apps. Always check your actual bank account balance directly.",
                    "tips": [
                        "Screenshots are not proof of payment.",
                        "Check your own bank app balance directly.",
                        "Ignore threats of fake police complaints.",
                    ],
                },
            },
            "ta": {
                "explanation": "இந்த கட்டண ஸ்கிரீன்ஷாட் திருத்தப்பட்டிருக்க அதிக வாய்ப்புள்ளது. ஸ்கிரீன்ஷாட் மட்டும் பணம் வந்ததற்கான ஆதாரமாகாது. 1 மணி நேரத்திற்குள் கூரியர் அனுப்பாவிட்டால் போலீசில் புகார் தருவேன் என மிரட்டுவது வழக்கமான மோசடி உத்தி.",
                "next_steps": [
                    "ஒரு ஸ்கிரீன்ஷாட் பணப் பரிவர்த்தனையை நிரூபிக்காது. உங்கள் வங்கி செயலி அல்லது அதிகாரப்பூர்வ எஸ்எம்எஸ் மூலம் உறுதிப்படுத்தவும்.",
                    "உங்கள் வங்கிக் கணக்கில் பணம் வரவு வைக்கப்படும் வரை பொருட்களை அனுப்ப வேண்டாம்.",
                    "மிரட்டல்களுக்கு பயந்து எந்த நடவடிக்கையும் எடுக்க வேண்டாம்.",
                    "தேவைப்பட்டால் 1930 எண்ணில் புகார் அளிக்கவும்.",
                ],
                "family_alert": {
                    "title": "⚠️ எச்சரிக்கை: போலி கட்டண ஸ்கிரீன்ஷாட் மோசடி",
                    "body": "யாராவது பணம் அனுப்பிவிட்டதாக ஸ்கிரீன்ஷாட் காட்டினால் உடனே நம்பி பொருட்களை அனுப்பாதீர்கள் அல்லது பணம் திருப்பி அனுப்பாதீர்கள். உங்கள் வங்கி செயலியைத் திறந்து பாருங்கள்.",
                    "tips": [
                        "ஸ்கிரீன்ஷாட் பண வரவிற்கான ஆதாரம் அல்ல.",
                        "உங்கள் சொந்த வங்கி செயலியில் கணக்கு இருப்பை சரிபார்க்கவும்.",
                        "போலீஸ் புகார் மிரட்டல்களை புறக்கணிக்கவும்.",
                    ],
                },
            },
            "hi": {
                "explanation": "यह भुगतान स्क्रीनशॉट छेड़छाड़ किया हुआ प्रतीत होता है। केवल एक स्क्रीनशॉट कभी भी भुगतान का पुख्ता प्रमाण नहीं हो सकता। 1 घंटे में कूरियर न भेजने पर पुलिस में शिकायत करने की धमकी दबाव बनाने का पुराना हथकंडा है।",
                "next_steps": [
                    "एक स्क्रीनशॉट भुगतान साबित नहीं कर सकता। अपने बैंक ऐप या आधिकारिक बैंक एसएमएस में पुष्टि करें।",
                    "जब तक बैंक खाते में राशि जमा न दिखे, कोई सामान न भेजें।",
                    "धमकी भरे संदेशों पर प्रतिक्रिया न दें।",
                    "साइबर हेल्पलाइन 1930 पर सहायता प्राप्त करें।",
                ],
                "family_alert": {
                    "title": "⚠️ सावधान: फर्जी भुगतान स्क्रीनशॉट की चेतावनी",
                    "body": "केवल स्क्रीनशॉट देखकर कभी भी सामान न भेजें और न ही कोई रिफंड वापस करें। हमेशा अपने स्वयं के बैंक ऐप में जाकर खाते की शेष राशि जांचें।",
                    "tips": [
                        "स्क्रीनशॉट भुगतान का सबूत नहीं होता।",
                        "अपने बैंक ऐप में जाकर खाते की जांच करें।",
                        "पुलिस शिकायत की झूठी धमकियों से न डरें।",
                    ],
                },
            },
        },
    },
}


def get_mock_response(
    text: Optional[str] = None,
    filename: Optional[str] = None,
    language: str = "en",
    mode: str = "mock",
) -> AnalyzeResponse:
    """
    Selects one of realistic mock results based on text keywords or filename.
    Defaults to fake internship offer scam if no pattern matches.
    """
    query = (text or "").lower() + " " + (filename or "").lower()

    if any(k in query for k in ["payment", "paid", "screenshot", "paytm", "gpay", "phonepe", "s1", "receipt", "rupees", "ref"]):
        scenario = MOCK_SCENARIOS["payment"]
    elif any(k in query for k in ["parcel", "courier", "post", "delivery", "track"]):
        scenario = MOCK_SCENARIOS["courier"]
    elif any(k in query for k in ["debited", "hdfc", "sbi", "bank", "balance", "swiggy", "inr"]):
        scenario = MOCK_SCENARIOS["bank_alert"]
    else:
        scenario = MOCK_SCENARIOS["internship"]

    lang = language if language in ["en", "ta", "hi"] else "en"
    lang_content = scenario["i18n"][lang]

    return AnalyzeResponse(
        request_id=str(uuid.uuid4()),
        band=scenario["band"],
        score=scenario["score"],
        confidence=scenario["confidence"],
        scam_type=scenario["scam_type"],
        language=lang,
        extracted=ExtractedData(**scenario["extracted"]),
        signals=[Signal(**s) for s in scenario["signals"]],
        tool_results=[ToolResult(**tr) for tr in scenario["tool_results"]],
        explanation=lang_content["explanation"],
        next_steps=lang_content["next_steps"],
        family_alert=FamilyAlert(**lang_content["family_alert"]),
        limitations="This assessment is based exclusively on the provided text and imagery. Absence of detected red flags does not guarantee authenticity.",
        mode=mode if mode in ["cloud", "local", "mock"] else "mock",
        timings_ms={
            "total": 312,
            "extraction": 140,
            "verifiers": 82,
            "rules": 25,
            "explanation": 65,
        },
    )
