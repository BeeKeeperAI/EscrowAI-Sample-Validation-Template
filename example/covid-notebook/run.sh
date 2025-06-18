#!/bin/sh

set -e

# Convert notebook to script
jupyter nbconvert --to script app.ipynb

# Check if conversion was successful
if [ ! -f "app.py" ]; then
    echo "Error: Failed to convert notebook to app.py"
    exit 1
fi

python3 app.py