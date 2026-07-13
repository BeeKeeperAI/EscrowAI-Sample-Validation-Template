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

## Supported File Extensions and MIME Types

The supported file types are grouped by category below for easier maintenance and readability.

## Document Formats

| File Type | Extensions | MIME Type |
|-----------|------------|-----------|
| PDF | .pdf | application/pdf |
| JSON | .json | application/json |
| XML | .xml | application/xml |
| Plain Text | .txt | text/plain |

## Image Formats

| File Type | Extensions | MIME Type |
|-----------|------------|-----------|
| JPEG Image | .jpg, .jpeg | image/jpeg |
| PNG Image | .png | image/png |
| Bitmap Image | .bmp | image/bmp |