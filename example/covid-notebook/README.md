# An Example of COVID Inference in EscrowAI

This example demonstrates how to use BeeKeeperAI's EscrowAI platform to validate a COVID-19 diagnosis model using chest x-ray images. The code can be run either locally for development/testing or deployed to EscrowAI for secure execution.

## Repository Contents

This repository includes:
1. `app.ipynb` - Jupyter notebook containing the main analysis code
2. `Dockerfile` - Container configuration for EscrowAI deployment
3. `run.sh` - Script to convert and execute the notebook
4. `requirements.txt` - Python package dependencies
5. `models/multi-class-pg.pkl` - Pre-trained model file
6. `schema.json` - Output validation criteria

## Local Development Setup

### 1. Set up Python Virtual Environment
First, create and activate a Python virtual environment to manage dependencies:
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Unix/MacOS
# or
.venv\Scripts\activate  # On Windows

# Install required packages
pip install -r requirements.txt
```

### 2. Running the Code

You can run this example in two ways:

#### Option 1: Using Jupyter Notebook
This is recommended for development and interactive exploration:
```bash
# Set the SAS_URL environment variable and start Jupyter
SAS_URL='your_sas_url_here' jupyter notebook
```
Then open `app.ipynb` in your browser and run the cells interactively.

#### Option 2: Using run.sh
This method converts the notebook to a Python script and executes it:
```bash
# Set the SAS_URL and execute run.sh
SAS_URL='your_sas_url_here' ./run.sh
```

Note: Replace `your_sas_url_here` with your actual SAS URL from EscrowAI.

## Deploying to EscrowAI

When you're ready to deploy to EscrowAI:

1. Upload this entire directory to the EscrowAI platform
2. The platform will automatically:
   - Use the `Dockerfile` to build the container
   - Execute `run.sh` which converts the notebook and runs the analysis
   - Process the results according to `schema.json`

The `Dockerfile` and `run.sh` handle all the necessary setup and execution in the secure enclave environment.

## What Does This Example Do?

This code:
1. Loads a pre-trained deep learning model for COVID-19 diagnosis
2. Downloads chest x-ray images inside a Trusted Execution Environment
3. Runs the model on these images
4. Generates a validation report with accuracy metrics
5. Outputs results in a format that meets EscrowAI's requirements

## Prerequisites

- Basic understanding of Python and Jupyter notebooks
- Familiarity with virtual environments
- Docker knowledge (for understanding deployment)
- Access to EscrowAI platform and valid SAS URL

For Docker basics, the [getting-started tutorial](https://docs.docker.com/get-started/) on Docker.com is recommended.
