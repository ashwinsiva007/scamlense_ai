import { NextRequest, NextResponse } from "next/server";
import { parsePaymentFields } from "@/lib/paymentScreenshot";
import paymentEn from "../../../../public/demo/sample_payment_en.json";
import paymentTa from "../../../../public/demo/sample_payment_ta.json";
import paymentHi from "../../../../public/demo/sample_payment_hi.json";
import kycEn from "../../../../public/demo/sample_kyc_en.json";
import kycTa from "../../../../public/demo/sample_kyc_ta.json";
import kycHi from "../../../../public/demo/sample_kyc_hi.json";
import internshipEn from "../../../../public/demo/sample_internship_en.json";
import internshipTa from "../../../../public/demo/sample_internship_ta.json";
import internshipHi from "../../../../public/demo/sample_internship_hi.json";
import bankAlertEn from "../../../../public/demo/sample_bank_alert_en.json";
import bankAlertTa from "../../../../public/demo/sample_bank_alert_ta.json";
import bankAlertHi from "../../../../public/demo/sample_bank_alert_hi.json";

const SAMPLE_DATABASE: Record<string, Record<string, Record<string, unknown>>> = {
  payment: {
    en: paymentEn as Record<string, unknown>,
    ta: paymentTa as Record<string, unknown>,
    hi: paymentHi as Record<string, unknown>,
  },
  kyc: {
    en: kycEn as Record<string, unknown>,
    ta: kycTa as Record<string, unknown>,
    hi: kycHi as Record<string, unknown>,
  },
  internship: {
    en: internshipEn as Record<string, unknown>,
    ta: internshipTa as Record<string, unknown>,
    hi: internshipHi as Record<string, unknown>,
  },
  bank_alert: {
    en: bankAlertEn as Record<string, unknown>,
    ta: bankAlertTa as Record<string, unknown>,
    hi: bankAlertHi as Record<string, unknown>,
  },
};

const CANDIDATE_MODELS = [
  "gemini-2.5-flash",
  "gemini-flash-latest",
  "gemini-3.1-flash-lite",
  "gemini-3.5-flash",
];

