FROM python:3.9.16-slim

WORKDIR /app

COPY requirements.txt .
COPY app.py .
COPY run.sh .
COPY models/ models/

RUN pip install -r requirements.txt

# set the start command
ENTRYPOINT ["bash", "run.sh"]
