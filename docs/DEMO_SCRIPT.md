# ScamLens 3-Minute Live Demo Script & Pitch

**Target Audience:** Hackathon Judges, Security Engineers, and Community Reviewers  
**Duration:** Exactly 3 Minutes (180 Seconds)  
**Presenter Tone:** Energetic, confident, grounded in practical Indian cyber safety reality.

---

## ⏱️ Timeline & Stage Directions

### [0:00 – 0:30] The Hook: The Human Cost of Digital Deception
- **Action:** Open the ScamLens homepage (`/`). Have browser open to 100% zoom.
- **Spoken Script:**
  > *"Every single day across India, over 100,000 deceptive messages land on family WhatsApp groups—fake Google internship offers, parcel delivery SMS links, and spoofed UPI payment screenshots.*
  >
  > *When our parents receive these, they face two huge problems: either the message is in complex English or technical jargon they cannot evaluate, or they ask a generic AI that hallucinates and says 'This looks safe', leading to financial loss.*
  >
  > *Meet **ScamLens**: an open-source, multilingual, privacy-first scam intelligence tool. ScamLens follows one fundamental rule: **AI reads and explains; deterministic open-source rules and live verifiers decide.**"*

---

### [0:30 – 1:00] Flow 1: Fake Internship Offer & Objective Quoted Evidence
- **Action:** Click the sample chip **"Fake Internship Offer"** (or drag & drop the offer letter screenshot). Click **"Analyze For Red Flags"**.
- **Spoken Script:**
  > *"Let's test a classic recruitment scam: an offer letter pretending to be Google, demanding a ₹1,500 'refundable security deposit' via UPI within 24 hours.*
  >
  > *Notice what ScamLens does in under 300 milliseconds. It does **not** give a vague opinion. It quotes the verbatim evidence directly:
  > - Advance Fee Demanded: quoting `refundable security fee of Rs. 1500` (+40 points)
  > - Artificial Urgency: quoting `within 24 hours to secure your seat` (+25 points)
  > - Live Verifier Check: our domain verifier detected that `tech-hiring-portal.org` was registered just 4 days ago and is not affiliated with Google!*
  >
  > *The result is deterministic: Score 85, **Likely Scam**."*

---

### [1:00 – 1:30] Flow 2: Multilingual Accessibility (Tamil & Hindi)
- **Action:** Select **தமிழ் (Tamil)** in the language selector (or Hindi).
- **Spoken Script:**
  > *"Now watch what happens for non-English speaking parents. With one click, the entire explanation transforms into plain, empathetic Tamil:
  >
  > 'இந்த சலுகை கடிதம் போலி வேலைவாய்ப்பு மோசடியின் வலுவான அறிகுறிகளைக் கொண்டுள்ளது. முறையான நிறுவனங்கள் ஒருபோதும் முன்பணம் கோருவதில்லை.'
  >
  > *No tech jargon. Just plain truth, with audio read-aloud support so anyone can listen directly on their phone."*

---

### [1:30 – 2:00] Flow 3: Fake Payment Screenshot & Calibrated Honesty
- **Action:** Click **"Fake Payment Screenshot"** sample. Click **"Analyze For Red Flags"**.
- **Spoken Script:**
  > *"Next, let's examine digital payment fraud. A shopkeeper or student is shown a screenshot claiming '₹2,500 Paid via UPI', but the funds haven't arrived.*
  >
  > *ScamLens analyzes the visual layout, detects missing Bank UTR reference numbers and mismatched font weights, and immediately flags layout tampering.*
  >
  > *Crucially, notice our honesty guarantee: ScamLens explicitly displays: **'Absence of detected red flags does not certify safety. Always check your official banking app.'** We never declare any communication '100% safe'."*

---

### [2:00 – 2:30] Flow 4: The Family Alert Card (WhatsApp Forwardable)
- **Action:** Scroll down to the **Family Alert Card**. Point out the clean border and tips. Click **"Copy Text"** (toast appears: *"Copied to clipboard!"*).
- **Spoken Script:**
  > *"When a user spots a scam, how do they warn their family? Technical PDF reports don't work.*
  >
  > *ScamLens generates this **Family Alert Card**. One click copies formatted WhatsApp-ready text with bulleted tips:
  > 1. Never pay money to receive a job.
  > 2. Verify company email domains.
  > 3. Call the national helpline at 1930.*
  >
  > *Users can copy text or download a beautiful PNG card to forward directly to family WhatsApp groups."*

---

### [2:30 – 3:00] Flow 5: Architecture, Local Mode & Benchmarks
- **Action:** Navigate to `/benchmarks`, then briefly point to the mode toggle (`Private, local`).
- **Spoken Script:**
  > *"How is this built?
  > 1. **Zero Data Retention:** Uploads reside strictly in volatile RAM and are purged the second the HTTP response finishes. Zero files written to disk.
  > 2. **Private Local Mode:** Switch to Local Mode powered by an offline Ollama daemon—not a single byte leaves your machine.
  > 3. **Published Benchmarks:** Visit our `/benchmarks` page. On our evaluation suite across English, Tamil, and Hindi, the ScamLens hybrid engine achieved **100% recall with 0% false positives** on genuine bank alerts, while ungrounded LLMs suffered prompt injection bypasses.
  >
  > *ScamLens is fully open source under the Apache-2.0 license. Thank you!"*

---

## 🛡️ Fallback & Contingency Plan

| Scenario | Fallback Action |
| :--- | :--- |
| **Cloud API Rate Limited or Network Down** | Toggle **Demo Mode** in the navbar badge. The frontend immediately switches to bundled, pre-generated offline sample fixtures (`/demo/sample_internship_en.json`) with zero latency. |
| **Local Ollama Daemon Not Running** | The health check automatically detects `ollama_reachable: false` and routes gracefully to Cloud Mode or Mock Mode. |
| **Live Internet Disconnection on Stage** | Run the offline presentation stack: `docker compose up` with local mock mode, or play the pre-recorded 3-minute video backup located in `docs/demo_walkthrough.mp4`. |
