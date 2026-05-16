FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies into the system Python (no venv needed in container)
RUN uv sync --frozen --no-dev

# Copy source
COPY src/ ./src/

# Create directories that the app expects
RUN mkdir -p data/watch logs

EXPOSE 8000

CMD ["uv", "run", "doc-summarizer", "serve", "--host", "0.0.0.0", "--port", "8000"]
