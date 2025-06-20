# COVID-19 Chest X-Ray Analysis - EscrowAI Example

This example demonstrates how to perform COVID-19 diagnosis using deep learning models on chest X-ray images within EscrowAI's secure enclave environment. The application downloads chest X-ray images, applies a pre-trained COVID-19 detection model, and generates diagnostic reports while maintaining data privacy.

## Prerequisites

### Knowledge Requirements
- Understanding of Docker container build system ([Docker getting-started tutorial](https://docs.docker.com/get-started/) recommended)
- Basic Python programming knowledge
- Familiarity with machine learning and image classification concepts

### Technical Requirements
- Python 3.8 or higher
- Docker Version 20+
- Bash shell

### Data Requirements
- Chest X-ray images (automatically downloaded within the enclave)
- Pre-trained COVID-19 detection model (included in the package)
- SAS URL for accessing blob storage containing the X-ray images

### Environment Variables
The application requires the following environment variables:

- **`SAS_URL`** (Required): Shared Access Signature URL for accessing your blob storage containing chest X-ray images
- **`ENCLAVE_URL`** (Optional): EscrowAI enclave API endpoint. Defaults to `https://enclaveapi.escrow.beekeeperai.com/` if not provided

## What This Example Does

This example creates a container that operates within a Trusted Execution Environment to:

1. Download chest X-ray images securely using the EnclaveSDK
2. Load a pre-trained deep learning model for COVID-19 detection
3. Process the X-ray images through the diagnostic model
4. Generate classification results (COVID-19 positive/negative)
5. Create a comprehensive validation report with model performance metrics
6. Post results securely through the EnclaveAPI

## Files in This Example

1. **`Dockerfile`** - Container environment configuration specifying the runtime environment for the enclave
2. **`run.sh`** - Entry point script that starts the application in the Trusted Execution Environment
3. **`app.py`** - Main Python script that uses EnclaveSDK to access secrets, process X-ray images, and generate reports
4. **`models/multi-class-pg.pkl`** - Pre-trained COVID-19 detection model (encrypted secret)
5. **`requirements.txt`** - Python package dependencies needed to run the application
6. **`schema.json`** - Validation criteria file that enforces strict output requirements for the final report

## How to Run This Example

### Option 1: Local Development
For testing the application locally before enclave deployment:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (replace with your actual values)
export ENCLAVE_URL="https://enclaveapi.escrow.beekeeperai.com/"
export SAS_URL="your_sas_url_here"

# Run the Python application directly
python app.py
```

**Important**: When running locally, you must provide:
- `SAS_URL`: The Shared Access Signature URL for accessing your data in the blob storage
- `ENCLAVE_URL`: The EscrowAI enclave API endpoint (defaults to sandbox if not provided)

Note: Local execution will use the provided SAS URL to access real data, but may have limited functionality compared to enclave execution.

### Option 2: Docker Container
Build and test the containerized version:

```bash
# Build the Docker image
docker build -t covid-validation .

# Run the container with environment variables
docker run --rm \
  -e ENCLAVE_URL="https://enclaveapi.escrow.beekeeperai.com/" \
  -e SAS_URL="your_sas_url_here" \
  covid-validation
```

**Important**: When running in Docker, you must pass the environment variables:
- `-e SAS_URL="your_sas_url_here"`: Replace with your actual SAS URL for blob storage access
- `-e ENCLAVE_URL="https://enclaveapi.escrow.beekeeperai.com/"`: The EscrowAI API endpoint

### Option 3: EscrowAI Enclave
For production deployment in the secure enclave:

1. **Prepare files for encryption**: Encrypt sensitive files like the model file (`models/multi-class-pg.pkl`) and `app.py` if desired. Do NOT encrypt `Dockerfile` and `run.sh`
2. **Package the algorithm**: Create a zip file containing all components
3. **Upload to EscrowAI**: Use the EscrowAI platform to upload your encrypted package
4. **Execute**: Run the COVID-19 validation within the trusted execution environment

## Expected Results

Upon successful execution, you should see:
- Image download and preprocessing progress
- Model loading confirmation
- Classification results for each processed X-ray image
- Performance metrics and validation statistics
- Schema validation success confirmation
- Final diagnostic report submission status

## Troubleshooting

- **SAS URL issues**: 
  - Ensure the `SAS_URL` environment variable is properly set and contains a valid Shared Access Signature URL
  - Verify that the SAS URL has read and list permissions for the blob storage container
  - Check that the SAS URL has not expired
- **Model loading errors**: Ensure the `multi-class-pg.pkl` file is properly encrypted and accessible
- **Image processing failures**: Verify that the input images are in the correct format and accessible
- **Docker build issues**: Check that all dependencies in `requirements.txt` are compatible
- **Schema validation errors**: Review the output format against the `schema.json` requirements
- **EnclaveSDK connection issues**: Verify that the enclave environment is properly configured
- **Environment variable errors**: Ensure all required environment variables (`SAS_URL`) are set before running the application
