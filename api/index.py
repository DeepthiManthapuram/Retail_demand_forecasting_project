# api/index.py — Minimal Self-Contained App for Diagnostic

from fastapi import FastAPI
import sys
import os

app = FastAPI(title="Diagnostic App")

@app.get("/health")
@app.get("/")
def health():
    return {
        "status": "ok",
        "message": "minimal self-contained app is running!",
        "python_version": sys.version,
        "cwd": os.getcwd(),
        "sys_path": sys.path,
        "env_keys": list(os.environ.keys()),
    }
