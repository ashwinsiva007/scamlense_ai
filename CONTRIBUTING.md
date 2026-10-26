# Contributing to ScamLens

Thank you for your interest in contributing to ScamLens! We are committed to building an open, transparent, and privacy-first defense against digital deception.

---

## 🛠️ Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## 🔍 How Can You Contribute?

### 1. Contributing Rule Packs (`backend/rules/`)
ScamLens relies on declarative YAML rule packs for transparent scoring. You can add new rules to address emerging scams.
- Each rule must define:
  - `id`: Unique uppercase string identifier (e.g. `MONEY_CRYPTO_REFUND`).
  - `label`: Brief human-readable description.
  - `category`: Must match one of the 10 signal categories.
  - `weight`: Score weight (1.0 to 50.0).
  - `patterns`: Regex or substring matches.
  - `explanation_templates`: Clear plain-language explanations in `en`, `ta`, and `hi`.

### 2. Contributing New Languages (`frontend/src/i18n/`)
To add a new language:
1. Create a new locale file in `frontend/src/i18n/<lang_code>.json`.
2. Provide translations for UI elements, navigation, and disclaimer notices.
3. Add explanatory templates in `backend/app/services/explainer.py`.
4. Open an issue using the `New Language` template.

### 3. Submitting Synthetic Test Samples (`samples/`)
⚠️ **Strict Privacy Rule:** NEVER upload real screenshots containing live personal identifying information (PII), real phone numbers, real Aadhaar cards, or private bank account details. All samples must be synthetic, redacted, or artificially constructed.

---

## 🚀 Development Workflow

1. Fork the repository and create your branch from `main`:
   ```bash
   git checkout -b feature/my-feature
   ```
2. Set up the local Python virtual environment and install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   pytest
   ```
3. Set up frontend dependencies and run linter:
   ```bash
   cd ../frontend
   npm install
   npm run build
   ```
4. Commit your changes with clear, descriptive commit messages.
5. Push to your fork and submit a Pull Request.

---

## 📝 Pull Request Checklist
- [ ] Code follows project formatting and style guidelines.
- [ ] Backend tests pass (`pytest`).
- [ ] Frontend builds without TypeScript or ESLint errors (`npm run build`).
- [ ] No personal information or real-world credentials included.
- [ ] Documentation updated if necessary.
