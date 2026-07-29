# ──────────────────────────────────────────────
# Backend Dockerfile — Multi-stage
# ──────────────────────────────────────────────
# Stage 1: Instalar dependencias + Chromium
# Stage 2: Copiar solo lo necesario → imagen slim
# ──────────────────────────────────────────────

# Stage 1: Builder
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Instalar Chromium para pixelshot (PixelRAG)
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime (slim)
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_DIR=/app \
    PATH="/root/.local/bin:$PATH"

# Chromium runtime libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Copiar site-packages y app desde builder
COPY --from=builder /root/.local /root/.local
COPY --from=builder /usr/bin/chromium /usr/bin/chromium
COPY --from=builder /usr/bin/chromedriver /usr/bin/chromedriver

WORKDIR /app
COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
