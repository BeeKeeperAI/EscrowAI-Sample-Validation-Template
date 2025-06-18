#!/bin/sh

# Report errors immediately to the enclave and exit
set -e

if [ -n "$RUN_NOTEBOOK" ]; then
    # Convert and execute notebook
    jupyter nbconvert --to script app.ipynb
    python3 app.py
else
    # Run the original script
    python3 app.py
fi