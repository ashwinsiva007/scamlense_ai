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
  average_latency_ms: number;
  rule_packs_loaded: number;
  last_updated: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function analyzeMessage(params: {
  image?: File | null;
  text?: string;
  language?: Language;
  mode?: Mode;
}): Promise<AnalyzeResponse> {
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

  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let errorDetail = "Failed to analyze input";
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/health`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Health check failed");
  }
  return response.json();
}

export async function getBenchmarks(): Promise<BenchmarksResponse> {
  const response = await fetch(`${API_BASE_URL}/api/benchmarks`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Failed to fetch benchmarks");
  }
  return response.json();
}
