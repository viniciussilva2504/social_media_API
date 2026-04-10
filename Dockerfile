# ── Stage 1: builder ─────────────────────────────────────────────
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    build-essential gcc libpq-dev libjpeg-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt ./
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ── Stage 2: runtime ────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Runtime-only C libs (no compilers)
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    libpq5 libjpeg62-turbo zlib1g \
    && rm -rf /var/lib/apt/lists/*

# Copy the pre-built virtualenv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Non-root user
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app
COPY . /app/

RUN SECRET_KEY=build-placeholder DEBUG=1 python manage.py collectstatic --noinput

# Own media directory
RUN mkdir -p /app/media && chown -R app:app /app/media

USER app

EXPOSE 8000

CMD ["gunicorn", "social_media.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "--max-requests", "1000", "--max-requests-jitter", "50"]

EXPOSE 8000

CMD ["gunicorn", "social_media.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "--max-requests", "1000", "--max-requests-jitter", "50", "--access-logfile", "-"]
