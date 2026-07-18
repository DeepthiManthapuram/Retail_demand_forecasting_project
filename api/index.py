# api/index.py — Vercel Serverless Entrypoint with Diagnostic Fallback

import sys
import os
import traceback
from pathlib import Path

# Add project root to sys.path for serverless imports
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    # Import FastAPI app from backend.main
    from backend.main import app
except Exception as exc:
    # Fallback FastAPI app to display the import error stack trace
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    
    app = FastAPI(title="Diagnostic Fallback")
    error_tb = traceback.format_exc()
    
    @app.get("/health")
    @app.get("/")
    def diagnostic_error():
        html = f"""
        <html>
            <head><title>Diagnostic Error</title></head>
            <body style="font-family: monospace; padding: 2rem; background: #0f172a; color: #f8fafc;">
                <h1 style="color: #ef4444;">Vercel Startup Error</h1>
                <p>An exception occurred while importing backend.main:</p>
                <pre style="background: #1e293b; padding: 1.5rem; border-radius: 8px; border: 1px solid #334155; overflow-x: auto;">{error_tb}</pre>
            </body>
        </html>
        """
        return HTMLResponse(content=html, status_code=200) # Use 200 so Vercel gateway doesn't block
