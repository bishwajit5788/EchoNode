# EchoNode Persistent Audio Extraction Worker
# Dedicated background worker container with FFmpeg, Python, Node.js, and yt-dlp PO Token Provider.

FROM python:3.12-slim-bookworm

# Prevent python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies: FFmpeg, curl, Node.js runtime for YouTube BotGuard challenges
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Create staging downloads directory
RUN mkdir -p /app/downloads

# Worker configuration
ENV WORKER_HOST="0.0.0.0" \
    WORKER_PORT="8001" \
    DOWNLOADS_DIR="/app/downloads" \
    EXTRACTION_MODE="local"

EXPOSE 8001

CMD ["python", "worker.py"]
