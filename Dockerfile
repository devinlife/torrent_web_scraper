FROM mcr.microsoft.com/playwright/python:v1.48.0-noble
COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /usr/local/bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH" DATA_DIR=/data TZ=Asia/Seoul
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY app ./app

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
