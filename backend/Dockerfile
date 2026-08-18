# =============================================================================
# Stage 1: dependency installer
# We install wheels in a separate layer so the final image cache is efficient.
# =============================================================================
FROM python:3.11-slim AS builder

WORKDIR /app

# System deps needed to compile psycopg2-binary + cryptography wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python deps into a prefix directory
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# =============================================================================
# Stage 2: final runtime image
# =============================================================================
FROM python:3.11-slim AS runtime

# Security: create a non-root user and group
RUN groupadd --gid 1001 appgroup \
 && useradd  --uid 1001 --gid appgroup --no-create-home appuser

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application source (honoring .dockerignore)
COPY . .

# Ensure the entrypoint script is executable
RUN chmod +x /app/entrypoint.sh

# Directories owned by appuser (uploads + structured log files)
RUN mkdir -p /app/uploads /app/logs && chown -R appuser:appgroup /app/uploads /app/logs

# Switch to non-root user
USER appuser

# Expose the port Uvicorn will listen on
# Render injects $PORT at runtime; entrypoint.sh uses ${PORT:-8000} as fallback.
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health', timeout=8)"

ENTRYPOINT ["/app/entrypoint.sh"]
