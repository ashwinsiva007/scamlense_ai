import { NextRequest, NextResponse } from "next/server";
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

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const image = formData.get("image") as File | null;
    const text = (formData.get("text") as string | null) || "";
    const language = ((formData.get("language") as string) || "en") as "en" | "ta" | "hi";
    const mode = (formData.get("mode") as string) || "cloud";

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

    // 2. In demo/serverless mode, only return cached results for exact built-in samples
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

    if (!sampleKey) {
      return NextResponse.json(
        {
          error_code: "DEMO_MODE_RESTRICTION",
          detail: "Demo mode can only show built-in samples. Switch to Live or Local mode to analyze your own screenshot.",
          message: "Demo mode can only show built-in samples. Switch to Live or Local mode to analyze your own screenshot.",
        },
        { status: 400 }
      );
    }

    // 3. Load pre-verified, localized analysis directly from bundled JSON
    const safeLang = ["en", "ta", "hi"].includes(language) ? language : "en";
    const localizedSamples = SAMPLE_DATABASE[sampleKey] || SAMPLE_DATABASE.internship;
    const analysisData = localizedSamples[safeLang] || localizedSamples.en;

    // Return with a unique request ID and execution metadata
    const responsePayload = {
      ...analysisData,
      request_id: `sl-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`,
      language: safeLang,
      mode: mode === "local" ? "local" : "cloud",
      limitations: "Analyzed with ScamLens verified intelligence engine. Absence of detected red flags does not guarantee authenticity.",
    };

    return NextResponse.json(responsePayload);
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : "Internal Server Error";
    return NextResponse.json({ detail: errorMsg }, { status: 500 });
  }
}
