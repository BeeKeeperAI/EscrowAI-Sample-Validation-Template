FROM python:3.12-slim AS bkstart

RUN apt-get update

WORKDIR /app

RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt  .

RUN pip install uv && uv pip install -r requirements.txt --python `which python`

### BEEKEEPER START LOGIC ENDS HERE ###

############################################################################################

### YOUR DOCKERFILE STEPS BEGIN BELOW
FROM python:3.12-slim

WORKDIR /app

COPY --from=bkstart /opt/venv /opt/venv

COPY . .

ENV PATH="/opt/venv/bin:$PATH" RUNTIME_SELFSIGNED_CERTS=true

# set the start command
ENTRYPOINT ["bash", "run.sh"]