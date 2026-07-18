# api/index.py — Vercel Serverless Entrypoint for FastAPI backend

import sys
import os
from pathlib import Path

# Add project root to sys.path for serverless imports
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Import FastAPI app from backend.main
from backend.main import app
