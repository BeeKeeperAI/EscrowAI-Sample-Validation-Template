FROM python:3.9.16-slim

WORKDIR /app

COPY requirements.txt .
COPY *.py .
COPY run.sh .
COPY *.bkenc .
COPY models/ models/

# Ensure the secrets.yaml file is copied to the container when encrypting
COPY *.yaml . 



# Install build dependencies for packages that need compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
RUN pip install -r requirements.txt

# set the start command
ENTRYPOINT ["bash", "run.sh"]
