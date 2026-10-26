#!/usr/bin/env python3
"""
ScamLens Gemini API Diagnostic Tool
Loads the application configuration and validates Google Gemini / Gemma connectivity.

Usage:
    python backend/scripts/check_gemini.py
    python backend/scripts/check_gemini.py --list-models

SECURITY NOTE:
    This script NEVER prints, logs, or exposes the actual API key string.
    Only its presence, length, and validation status are reported.
"""

import argparse
import sys
from pathlib import Path

# Add backend directory to path so app modules can be loaded
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings, clean_key, BACKEND_ENV, ROOT_ENV


def parse_args():
    parser = argparse.ArgumentParser(description="Check Google Gemini API configuration and connectivity.")
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available model identifiers accessible with this API key.",
    )
    return parser.parse_args()


def inspect_key_format(key: str) -> str:
    """Provides a safe format inspection without revealing key contents."""
    if not key:
        return "MISSING"
    if key.startswith("AIzaSy"):
        return f"Standard Google AI Studio API Key (AIzaSy..., length {len(key)})"
    if key.startswith("AQ.") or key.startswith("AQ"):
        return f"Google Cloud Service / Token format (AQ..., length {len(key)})"
    return f"Custom / Unknown format (length {len(key)})"


def check_sdk_version() -> str:
    try:
        import google.genai
        return getattr(google.genai, "__version__", "installed (version unknown)")
    except ImportError:
        return "NOT INSTALLED"


def main():
    args = parse_args()
    print("=" * 60)
    print("  ScamLens Gemini API Configuration & Connectivity Diagnostic")
    print("=" * 60)

    # 1. Config & File Resolution
    print(f"\n[1] Environment Files Inspected:")
    print(f"  - backend/.env: {'EXISTS' if BACKEND_ENV.is_file() else 'NOT FOUND'} ({BACKEND_ENV})")
    print(f"  - root .env:    {'EXISTS' if ROOT_ENV.is_file() else 'NOT FOUND'} ({ROOT_ENV})")
    print(f"  - Operating MODE: {settings.MODE}")
    print(f"  - Configured Model (GEMMA_MODEL): {settings.GEMMA_MODEL}")

    # 2. Key Status
    key = clean_key(settings.GEMINI_API_KEY)
    key_present = bool(key and len(key) > 8)
    sdk_version = check_sdk_version()

    print(f"\n[2] Key & SDK Status:")
    print(f"  - Key present:    {key_present}")
    print(f"  - Key length:     {len(key) if key_present else 0}")
    print(f"  - Format type:    {inspect_key_format(key)}")
    print(f"  - google-genai:   {sdk_version}")

    if not key_present:
        print("\n[!] ERROR: GEMINI_API_KEY is not configured or is empty.")
        print("    Please add your API key to backend/.env like this:")
        print("      GEMINI_API_KEY=AIzaSy...")
        print("    You can get a free key in 30 seconds at: https://aistudio.google.com")
        sys.exit(1)

    # 3. Initialize Google GenAI Client
    try:
        from google import genai
        client = genai.Client(api_key=key)
    except Exception as e:
        print(f"\n[!] Failed to initialize google-genai client: {e}")
        sys.exit(1)

    # 4. Handle --list-models
    if args.list_models:
        print(f"\n[3] Querying available models from Google AI Studio...")
        try:
            models_pager = client.models.list()
            available = []
            for m in models_pager:
                name = m.name.replace("models/", "") if hasattr(m, "name") else str(m)
                methods = getattr(m, "supported_generation_methods", []) or getattr(m, "supported_actions", [])
                available.append((name, getattr(m, "display_name", "") or name))

            print(f"    Found {len(available)} accessible model(s):\n")
            gemma_models = []
            gemini_models = []
            for name, display in available:
                if "gemma" in name.lower():
                    gemma_models.append((name, display))
                else:
                    gemini_models.append((name, display))

            if gemma_models:
                print("  === Recommended Gemma Models (Open Source) ===")
                for name, display in gemma_models:
                    print(f"    * {name}")
                print()

            print("  === Available Gemini Models ===")
            for name, display in gemini_models[:15]:
                print(f"    * {name}")
            if len(gemini_models) > 15:
                print(f"    * ... and {len(gemini_models) - 15} more.")

            print("\n  To use one of these models, set in backend/.env:")
            print(f"    GEMMA_MODEL={gemma_models[0][0] if gemma_models else 'gemini-3-flash-preview'}")
            return
        except Exception as e:
            err_msg = str(e)
            print(f"\n[!] Failed to list models: {err_msg}")
            _diagnose_error(err_msg, sdk_version, key)
            sys.exit(1)

    # 5. Make a small text test request
    target_model = settings.GEMMA_MODEL
    print(f"\n[3] Testing small text request to model: '{target_model}'...")

    try:
        response = client.models.generate_content(
            model=target_model,
            contents="Say 'OK' in one word.",
        )
        if response and response.text:
            cleaned_resp = response.text.strip().replace("\n", " ")
            print(f"\n[+] SUCCESS! Model '{target_model}' responded successfully:")
            print(f"    Response snippet: \"{cleaned_resp[:60]}\"")
            print("\n    Your Gemini Cloud API configuration is working properly!")
        else:
            print("\n[!] Model returned an empty response.")
    except Exception as e:
        err_msg = str(e)
        print(f"\n[-] ERROR calling model '{target_model}':")
        _diagnose_error(err_msg, sdk_version, key)
        sys.exit(1)


