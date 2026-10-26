import os
import sys

# Ensure backend directory is in Python module search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

# Export app for Vercel and ASGI runners
__all__ = ["app"]
