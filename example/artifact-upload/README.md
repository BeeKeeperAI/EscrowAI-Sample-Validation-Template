# bk-demo-artifact-upload — Escrow artifact upload example

This repository demonstrates how to upload artifacts to an escrow project. Use it as a reference for building a container, and sending artifacts to escrow via the Enclave API.

## Repository contents

- `app.py` — example script that performs artifact upload.
- `Dockerfile` — container image build for the example.
- `run.sh` — container entrypoint used by the image.
- `requirements.txt` — Python dependencies for local runs.

## Goal

Show, end-to-end, how to:

- Package a validator into a container
- Upload one or more artifacts to an escrow/enclave project

## Prerequisites

- Docker (to build and run the container)
- Python 3.8+ 


Never check secrets into source control. Use CI secret stores or environment variables.


## Files to inspect

- `app.py` — HTTP client and artifact/report posting logic
- `run.sh` / `Dockerfile` — container start and runtime config

## License

Provided as an example template for escrow / Enclave integration.