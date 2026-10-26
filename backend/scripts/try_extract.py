"""
ScamLens CLI Extraction Tester (try_extract.py)
-----------------------------------------------
Quick CLI utility to test AI extraction and pipeline on a local image or text input.
Usage:
    python scripts/try_extract.py <image_path> [--text "optional text"] [--mode mock|cloud|local] [--lang en|ta|hi]
"""

import argparse
import asyncio
import json
import os
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
# Ensure backend root is on sys.path
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.services.pipeline import run_pipeline


async def main():
    parser = argparse.ArgumentParser(
        description="ScamLens CLI Extractor Tester: Run extraction pipeline on image or text."
    )
    parser.add_argument(
        "image_path",
        nargs="?",
        default=None,
        help="Path to screenshot or document image file (PNG, JPEG, WebP).",
    )
    parser.add_argument(
        "--text",
        default=None,
        help="Optional plain text message to analyze.",
    )
    parser.add_argument(
        "--mode",
        choices=["cloud", "local", "mock"],
        default=None,
        help="Execution mode override (cloud, local, mock). Defaults to config MODE.",
    )
    parser.add_argument(
        "--lang",
        choices=["en", "ta", "hi"],
        default="en",
        help="Target explanation language (en, ta, hi). Default: en.",
    )

    args = parser.parse_args()

    if not args.image_path and not args.text:
        parser.error("You must specify either an image_path or --text.")

    image_bytes = None
    filename = None
    if args.image_path:
        if not os.path.exists(args.image_path):
            print(f"Error: Image file not found: {args.image_path}", file=sys.stderr)
            sys.exit(1)
        with open(args.image_path, "rb") as f:
            image_bytes = f.read()
        filename = os.path.basename(args.image_path)
        print(f"Loaded image: {filename} ({len(image_bytes)} bytes)")

    if args.text:
        print(f"Input text: \"{args.text[:80]}...\"" if len(args.text) > 80 else f"Input text: \"{args.text}\"")

    print(f"Running extraction in mode='{args.mode or 'default'}' lang='{args.lang}'...\n")

    try:
        response = await run_pipeline(
            image_bytes=image_bytes,
            filename=filename,
            text=args.text,
            language=args.lang,
            mode=args.mode,
        )

        output_dict = response.model_dump()
        print("=== EXTRACTION RESULT (JSON) ===")
        print(json.dumps(output_dict, indent=2, ensure_ascii=False))
        print("================================")
        print(f"Summary: Band={response.band}, Score={response.score}, DocType={response.extracted.document_type}")
        print(f"Latency: Total={response.timings_ms.get('total')}ms, Extraction={response.timings_ms.get('extraction')}ms")

    except Exception as e:
        print(f"\nExtraction Pipeline Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
