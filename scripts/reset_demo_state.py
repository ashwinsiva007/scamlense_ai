#!/usr/bin/env python3
"""
ScamLens Demo State Reset Script
--------------------------------
Clears all runtime caches, evaluation caches, rate limit tracking,
and ensures the application is in a pristine state ready for live demonstration.
"""

import os
import shutil
import sys

# Windows UTF-8 stdout configuration
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(repo_root, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


def reset_state():
    print("=" * 60)
    print("🧹 Resetting ScamLens Demo State...")
    print("=" * 60)

    # 1. Clear Eval cache (.cache/)
    eval_cache = os.path.join(backend_dir, "eval", ".cache")
    if os.path.exists(eval_cache):
        try:
            shutil.rmtree(eval_cache)
            os.makedirs(eval_cache, exist_ok=True)
            print("✅ Cleared evaluation disk cache: backend/eval/.cache/")
        except Exception as e:
            print(f"⚠️ Could not clear {eval_cache}: {e}")
    else:
        os.makedirs(eval_cache, exist_ok=True)
        print("✅ Initialized evaluation cache directory.")

    # 2. Reset In-Memory Rate Limiter
    try:
        from app.api.limiter import limiter
        limiter.reset()
        print("✅ Reset in-memory IP rate limiter history.")
    except Exception as e:
        print(f"⚠️ Rate limiter reset note: {e}")

    # 3. Reset Verifier In-Memory Cache
    try:
        from app.services.verifiers import _LOOKUP_CACHE
        _LOOKUP_CACHE.clear()
        print("✅ Cleared external threat intelligence & RDAP in-memory cache.")
    except Exception as e:
        print(f"⚠️ Verifier cache reset note: {e}")

    # 4. Clean Python bytecode caches
    count = 0
    for root, dirs, files in os.walk(backend_dir):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            try:
                shutil.rmtree(pycache_path)
                count += 1
            except Exception:
                pass
    print(f"✅ Purged {count} Python __pycache__ directories.")

    # 5. Verify Rule Packs
    try:
        from scripts.validate_rule_packs import main as validate_main
        print("\n🔍 Validating rule packs...")
        validate_main()
    except Exception as e:
        print(f"⚠️ Rule validation note: {e}")

    print("\n" + "=" * 60)
    print("🎉 Demo state reset complete! System is clean and ready for judging.")
    print("=" * 60)


if __name__ == "__main__":
    reset_state()
