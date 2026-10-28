# Production Dockerfile for Backend and Blender Headless Execution
FROM ubuntu:22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies, Python 3, pip, numpy, and headless Blender
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    python3-dev \
    python3-numpy \
    blender \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set up backend app directory
WORKDIR /app

# Install Python requirements
COPY backend/requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy source trees
COPY backend ./backend
COPY blender ./blender
COPY shared ./shared

ENV BLENDER_PATH=/usr/bin/blender
ENV STORAGE_TYPE=local
ENV LOCAL_STORAGE_DIR=/app/storage_data
ENV PYTHONPATH=/app

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
