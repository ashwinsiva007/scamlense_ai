# Contributing to ScamLens

Thank you for your interest in contributing to ScamLens! We are committed to building an open, transparent, community-driven, and privacy-first defense against digital deception.

---

## 🛠️ Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## 🎯 Where We Need Help (Good First Issues)

If you are looking for an issue to get started with, check out [`docs/GOOD_FIRST_ISSUES.md`](docs/GOOD_FIRST_ISSUES.md) for 10 ready-to-claim ideas:
- Adding regional Indian languages (Telugu, Kannada, Malayalam, Bengali, Marathi)
- Adding new Indian brands to `backend/data/brands.yaml`
- Adding emerging scam patterns (digital arrest scams, electricity meter threats, fake crypto task bots)
- Expanding Tamil & Hindi colloquial and transliterated keyword coverage
- Adding dark mode to the Next.js UI

---

## 📦 How to Add a Rule Pack

ScamLens separates perception from judgment: all fraud risk scores are decided by auditable YAML rule packs located in `backend/rules/`.

### 1. Rule Pack Structure
Every rule pack is a YAML file named `<category>.yaml` adhering to `backend/rules/rule_pack_schema.json`:

```yaml
category: "money_demands"  # Must match one of the 10 signal categories
rules:
  - id: "MONEY_ADVANCE_FEE"
    category: "money_demands"
    label: "Advance Registration / Security Fee Demanded"
    weight: 40.0             # Positive weight (1.0 - 50.0) or negative for reducers (-10.0 to -25.0)
    patterns:
      en:
        - "(?:refundable|advance|registration|security)\\s+(?:fee|deposit|amount)"
        - "pay\\s+(?:rs\\.?|inr|₹)\\s*\\d+\\s+to\\s+(?:confirm|secure|reserve)"
      ta:
        - "(?:முன்பணம்|பதிவுக் கட்டணம்|டெபாசிட்|பணம் செலுத்தவும்)"
      hi:
        - "(?:पंजीकरण शुल्क|सुरक्षा राशि|एडवांस फीस|पैसे जमा करें)"
    explanation_templates:
      en: "Demands an upfront fee before services or employment are rendered."
      ta: "சேவை அல்லது வேலைவாய்ப்பிற்கு முன் முன்பணம் கோருகிறது."
      hi: "सेवा या नौकरी शुरू करने से पहले अग्रिम शुल्क की मांग करता है।"
```

### 2. Supported Signal Categories
- `money_demands`: Advance fees, courier charges, interview deposits.
- `credentials`: Requests for OTP, UPI PIN, ATM PIN, passwords, screen share (AnyDesk).
- `urgency_threat`: Time limits (within 24 hours, tonight 9:30 PM, warrant issued).
- `too_good`: Part-time job (₹5000/day liking videos), lottery winnings, guaranteed returns.
- `impersonation`: Claiming to represent Google, SBI, HDFC, India Post via unofficial channels.
- `links`: Shortened URLs (`bit.ly`), numeric IP links, typosquatted brand domains.
- `sender`: Official organizations messaging from `@gmail.com` or international phone codes (+92).
- `document_quality`: Fake offer letters, blurred seals, mismatched fonts.
- `payment_screenshot`: Forged UPI transaction slips, missing UTR, mismatched layout.
- `reducers`: Negative weights for genuine transactional notifications (masked A/c **1234).

### 3. Validate Your Rule Pack
Before committing, run the automated schema and regex validator:

```bash
python backend/scripts/validate_rule_packs.py
```

Expected output:
```text
Validating 10 rule packs against rule_pack_schema.json...
✅ credentials.yaml (5 rules) - PASS
...
All rule packs are structurally valid!
```

---

## 🧪 Testing Your Changes

### Backend Unit & Integration Tests
Run pytest with the full suite of 100+ tests:
```bash
cd backend
pytest
```

### Evaluation & Benchmark Suite
Run the comparative evaluation across synthetic fixtures to verify no regression:
```bash
python backend/eval/run_eval.py
```
This regenerates `backend/eval/results.json` and `backend/eval/results.md`.

### Frontend Type Check & Lint
Ensure the Next.js frontend passes all TypeScript and ESLint checks:
```bash
cd frontend
npm run lint
npx tsc --noEmit
npm run build
```

---

## ⚠️ Safe Contributing: Strict Privacy Policy

1. **NO REAL PII:** NEVER commit real screenshots containing live personal identifying information, real phone numbers, real Aadhaar/PAN cards, or private bank account details.
2. **SYNTHETIC DATA ONLY:** Construct synthetic fixtures using fictional corporate entities and standard test formats (e.g. `+91 98765 43210`, `testuser@okaxis`).
3. **NEVER LOG USER CONTENT:** All code contributions must adhere to the zero-persistence guarantee. No images or message texts may be written to disk or logged.

---

## 📝 Pull Request Checklist

- [ ] Rule pack conforms to `rule_pack_schema.json` and passes `validate_rule_packs.py`.
- [ ] All backend tests pass (`pytest`).
- [ ] Evaluation runner completes cleanly (`python backend/eval/run_eval.py`).
- [ ] Frontend builds without TypeScript or ESLint errors (`npm run lint`, `npm run build`).
- [ ] No personal information or real-world credentials included.
- [ ] Documentation updated if relevant.
