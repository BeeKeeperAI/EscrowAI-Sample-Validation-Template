FROM python:3.12-slim

WORKDIR /app

COPY . .

COPY requirements.txt  .

RUN pip install -U pip setuptools && pip install -r requirements.txt

# Make the run.sh script executable
RUN chmod +x run.sh

# set the start command
ENTRYPOINT ["./run.sh"]