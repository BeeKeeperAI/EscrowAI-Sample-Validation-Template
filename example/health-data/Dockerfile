FROM python:3.9.16-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    dos2unix \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements first (for layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files (encrypted and config files)
COPY run.sh .
COPY *.bkenc .
COPY *.yaml .
COPY *.json .

# Fix line endings in run.sh
RUN dos2unix run.sh

# Set the start command
ENTRYPOINT ["bash", "run.sh"]
