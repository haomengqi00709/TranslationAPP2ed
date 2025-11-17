# Multi-stage Docker build for PowerPoint Translation API

# Stage 1: Build fast_align (C++ component)
FROM ubuntu:22.04 AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy fast_align source
WORKDIR /build
COPY ../fast_align ./fast_align

# Build fast_align
WORKDIR /build/fast_align
RUN mkdir -p build && cd build && \
    cmake .. && \
    make -j$(nproc)


# Stage 2: Python runtime
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy fast_align binaries from builder
COPY --from=builder /build/fast_align/build/fast_align /usr/local/bin/
COPY --from=builder /build/fast_align/build/atools /usr/local/bin/

# Copy Python requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads output temp logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run API server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
