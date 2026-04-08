# ─── SecureCodeEnv Dockerfile ────────────────────────────────────────────────
# Base: python:3.11-slim — minimal, fast, secure
# Port: 7860 — HuggingFace Spaces standard port
# Security: Non-root user, no network for agent subprocesses
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# Install system dependencies for bandit + compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer cache optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security (best practice — agent code runs as appuser)
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

USER appuser

# HuggingFace Spaces requires port 7860
EXPOSE 7860

# Health check — hackathon automated ping checks /health
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health')"

# 2 workers for concurrency (stateless sessions support this)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "2"]