def _diagnose_error(err_msg: str, sdk_version: str, key: str):
    lower_err = err_msg.lower()

    if "401" in lower_err or "403" in lower_err or "api_key" in lower_err or "permission_denied" in lower_err:
        print("\n  Category: AUTHENTICATION / PERMISSION ERROR (HTTP 401 / 403)")
        print("  Possible causes:")
        print("  1. The API key may be invalid, revoked, or expired.")
        if not key.startswith("AIzaSy"):
            print("  2. Note: Your key does NOT begin with 'AIzaSy'. Standard Google AI Studio")
            print("     keys start with 'AIzaSy...'. If you generated this key from another Google")
            print("     service or Vertex AI, verify that the Generative Language API is enabled.")
        print("  3. To generate a fresh, free AI Studio key in 30 seconds:")
        print("     Visit: https://aistudio.google.com/app/apikey")
        print(f"  Installed google-genai version: {sdk_version}")

    elif "404" in lower_err or "not found" in lower_err or "no longer available" in lower_err:
        print("\n  Category: MODEL NOT FOUND (HTTP 404)")
        print(f"  Error details: {err_msg}")
        print("  The specified model is either deprecated or not available to this API key.")
        print("  Run this script with --list-models to see all valid model names:")
        print("    python backend/scripts/check_gemini.py --list-models")

    elif "429" in lower_err or "resource_exhausted" in lower_err or "quota" in lower_err:
        print("\n  Category: RATE LIMIT / QUOTA EXCEEDED (HTTP 429)")
        print(f"  Error details: {err_msg}")
        print("  The API quota has been reached. You can either wait a moment, or switch to")
        print("  offline local mode (Ollama) in settings: MODE=local")

    elif any(x in lower_err for x in ["connect", "network", "getaddrinfo", "dns", "ssl", "timeout"]):
        print("\n  Category: NETWORK / CONNECTIVITY ERROR")
        print(f"  Error details: {err_msg}")
        print("  Unable to reach Google API endpoints. Please check internet access or firewall.")

    elif "500" in lower_err or "503" in lower_err or "internal" in lower_err:
        print("\n  Category: GOOGLE SERVICE TEMPORARY ERROR (HTTP 500 / 503)")
        print(f"  Error details: {err_msg}")
        print("  Google AI Studio returned a temporary internal error. Retrying usually resolves this,")
        print("  or check if the model requires specific prompt formatting.")

    else:
        print(f"\n  Category: UNEXPECTED ERROR: {err_msg}")


if __name__ == "__main__":
    main()