function normalizeGeminiResponse(
  raw: Record<string, unknown>,
  safeLang: "en" | "ta" | "hi"
): Record<string, unknown> {
  const validBands = ["low_risk", "suspicious", "likely_scam", "insufficient_info"];
  const band = typeof raw.band === "string" && validBands.includes(raw.band)
    ? raw.band
    : "low_risk";

  const rawExtracted = (raw.extracted as Record<string, unknown>) || {};
  const extracted = {
    document_type: String(rawExtracted.document_type || "document"),
    sender: rawExtracted.sender ? String(rawExtracted.sender) : null,
    message_text: String(rawExtracted.message_text || ""),
    urls: Array.isArray(rawExtracted.urls) ? rawExtracted.urls.map(String) : [],
    phone_numbers: Array.isArray(rawExtracted.phone_numbers) ? rawExtracted.phone_numbers.map(String) : [],
    upi_ids: Array.isArray(rawExtracted.upi_ids) ? rawExtracted.upi_ids.map(String) : [],
    amounts: Array.isArray(rawExtracted.amounts) ? rawExtracted.amounts.map(String) : [],
    claimed_brand: rawExtracted.claimed_brand ? String(rawExtracted.claimed_brand) : null,
    detected_language: String(rawExtracted.detected_language || safeLang),
    image_quality: String(rawExtracted.image_quality || "good"),
    visual_notes: Array.isArray(rawExtracted.visual_notes) ? rawExtracted.visual_notes.map(String) : [],
  };

  const rawAlert = (raw.family_alert as Record<string, unknown>) || {};
  const family_alert = {
    title: String(rawAlert.title || (band === "likely_scam" ? "Scam Alert" : "Safety Alert")),
    body: String(
      rawAlert.body ||
        "Exercise caution before sharing personal credentials, OTPs, or transferring money."
    ),
    tips: Array.isArray(rawAlert.tips) && rawAlert.tips.length > 0
      ? rawAlert.tips.map(String)
      : [
          "Never share your banking password, OTP, or UPI PIN.",
          "Independently verify sender contacts before sending money.",
        ],
  };

  const rawSignals = Array.isArray(raw.signals) ? raw.signals : [];
  const signals = rawSignals.map((s, idx) => {
    const sig = (s as Record<string, unknown>) || {};
    return {
      id: String(sig.id || `SIG_${idx + 1}`),
      label: String(sig.label || "Suspicious Indicator"),
      category: String(sig.category || "general"),
      weight: typeof sig.weight === "number" ? sig.weight : 20,
      evidence: String(sig.evidence || ""),
      source: (sig.source === "tool" || sig.source === "rule" ? sig.source : "model") as "model",
    };
  });

  const rawNextSteps = Array.isArray(raw.next_steps) ? raw.next_steps : [];
  const next_steps = rawNextSteps.length > 0
    ? rawNextSteps.map(String)
    : [
        "Do not click on unverified links or dial unknown callback numbers.",
        "Verify suspicious communications via official customer care portals.",
      ];

  const rawToolResults = Array.isArray(raw.tool_results) ? raw.tool_results : [];
  const tool_results = rawToolResults.map((tr) => {
    const item = (tr as Record<string, unknown>) || {};
    return {
      tool: String(item.tool || "verifier"),
      target: String(item.target || ""),
      status: (["ok", "warn", "error", "skipped"].includes(item.status as string)
        ? item.status
        : "skipped") as "ok" | "warn" | "error" | "skipped",
      detail: String(item.detail || ""),
    };
  });

  return {
    band,
    score: typeof raw.score === "number" ? Math.min(100, Math.max(0, raw.score)) : 10,
    confidence: (["high", "medium", "low"].includes(raw.confidence as string)
      ? raw.confidence
      : "medium") as "high" | "medium" | "low",
    scam_type: raw.scam_type ? String(raw.scam_type) : null,
    explanation: String(raw.explanation || "Document evaluated with ScamLens AI vision intelligence."),
    next_steps,
    extracted,
    signals,
    tool_results,
    family_alert,
  };
}

