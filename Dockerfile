FROM python:3.11-slim-bookworm
LABEL authors="elian118"

ARG APP_PORT

ENV APP_PORT=${APP_PORT}
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache --no-dev --no-install-project
COPY . .

EXPOSE ${APP_PORT}

HEALTHCHECK --start-period=20s --interval=30s --timeout=3s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; port=os.environ.get('APP_PORT'); urllib.request.urlopen(f'http://localhost:{port}/health')"]

CMD ["uv", "run", "python", "src/main.py"]
