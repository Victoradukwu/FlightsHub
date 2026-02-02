FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

WORKDIR /app

# System deps for asyncpg / psycopg
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev \
build-essential python3-dev curl bash supervisor && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
# ENV PATH="/root/.local/bin:$PATH"
ENV PATH="/root/.cargo/bin:/root/.local/bin:$PATH"



# Dependency files first (Docker layer caching)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

# Copy application code
COPY . .

EXPOSE 8000

# Create supervisord config to run migrations, FastAPI, and Celery
RUN mkdir -p /etc/supervisor/conf.d
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Run migrations on startup, then start supervisor (FastAPI + Celery)
CMD ["sh", "-c", "uv run alembic upgrade head && supervisord -c /etc/supervisor/conf.d/supervisord.conf"]
