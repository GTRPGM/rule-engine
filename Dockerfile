# builder stage
FROM python:3.11-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.5.7 /uv /bin/uv

ENV UV_PROJECT_ENVIRONMENT="/usr/local"

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# final stage
FROM python:3.11-slim-bookworm
LABEL authors="elian118"

ARG APP_PORT
ENV APP_PORT=${APP_PORT}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN useradd -m appuser

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY --chown=appuser:appuser src /app/src

# runtime config
ENV PORT=8060

USER appuser

EXPOSE 8060

HEALTHCHECK --start-period=20s --interval=30s --timeout=3s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; port=os.environ.get('APP_PORT'); urllib.request.urlopen(f'http://localhost:{port}/health')"]

CMD ["python", "src/main.py"]
