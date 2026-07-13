FROM python:3.9.16-slim

WORKDIR /app

COPY . .

COPY requirements.txt  .

RUN pip install -r requirements.txt

# set the start command - will run either script or notebook based on environment variable
ENTRYPOINT ["bash", "run.sh"]