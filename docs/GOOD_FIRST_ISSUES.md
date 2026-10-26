# ScamLens Good First Issues (10 Ready-to-Post Issues)

These issues are formatted and ready to be posted to GitHub Issues to welcome open-source contributors during Hacktoberfest and community sprints.

### Recommended Repository Topics:
`hacktoberfest`, `gemma`, `open-source`, `scam-detection`, `india`, `fastapi`, `nextjs`, `cybersecurity`, `upi`, `multilingual`

---

## Issue 1: Add Telugu (`te`) & Kannada (`kn`) Language Support
- **Labels:** `good first issue`, `i18n`, `languages`, `hacktoberfest`
- **Difficulty:** Beginner / Intermediate
- **Description:**  
  Extend ScamLens linguistic coverage to South Indian languages by adding Telugu and Kannada translations.
- **Tasks:**
  1. Create `frontend/src/i18n/te.json` and `frontend/src/i18n/kn.json` mirroring `en.json`.
  2. Add Telugu and Kannada language entries in `frontend/src/context/LanguageContext.tsx`.
  3. Add localized fallback templates and next steps in `backend/app/services/explainer.py`.
- **Acceptance Criteria:**
  - UI language toggle switches between English, Tamil, Hindi, Telugu, and Kannada.
  - Family Alert card renders clean Telugu and Kannada text without truncation.

---

## Issue 2: Expand `brands.yaml` with Indian Fintech & Quick-Commerce Brands
- **Labels:** `good first issue`, `data`, `security`
- **Difficulty:** Beginner
- **Description:**  
  ScamLens verifies brand lookalikes and homoglyphs against `backend/data/brands.yaml`. We need to expand this database to cover prominent Indian investment, fintech, and quick-commerce platforms that fraudsters frequently impersonate.
- **Suggested Brands to Add:**
  - Zerodha (`zerodha.com`)
  - Groww (`groww.in`)
  - Angel One (`angelone.in`)
  - Blinkit (`blinkit.com`)
  - Zepto (`zeptonow.com`)
  - Meesho (`meesho.com`)
  - Tata Neu (`tataneu.com`)
- **Tasks:**
  Add brand entries with official `canonical_domains`, `keywords`, and known `spoof_slugs` to `backend/data/brands.yaml`.
- **Acceptance Criteria:**
  `pytest backend/tests/test_verifiers.py` passes and lookalike tests flag typosquats like `groww-kyc-login.top`.

---

## Issue 3: Add "Digital Arrest" & Fake Law Enforcement Scam Rule Pack
- **Labels:** `good first issue`, `rules`, `fraud-research`
- **Difficulty:** Intermediate
- **Description:**  
  "Digital Arrest" scams are a rapidly surging fraud tactic in India where scammers impersonate CBI, Mumbai Police, ED, or Customs officers over Skype/WhatsApp video claiming an illegal courier was seized in the victim's name.
- **Tasks:**
  1. Add rules to `backend/rules/urgency_threat.yaml` or create a new pack `backend/rules/law_enforcement_impersonation.yaml`.
  2. Add regex patterns in English, Tamil, and Hindi detecting phrases like "CBI parcel seized", "narcotics found", "money laundering investigation", "stay on video call", "digital arrest".
  3. Add unit test fixtures in `backend/eval/fixtures/`.
- **Acceptance Criteria:**
  Passes `python backend/scripts/validate_rule_packs.py` and flags digital arrest message fixtures with high confidence.

---

## Issue 4: Enrich Tamil Colloquial & Transliterated (Tanglish) Keywords
- **Labels:** `good first issue`, `i18n`, `tamil`, `regex`
- **Difficulty:** Beginner
- **Description:**  
  Many fraud SMS and WhatsApp messages targeting Tamil Nadu citizens use Romanized Tamil ("Tanglish") such as *"EB bill kattalana inniku night current cut aagirum"* or *"GPay pannunga"*.
- **Tasks:**
  1. Expand regex patterns in `backend/rules/urgency_threat.yaml` and `backend/rules/money_demands.yaml` with Tanglish colloquialisms (`kattunga`, `anuppunga`, `seiyavum`, `thundikkappadum`).
  2. Verify that regexes do not cause false positives on genuine Tamil debit alerts.
- **Acceptance Criteria:**
  All regexes compile cleanly with `validate_rule_packs.py` and evaluation benchmarks maintain 100% precision.

---

