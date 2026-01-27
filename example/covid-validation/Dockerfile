FROM python:3.9.16-slim

WORKDIR /app

# Install system dependencies first (rarely changes)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    dos2unix \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements FIRST (before copying code)
# This allows Docker to cache the pip install layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files (changes frequently, so put last)
COPY *.py .
COPY run.sh .
COPY *.bkenc .
COPY models/ models/
COPY *.yaml . 

# Fix line endings in run.sh
RUN dos2unix run.sh

# set the start command
ENTRYPOINT ["bash", "run.sh"]
