FROM python:3.12.15-slim-bookworm AS build
COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Same base as build: the venv's python symlinks to /usr/local/bin/python3.12.
FROM python:3.12.15-slim-bookworm
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" DATA_DIR=/data TZ=Asia/Seoul PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
COPY --from=build /app/.venv /app/.venv
# Full Chromium only (1.48 has no separate headless shell); --headless=new keeps its ECH.
RUN playwright install --with-deps chromium && rm -rf /var/lib/apt/lists/*
COPY app ./app

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
