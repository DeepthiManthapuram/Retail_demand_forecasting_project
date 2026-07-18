# ============================================================
# Dockerfile — Retail Demand Forecasting Backend
# ============================================================
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (for Prophet / LightGBM)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libstdc++6 libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# Create necessary directories
RUN mkdir -p datasets saved_models logs reports

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the FastAPI application
CMD ["uvicorn", "backend.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--log-level", "info"]
