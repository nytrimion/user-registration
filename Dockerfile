# Multi-stage Dockerfile for User Registration API with Poetry

# Stage 1: Base image with Python 3.14
FROM python:3.14-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.8.4 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Add Poetry to PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Set working directory
WORKDIR /app

# Install system dependencies for PostgreSQL driver and Poetry
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    chmod +x $POETRY_HOME/bin/poetry

# Stage 2: Development image
FROM base AS development

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies (including dev dependencies)
RUN poetry install --no-root && \
    rm -rf $POETRY_CACHE_DIR

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application with hot reload
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage 3: Production image
FROM base AS production

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install production dependencies only
RUN poetry install --only main --no-root && \
    rm -rf $POETRY_CACHE_DIR

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copy application code with layer caching optimization
# Order: stable → semi-stable → volatile (maximizes cache hits)
COPY --chown=appuser:appuser scripts/ ./scripts/
COPY --chown=appuser:appuser migrations/ ./migrations/
COPY --chown=appuser:appuser src/ ./src/

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]