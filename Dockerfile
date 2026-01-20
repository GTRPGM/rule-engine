FROM python:3.11-slim-bookworm
LABEL authors="elian118"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache --no-dev --no-install-project
COPY . .
EXPOSE 8050
CMD ["uv", "run", "python", "src/main.py"]
