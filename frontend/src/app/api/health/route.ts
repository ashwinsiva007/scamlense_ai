import { NextResponse } from "next/server";

export async function GET() {
  const backendUrl = process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_API_URL;
  if (backendUrl && !backendUrl.includes("localhost") && !backendUrl.includes("127.0.0.1")) {
    try {
      const resp = await fetch(`${backendUrl}/api/health`, { cache: "no-store" });
      if (resp.ok) {
        return NextResponse.json(await resp.json());
      }
    } catch {
      // fallback to edge config
    }
  }

  const apiKey = process.env.GEMINI_API_KEY || "";
  const hasKey = apiKey.length > 0 && !apiKey.toLowerCase().includes("placeholder") && !apiKey.toLowerCase().includes("your_");

  return NextResponse.json({
    status: "ok",
    mode: hasKey ? "cloud" : "mock",
    model: "gemini-3.1-flash-lite-preview",
    model_name: "gemini-3.1-flash-lite-preview",
    env_file_loaded: hasKey ? "process.env" : "none",
    key_configured: hasKey,
    key_length: hasKey ? apiKey.length : 0,
    sdk_version: "2.33.0-edge",
    process_id: 1,
    started_at: new Date().toISOString(),
    ollama_reachable: false,
    cloud_key_set: hasKey,
  });
}
