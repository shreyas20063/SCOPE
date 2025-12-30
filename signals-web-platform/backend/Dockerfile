# Multi-stage build for production-optimized Python backend
# Stage 1: Builder - install dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install to user directory
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt
RUN pip install --user --no-cache-dir gunicorn

# Stage 2: Production - minimal runtime image
FROM python:3.11-slim

WORKDIR /app

# Create non-root user for security
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY . .

# Set ownership
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Set environment variables
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run gunicorn with uvicorn workers for production
# 4 workers recommended for 100 concurrent users
CMD ["gunicorn", "main:app", \
    "--workers", "4", \
    "--worker-class", "uvicorn.workers.UvicornWorker", \
    "--bind", "0.0.0.0:8000", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--timeout", "120", \
    "--keep-alive", "5", \
    "--graceful-timeout", "30"]
