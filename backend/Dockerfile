# syntax=docker/dockerfile:1

# ---- build: resolve and install dependencies into /app/.venv ------------------------
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.8 /uv /bin/uv

# Compile bytecode now, because the runtime user cannot write next to the sources.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Dependencies change far less often than code: installing them in their own layer
# lets Docker reuse it across code-only rebuilds.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

COPY alembic.ini ./
COPY src ./src

# ---- runtime: same Python, no uv or build cache, unprivileged user ------------------
FROM python:3.12-slim AS runtime

RUN useradd --system --uid 10001 --no-create-home app

WORKDIR /app
COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER app
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

# Apply pending migrations before serving, so the schema always matches the code.
# exec hands PID 1 to uvicorn so it receives SIGTERM and shuts down gracefully.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn src.infrastructure.fastapi.main:create_app --factory --host 0.0.0.0 --port 8000"]
