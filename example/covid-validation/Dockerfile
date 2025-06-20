FROM python:3.9.16-slim

WORKDIR /app

COPY requirements.txt .
COPY *.py .
COPY run.sh .
COPY *.bkenc .
COPY models/ models/

# Install build dependencies and uv
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && pip install uv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Use uv to install requirements
RUN uv pip install --system -r requirements.txt

# set the start command
ENTRYPOINT ["bash", "run.sh"]
