FROM python:3.12-slim

RUN apt update && \
    apt install -y gcc python3-dev curl

WORKDIR /app

COPY requirements.txt .
COPY training.py .
COPY run.sh .
COPY *.bkenc .

# Obtain the resnet model for the container because egress is not allowed in the enclave
RUN curl https://download.pytorch.org/models/resnet101-5d3b4d8f.pth --output resnet101.pth 

RUN pip install uv && uv pip install -r requirements.txt --python `which python`

# Make the run.sh script executable
RUN chmod +x run.sh

# set the start command
ENTRYPOINT ["./run.sh"]
