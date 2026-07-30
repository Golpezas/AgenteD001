# ──────────────────────────────────────────────
# Backend Dockerfile — Multi-stage
# ──────────────────────────────────────────────
# Stage 1: Builder — solo Chromium
# Stage 2: Runtime — dependencias Python + app
# ──────────────────────────────────────────────

# Stage 1: Builder (Chromium)
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Chromium runtime libraries + dependencias Python
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

# Copiar Chromium desde builder
COPY --from=builder /usr/bin/chromium /usr/bin/chromium
COPY --from=builder /usr/bin/chromedriver /usr/bin/chromedriver

# Instalar dependencias Python directo en runtime
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la app
COPY backend/app/ ./app/
COPY backend/alembic.ini .
COPY backend/migrations/ ./migrations/
COPY backend/seed/ ./seed/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
