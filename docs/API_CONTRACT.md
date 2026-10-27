# ScamLens API Contract

This document specifies the exact REST API contract between the frontend (Next.js) and the backend (FastAPI).

---

## 1. Endpoints Overview

| Method | Path | Request Content-Type | Response Content-Type | Description |
|:---|:---|:---|:---|:---|
| `GET` | `/api/health` | None | `application/json` | System health check and runtime connectivity status |
| `POST` | `/api/analyze` | `multipart/form-data` | `application/json` | Analyzes image and/or text input for scam markers |
| `GET` | `/api/benchmarks` | None | `application/json` | Performance metrics and detection benchmark summary |

---

## 2. Endpoint Details

### 2.1 `GET /api/health`

Verifies backend readiness, current operating mode, and model reachability.

#### Response Body (`200 OK`)
```json
{
  "status": "ok",
  "mode": "mock",
  "model": "google/gemma-4-9b-it",
  "ollama_reachable": false,
  "cloud_key_set": false
}
```

#### Fields
| Field | Type | Description |
|:---|:---|:---|
| `status` | `string` | Always `"ok"` if service is active. |
| `mode` | `string` | `"cloud"`, `"local"`, or `"mock"`. |
| `model` | `string` | Configured model identifier (e.g., `"google/gemma-4-9b-it"`). |
| `ollama_reachable` | `boolean` | `true` if local Ollama daemon responds on `OLLAMA_BASE_URL`. |
| `cloud_key_set` | `boolean` | `true` if GEMINI_API_KEY is configured and valid format. |

---

### 2.2 `POST /api/analyze`

Processes an uploaded image or pasted text to extract entities, evaluate rule packs, verify URLs/domains, and produce risk verdicts and multilingual explanations.

#### Request Headers
- `Content-Type: multipart/form-data`

#### Form Fields
| Field | Type | Required? | Constraints / Description |
|:---|:---|:---|:---|
| `image` | `file` (binary) | Optional* | Uploaded image or document file. Backward compatible field name. Max 8 MB. (*Either `image`/`file` or `text` is required). Supported formats: Images (PNG, JPG/JPEG, WEBP, GIF, BMP, TIFF, HEIC/HEIF) and Documents (PDF, DOCX, DOC, TXT, RTF, EML). |
| `file` | `file` (binary) | Optional* | Alias for `image`. Accepts identical image and document formats. (*Either `image`/`file` or `text` is required). |
| `text` | `string` | Optional* | Plain text or SMS copy pasted by user. (*Either `image`/`file` or `text` is required). |
| `language` | `string` | Optional | Language for generated verdict & family alert. One of: `"en"` (default), `"ta"`, `"hi"`. |
| `mode` | `string` | Optional | Override execution mode: `"cloud"`, `"local"`, or `"mock"`. Defaults to system configuration. |

#### Response Body (`200 OK`)
```json
{
  "request_id": "4f9d1bb8-17a4-4f4b-8877-e8369324e930",
  "band": "likely_scam",
  "score": 85,
  "confidence": "high",
  "scam_type": "fake_internship_fee",
  "language": "en",
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
    "visual_notes": ["Official Google header style mimicked", "Standard text font"]
  },
  "signals": [
    {
      "id": "MONEY_ADVANCE_FEE",
      "label": "Advance Security Fee Demanded",
      "category": "money_demands",
      "weight": 40.0,
      "evidence": "refundable security fee of Rs. 1500",
      "source": "rule"
    },
    {
      "id": "URGENCY_DEADLINE_24H",
      "label": "Artificial Urgency Deadline",
      "category": "urgency_threat",
      "weight": 25.0,
      "evidence": "within 24 hours to secure your seat",
      "source": "rule"
    },
    {
      "id": "SENDER_DOMAIN_MISMATCH",
      "label": "Unofficial Sender Domain",
      "category": "impersonation",
      "weight": 20.0,
      "evidence": "tech-hiring-portal.org claiming to represent Google",
      "source": "tool"
    }
  ],
  "tool_results": [
    {
      "tool": "domain_verifier",
      "target": "tech-hiring-portal.org",
      "status": "warn",
      "detail": "Domain registered 4 days ago. Not associated with Google LLC."
    },
    {
      "tool": "upi_verifier",
      "target": "techcareers@okaxis",
      "status": "warn",
      "detail": "Individual VPA format used instead of registered corporate merchant."
    }
  ],
  "explanation": "This offer letter shows strong signs of an internship recruitment scam. Legitimate employers never require applicants to pay a 'refundable security fee' or deposit money via UPI to confirm an offer. Furthermore, the email sender domain is not affiliated with Google.",
  "next_steps": [
    "Do NOT transfer any money or pay the requested Rs. 1500 via UPI.",
    "Do not share your Aadhaar, bank details, or personal ID documents.",
    "Verify genuine vacancies directly on the official careers page at careers.google.com.",
    "Report this fraudulent incident to the National Cybercrime Portal at cybercrime.gov.in or dial 1930."
  ],
  "family_alert": {
    "title": "⚠️ Caution: Fake Internship / Job Deposit Alert",
    "body": "If anyone sends you a job or internship offer asking for an upfront registration or equipment fee via UPI, DO NOT PAY. Genuine companies never charge candidates money to start work.",
    "tips": [
      "Never pay money to get a job or internship.",
      "Check the company email address carefully (@company.com).",
      "Discuss with a family member before transferring funds."
    ]
  },
  "limitations": "This assessment is based exclusively on the provided text and imagery. Absence of detected red flags does not guarantee authenticity.",
  "mode": "mock",
  "timings_ms": {
    "total": 312,
    "extraction": 140,
    "verifiers": 82,
    "rules": 25,
    "explanation": 65
  }
}
```

#### Error Responses
- `400 Bad Request`: When neither `image` nor `text` is supplied.
  ```json
  {
    "detail": "At least one of 'image' or 'text' must be provided."
  }
  ```
- `413 Payload Too Large`: When uploaded file exceeds `MAX_UPLOAD_MB`.
- `422 Unprocessable Entity`: Validation failure on input parameters.

---

### 2.3 `GET /api/benchmarks`

Retrieves detection benchmark statistics, rule pack version metadata, and evaluation dataset metrics.

#### Response Body (`200 OK`)
```json
{
  "dataset_version": "v0.1-synthetic",
  "total_eval_samples": 45,
  "accuracy": 0.955,
  "precision": 0.960,
  "recall": 0.950,
  "f1_score": 0.955,
  "average_latency_ms": 340,
  "rule_packs_loaded": 9,
  "last_updated": "2026-10-26T00:00:00Z"
}
```
