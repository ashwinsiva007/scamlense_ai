import { NextResponse } from "next/server";

export async function GET() {
  const apiKey = process.env.GEMINI_API_KEY || "";
  const hasKey = apiKey.length > 8 && !apiKey.toLowerCase().includes("placeholder") && !apiKey.toLowerCase().includes("your_");

  return NextResponse.json({
    status: "ok",
    mode: hasKey ? "cloud" : "mock",
    model: "gemini-3.5-flash",
    model_name: "gemini-3.5-flash",
    key_configured: hasKey,
    key_length: hasKey ? apiKey.length : 0,
    sdk_version: "2.33.0-edge",
    ollama_reachable: false,
    cloud_key_set: hasKey,
  });
}