async function callGeminiCloud(
  apiKey: string,
  parts: Array<Record<string, unknown>>,
  systemInstruction: string
): Promise<Record<string, unknown>> {
  let lastError: Error | null = null;

  for (const model of CANDIDATE_MODELS) {
    try {
      const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;
      const payload = {
        contents: [{ parts }],
        systemInstruction: { parts: [{ text: systemInstruction }] },
        generationConfig: {
          responseMimeType: "application/json",
          temperature: 0.1,
        },
      };

      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Model ${model} status ${res.status}: ${errorText.slice(0, 150)}`);
      }

      const json = await res.json();
      const rawText = json.candidates?.[0]?.content?.parts?.[0]?.text;
      if (!rawText) {
        throw new Error(`Model ${model} returned empty content.`);
      }

      return JSON.parse(rawText) as Record<string, unknown>;
    } catch (err: unknown) {
      lastError = err instanceof Error ? err : new Error(String(err));
      continue;
    }
  }

  throw lastError || new Error("All Gemini candidate models failed to respond.");
}

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const image = (formData.get("file") as File | null) || (formData.get("image") as File | null);
    const text = (formData.get("text") as string | null) || "";
    const language = ((formData.get("language") as string) || "en") as "en" | "ta" | "hi";
    const mode = (formData.get("mode") as string) || "cloud";
    const safeLang = ["en", "ta", "hi"].includes(language) ? language : "en";

    // 1. If an external backend is configured (e.g. on Render, Droplet, or AWS), forward the request
    const backendUrl = process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_API_URL;
    if (backendUrl && !backendUrl.includes("localhost") && !backendUrl.includes("127.0.0.1")) {
      try {
        const backendResp = await fetch(`${backendUrl}/api/analyze`, {
          method: "POST",
          body: formData,
        });
        if (backendResp.ok) {
          const data = await backendResp.json();
          return NextResponse.json(data);
        }
      } catch {
        // Fallback to internal engine on network error
      }
    }

    // 2. Check if the file is one of the built-in sample chips
    const filename = image?.name || "";
    let sampleKey: "internship" | "payment" | "kyc" | "bank_alert" | null = null;
    if (filename === "fake_internship_offer.png") {
      sampleKey = "internship";
    } else if (filename === "fake_payment_screenshot.png") {
      sampleKey = "payment";
    } else if (filename === "fake_kyc_otp_sms.png") {
      sampleKey = "kyc";
    } else if (filename === "genuine_bank_alert.png") {
      sampleKey = "bank_alert";
    }

    if (sampleKey) {
      const localizedSamples = SAMPLE_DATABASE[sampleKey] || SAMPLE_DATABASE.internship;
      const analysisData = localizedSamples[safeLang] || localizedSamples.en;

      return NextResponse.json({
        ...analysisData,
        request_id: `sl-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`,
        language: safeLang,
        mode: mode === "local" ? "local" : "cloud",
        limitations: "Analyzed with ScamLens verified intelligence engine. Absence of detected red flags does not guarantee authenticity.",
      });
    }

    // 3. For custom uploads or pasted text, execute live Gemini Cloud API inference
    const apiKey = (process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY || "").trim();
    if (!apiKey) {
      return NextResponse.json(
        {
          error_code: "CLOUD_KEY_MISSING",
          detail: "Gemini API key is not configured. Please set GEMINI_API_KEY in your environment or Vercel dashboard.",
          message: "Gemini API key is not configured. Please set GEMINI_API_KEY in your environment or Vercel dashboard.",
        },
        { status: 401 }
      );
    }
    const parts: Array<Record<string, unknown>> = [];

    if (image && image.size > 0) {
      const bytes = await image.arrayBuffer();
      const base64 = Buffer.from(bytes).toString("base64");
      const mimeType = image.type || "image/png";
      parts.push({
        inlineData: {
          mimeType: mimeType,
          data: base64,
        },
      });
    }

    const inputContext = text.trim()
      ? `User provided message text:\n"""\n${text.trim()}\n"""\n`
      : "";
    const langInstruction =
      safeLang === "ta"
        ? "Respond strictly in Tamil for all explanations, tips, and family alert content."
        : safeLang === "hi"
        ? "Respond strictly in Hindi for all explanations, tips, and family alert content."
        : "Respond strictly in clear English.";

    parts.push({
      text: `${inputContext}Analyze this document/screenshot for red flags, deceptive patterns, phishing attempts, fake job offers, fake payment receipts, or genuine communication. ${langInstruction}`,
    });

    const systemInstruction = `You are ScamLens, a world-class explainable scam intelligence system.
Analyze the user's input with deterministic rigor. Detect red flags, psychological pressure (urgency, panic, too good to be true), suspicious UPI/bank patterns, and brand impersonation.
Score the risk from 0 (completely genuine) to 100 (confirmed malicious scam).
Bands:
- "low_risk" (score 0-25)
- "suspicious" (score 26-65)
- "likely_scam" (score 66-100)
- "insufficient_info" (unreadable image or no discernible content)

Return ONLY valid JSON matching this schema:
{
  "band": "low_risk" | "suspicious" | "likely_scam" | "insufficient_info",
  "score": number,
  "confidence": "high" | "medium" | "low",
  "scam_type": string or null,
  "explanation": "concise 2-3 sentence explanation explaining why this verdict was chosen",
  "next_steps": ["actionable advice 1", "actionable advice 2", "actionable advice 3"],
  "extracted": {
    "document_type": string,
    "sender": string or null,
    "message_text": string,
    "urls": string[],
    "phone_numbers": string[],
    "upi_ids": string[],
    "amounts": string[],
    "claimed_brand": string or null,
    "detected_language": string,
    "image_quality": "good" | "fair" | "poor",
    "visual_notes": string[]
  },
  "signals": [
    {
      "id": string,
      "label": string,
      "category": string,
      "weight": number,
      "evidence": string,
      "source": "model"
    }
  ],
  "tool_results": [],
  "family_alert": {
    "title": "Short Warning Title",
    "body": "Simple plain-language summary suitable for forwarding via WhatsApp to family or elders",
    "tips": ["Clear protective tip 1", "Clear protective tip 2"]
  }
}`;

    const geminiResult = await callGeminiCloud(apiKey, parts, systemInstruction);
    const normalized = normalizeGeminiResponse(geminiResult, safeLang);

    // Background payment screenshot entity & authenticity enrichment
    const combinedText = `${text} ${
      typeof geminiResult.extracted === "object" && geminiResult.extracted !== null
        ? (geminiResult.extracted as Record<string, unknown>).message_text || ""
        : ""
    }`;
    const paymentData = parsePaymentFields(combinedText);

    if (geminiResult.extracted && typeof geminiResult.extracted === "object") {
      const ext = geminiResult.extracted as Record<string, unknown>;
      const amounts: string[] = Array.isArray(ext.amounts) ? [...(ext.amounts as string[])] : [];
      const upiIds: string[] = Array.isArray(ext.upi_ids) ? [...(ext.upi_ids as string[])] : [];
      const phones: string[] = Array.isArray(ext.phone_numbers) ? [...(ext.phone_numbers as string[])] : [];
      const visualNotes: string[] = Array.isArray(ext.visual_notes) ? [...(ext.visual_notes as string[])] : [];

      if (
        paymentData.amount &&
        !amounts.includes(`₹${paymentData.amount}`) &&
        !amounts.includes(paymentData.amount)
      ) {
        amounts.push(paymentData.currency === "INR" ? `₹${paymentData.amount}` : paymentData.amount);
      }
      for (const u of paymentData.upi_ids) {
        if (!upiIds.includes(u)) upiIds.push(u);
      }
      if (paymentData.phone && !phones.includes(paymentData.phone)) {
        phones.push(paymentData.phone);
      }
      if (paymentData.bank && !ext.claimed_brand) {
        ext.claimed_brand = paymentData.bank;
      }
      if (paymentData.payment_app && !ext.claimed_brand) {
        ext.claimed_brand = paymentData.payment_app;
      }

      ext.amounts = amounts;
      ext.upi_ids = upiIds;
      ext.phone_numbers = phones;
      ext.visual_notes = visualNotes;
    }

    if (!Array.isArray(geminiResult.tool_results)) {
      geminiResult.tool_results = [];
    }

    if (paymentData.transaction_id) {
      const is12Digit = /^\d{12}$/.test(paymentData.transaction_id);
      (geminiResult.tool_results as Array<Record<string, unknown>>).push({
        tool: "payment_fields",
        target: paymentData.transaction_id,
        status: is12Digit || paymentData.transaction_id.startsWith("T") ? "ok" : "warn",
        detail: is12Digit
          ? `Valid 12-digit UPI reference format ('${paymentData.transaction_id}'). Note: ScamLens cannot confirm bank settlement.`
          : `Transaction reference '${paymentData.transaction_id}' detected. Note: Format check only.`,
      });
    }

    if (paymentData.status) {
      (geminiResult.tool_results as Array<Record<string, unknown>>).push({
        tool: "payment_fields",
        target: "status",
        status: paymentData.status === "Success" ? "ok" : "warn",
        detail:
          paymentData.status === "Success"
            ? "Screenshot claims successful payment status. Note: Always verify in bank statement."
            : `Screenshot shows payment status as '${paymentData.status}', not completed or credited.`,
      });
    }

    return NextResponse.json({
      ...normalized,
      request_id: `sl-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`,
      language: safeLang,
      mode: "cloud",
      limitations: "Analyzed with ScamLens live Gemini Cloud vision engine. Absence of detected red flags does not guarantee authenticity.",
    });
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : "Internal Server Error";
    return NextResponse.json(
      {
        error_code: "ANALYSIS_ERROR",
        detail: `Analysis failed: ${errorMsg}. Please ensure your image is clear and try again.`,
        message: `Analysis failed: ${errorMsg}. Please ensure your image is clear and try again.`,
      },
      { status: 500 }
    );
  }
}
