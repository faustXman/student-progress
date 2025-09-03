# Multi-platform support for Raspberry Pi 4B (ARM64) and x86_64
FROM --platform=$BUILDPLATFORM python:3.11-slim-bookworm

# Set build arguments for cross-compilation
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Install system dependencies required for WeasyPrint and ARM compatibility
RUN apt-get update && apt-get install -y \
    # WeasyPrint dependencies
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libffi-dev \
    shared-mime-info \
    # Additional dependencies for ARM builds
    gcc \
    g++ \
    python3-dev \
    build-essential \
    # Clean up to reduce image size (important for Pi's limited storage)
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python packages with optimizations for ARM
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    # Use pre-compiled wheels when available to speed up ARM builds
    pip install --no-cache-dir --find-links https://www.piwheels.org/simple -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Create non-root user for security (good practice for Pi deployments)
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Use entrypoint script for better configuration management
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn"]