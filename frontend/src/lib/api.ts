export type Band = "low_risk" | "suspicious" | "likely_scam" | "insufficient_info";
export type Confidence = "high" | "medium" | "low";
export type Language = "en" | "ta" | "hi";
export type Mode = "cloud" | "local" | "mock";
export type SignalSource = "rule" | "tool" | "model";
export type ToolStatus = "ok" | "warn" | "error" | "skipped";

export interface ExtractedData {
  document_type: string;
  sender: string | null;
  message_text: string;
  urls: string[];
  phone_numbers: string[];
  upi_ids: string[];
  amounts: string[];
  claimed_brand: string | null;
  detected_language: string;
  image_quality: string;
  visual_notes: string[];
}

export interface Signal {
  id: string;
  label: string;
  category: string;
  weight: number;
  evidence: string;
  source: SignalSource;
}

export interface ToolResult {
  tool: string;
  target: string;
  status: ToolStatus;
  detail: string;
}

export interface FamilyAlert {
  title: string;
  body: string;
  tips: string[];
}

export interface AnalyzeResponse {
  request_id: string;
  band: Band;
  score: number;
  confidence: Confidence;
  scam_type: string | null;
  language: Language;
  extracted: ExtractedData;
  signals: Signal[];
  tool_results: ToolResult[];
  explanation: string;
  next_steps: string[];
  family_alert: FamilyAlert;
  limitations: string;
  mode: Mode;
  timings_ms: Record<string, number>;
}

export interface HealthResponse {
  status: string;
  mode: string;
  model: string;
  model_name?: string;
  key_configured?: boolean;
  key_length?: number;
  sdk_version?: string;
  ollama_reachable: boolean;
  cloud_key_set: boolean;
}

export interface BenchmarksResponse {
  dataset_version: string;
  total_eval_samples: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  false_positive_rate?: number;
  average_latency_ms: number;
  rule_packs_loaded: number;
  last_updated: string;
  confusion_matrix?: {
    tp: number;
    fp: number;
    tn: number;
    fn: number;
  };
  comparison?: {
    llm_only: Record<string, any>;
    scamlens_hybrid: Record<string, any>;
  };
  per_language?: Record<string, any>;
}

export function getApiBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  // In the browser
  if (typeof window !== "undefined") {
    // If running locally, direct API requests to FastAPI on port 8000
    if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
      return "http://localhost:8000";
    }
    // On Vercel or cloud multi-service, relative /api rewrites to backend service
    return "";
  }
  return "http://localhost:8000";
}

export class ApiNetworkError extends Error {
  isNetworkError = true;
  constructor(message: string) {
    super(message);
    this.name = "ApiNetworkError";
  }
}

export class ApiRateLimitError extends Error {
  isRateLimit = true;
  constructor(message: string) {
    super(message);
    this.name = "ApiRateLimitError";
  }
}

export async function analyzeMessage(params: {
  image?: File | null;
  text?: string;
  language?: Language;
  mode?: Mode;
}): Promise<AnalyzeResponse> {
  const isForcedDemo = process.env.NEXT_PUBLIC_DEMO_MODE === "true";
  if (isForcedDemo) {
    // If demo mode is forced via env, load sample based on text hints or default to internship
    return loadDemoResult("internship", params.language || "en");
  }

  const formData = new FormData();
  if (params.image) {
    formData.append("image", params.image);
  }
  if (params.text && params.text.trim()) {
    formData.append("text", params.text.trim());
  }
  if (params.language) {
    formData.append("language", params.language);
  }
  if (params.mode) {
    formData.append("mode", params.mode);
  }

  try {
    const response = await fetch(`${getApiBaseUrl()}/api/analyze`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      if (response.status === 429) {
        let rateLimitDetail = "Rate limit reached. Please wait a minute before analyzing another document.";
        try {
          const errorJson = (await response.json()) as { detail?: string };
          if (errorJson.detail) {
            rateLimitDetail = errorJson.detail;
          }
        } catch {
          // ignore JSON parse error
        }
        throw new ApiRateLimitError(rateLimitDetail);
      }
      let errorDetail = "Failed to analyze input";
      try {
        const errorJson = (await response.json()) as { detail?: string };
        errorDetail = errorJson.detail || errorDetail;
      } catch {
        // ignore JSON parse error
      }
      throw new Error(errorDetail);
    }

    return (await response.json()) as AnalyzeResponse;
  } catch (err: unknown) {
    if (err instanceof ApiRateLimitError) {
      throw err;
    }
    if (err instanceof TypeError && (err.message.includes("fetch") || err.message.includes("network") || err.message.includes("Failed to fetch"))) {
      throw new ApiNetworkError("Cannot connect to ScamLens API server. You can switch to Demo Mode to test offline samples.");
    }
    throw err instanceof Error ? err : new Error(String(err));
  }
}

export async function loadDemoResult(
  sampleKey: "internship" | "payment" | "kyc",
  language: Language
): Promise<AnalyzeResponse> {
  const filename = `/demo/sample_${sampleKey}_${language}.json`;
  const response = await fetch(filename);
  if (!response.ok) {
    // fallback to English
    const fallbackResponse = await fetch(`/demo/sample_${sampleKey}_en.json`);
    if (!fallbackResponse.ok) {
      throw new Error(`Failed to load demo fixture: ${filename}`);
    }
    return (await fallbackResponse.json()) as AnalyzeResponse;
  }
  return (await response.json()) as AnalyzeResponse;
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/health`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Health check failed");
  }
  return (await response.json()) as HealthResponse;
}

export async function getBenchmarks(): Promise<BenchmarksResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/benchmarks`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Failed to fetch benchmarks");
  }
  return (await response.json()) as BenchmarksResponse;
}