## Issue 5: Enrich Hindi Slang & Romanized (Hinglish) Task Scam Patterns
- **Labels:** `good first issue`, `i18n`, `hindi`, `regex`
- **Difficulty:** Beginner
- **Description:**  
  Work-from-home Telegram scams often use Romanized Hindi phrases like *"Ghar baithe kamaye"*, *"Video like karke paise kamaye"*, *"Telegram group join karo"*, *"Prepaid task complete karo"*.
- **Tasks:**
  1. Update `backend/rules/too_good.yaml` with common Hinglish variations.
  2. Ensure transliterations handle varied phonetic spellings (`kamaye`, `kamayein`, `kamao`).
- **Acceptance Criteria:**
  Passes `validate_rule_packs.py` and detects Hinglish test fixture `fixture_11_hinglish_tanglish_scam.json`.

---

## Issue 6: Add Dark Mode Theme Support with Tailwind & Next-Themes
- **Labels:** `good first issue`, `ui/ux`, `frontend`, `accessibility`
- **Difficulty:** Intermediate
- **Description:**  
  Add an accessible, sleek dark mode toggle to the Next.js frontend for comfortable viewing in low-light environments.
- **Tasks:**
  1. Install or configure `next-themes` in `frontend/src/app/layout.tsx`.
  2. Add dark theme utility tokens in `tailwind.config.ts` (e.g. slate-950 background, slate-900 glass panels).
  3. Add a sun/moon icon toggle button in `Navbar.tsx`.
- **Acceptance Criteria:**
  - Theme preference persists in `localStorage`.
  - Color contrast on risk badges (`likely_scam`, `suspicious`, `low_risk`) meets WCAG AAA standards in dark mode.

---

## Issue 7: Implement Offline IFSC Code & Bank Branch Verifier
- **Labels:** `good first issue`, `feature`, `backend`, `banking`
- **Difficulty:** Intermediate
- **Description:**  
  When an offer letter or payment request quotes a bank IFSC code (e.g. `SBIN0001234`), verify that the IFSC code is a valid registered branch and not a synthetic/bogus code.
- **Tasks:**
  1. Add an offline JSON dataset of active RBI IFSC prefixes in `backend/data/ifsc_prefixes.json`.
  2. Create an `ifsc_verifier` tool in `backend/app/services/verifiers.py`.
  3. Emit a `WARN` signal if an invalid or defunct IFSC code is claimed in formal bank documents.
- **Acceptance Criteria:**
  Unit tests pass and flag mismatched bank names against IFSC prefixes.

---

## Issue 8: Add WhatsApp / Telegram Bot Webhook Integration
- **Labels:** `feature`, `integration`, `bot`
- **Difficulty:** Advanced
- **Description:**  
  Allow elderly relatives or community groups to forward suspicious messages directly to a verified Telegram or WhatsApp bot and receive the Family Alert card as an instant reply.
- **Tasks:**
  1. Create a lightweight webhook listener endpoint in `backend/app/api/routes.py` (e.g., `/api/webhook/telegram`).
  2. Pipe forwarded images or texts into `run_pipeline(text=..., language="ta"|"hi"|"en")`.
  3. Reply with the formatted Family Alert body and risk band emoji.
- **Acceptance Criteria:**
  Stateless webhook responds within 5 seconds without storing sender chat logs.

---

## Issue 9: Add Image Contrast & Perspective De-skew Preprocessing
- **Labels:** `image-processing`, `python`, `pillow`
- **Difficulty:** Intermediate
- **Description:**  
  Users often photograph printed QR codes or ATM slips from steep angles or in dark rooms, causing OCR text extraction to fail.
- **Tasks:**
  1. Add optional adaptive contrast enhancement (CLAHE or unsharp mask) in `backend/app/services/image_utils.py`.
  2. Detect perspective skew of rectangular receipts and auto-rotate before passing to vision model.
- **Acceptance Criteria:**
  Improves OCR text extraction accuracy on low-contrast test samples without increasing processing latency by more than 150ms.

---

## Issue 10: Add Bengali (`bn`) & Marathi (`mr`) Explanations & Alert Cards
- **Labels:** `good first issue`, `i18n`, `languages`
- **Difficulty:** Beginner / Intermediate
- **Description:**  
  Extend ScamLens to two of India's most populous linguistic regions: West Bengal and Maharashtra.
- **Tasks:**
  1. Add `bn.json` and `mr.json` under `frontend/src/i18n/`.
  2. Add Bengali and Marathi translation templates to `backend/app/services/explainer.py`.
  3. Add sample phishing alerts in Bengali and Marathi to `backend/eval/fixtures/`.
- **Acceptance Criteria:**
  All tests and lint checks pass; Family Alert cards render properly formatted Bengali and Devanagari script.
