# Diabetes Analysis in R - EscrowAI Example

This example demonstrates how to perform correlation analysis on diabetes datasets within EscrowAI's secure enclave environment using R. The application analyzes diabetes data and generates correlation reports while maintaining data privacy and security.

## Prerequisites

### Knowledge Requirements
- Understanding of Docker container build system ([Docker getting-started tutorial](https://docs.docker.com/get-started/) recommended)
- Basic R programming knowledge
- Familiarity with statistical correlation analysis

### Technical Requirements
- R (version 3.6 or higher)
- Docker Version 20+
- Bash shell

### Data Requirements
- Diabetes dataset (example available at: https://www.kaggle.com/datasets/saurabh00007/diabetescsv)
- Dataset should be accessible via SAS URL for enclave execution
- SAS URL for accessing blob storage containing the diabetes dataset

### Environment Variables
The application requires the following environment variables:

- **`SAS_URL`** (Required): Shared Access Signature URL for accessing your blob storage containing the diabetes dataset
- **`ENCLAVE_URL`** (Optional): EscrowAI enclave API endpoint. Defaults to `https://enclaveapi.escrow.beekeeperai.com/` if not provided

## What This Example Does

This example uses BeeKeeperAI's EnclaveAPI to securely analyze diabetes data within a trusted execution environment. The application:

1. Fetches diabetes dataset from secure storage
2. Performs correlation analysis using R statistical functions
3. Generates comprehensive correlation reports
4. Validates output against predefined schema requirements
5. Posts results securely through the EnclaveAPI

## Files in This Example

1. **`Dockerfile`** - Container environment configuration for R and dependencies
2. **`run.sh`** - Entry point script that launches the R application
3. **`app.R`** - Main R script that performs correlation analysis using EnclaveAPI
4. **`corr.R`** - Correlation function implementation and statistical utilities
5. **`requirements.txt`** - R package dependencies (if applicable)
6. **`schema.json`** - Validation criteria for output reports ensuring data quality

## How to Run This Example

### Option 1: Local Development
For testing the R application locally before enclave deployment:

```bash
# Install R dependencies (if running outside Docker)
# R packages are installed automatically by the script

# Set environment variables (replace with your actual values)
export ENCLAVE_URL="https://enclaveapi.escrow.beekeeperai.com"
export SAS_URL="your_sas_url_here"

# Run the application
bash run.sh
```

**Important**: When running locally, you must provide:
- `SAS_URL`: The Shared Access Signature URL for accessing your diabetes dataset in blob storage
- `ENCLAVE_URL`: The EscrowAI enclave API endpoint (defaults to sandbox if not provided)

### Option 2: Docker Container
Build and run the containerized version:

```bash
# Build the Docker image
docker build -t diabetes-analysis-r .

# Run the container with environment variables
docker run --rm \
  -e ENCLAVE_URL="https://enclaveapi.escrow.beekeeperai.com" \
  -e SAS_URL="your_sas_url_here" \
  diabetes-analysis-r
```

**Important**: When running in Docker, you must pass the environment variables:
- `-e SAS_URL="your_sas_url_here"`: Replace with your actual SAS URL for blob storage access
- `-e ENCLAVE_URL="https://enclaveapi.escrow.beekeeperai.com"`: The EscrowAI API endpoint

### Option 3: EscrowAI Enclave
For production deployment in the secure enclave:

1. **Prepare files for encryption**: Encrypt sensitive files (do NOT encrypt `Dockerfile` and `run.sh`)
2. **Package the algorithm**: Create a zip file with all components
3. **Upload to EscrowAI**: Use the EscrowAI platform to upload your encrypted package
4. **Execute**: Run the analysis within the trusted execution environment

## Expected Results

Upon successful execution, you should see:
- Data loading confirmation messages
- Correlation analysis progress indicators
- Statistical correlation results
- Schema validation success confirmation
- Final report submission status

## Troubleshooting

- **SAS URL issues**: 
  - Ensure the `SAS_URL` environment variable is properly set and contains a valid Shared Access Signature URL
  - Verify that the SAS URL has read and list permissions for the blob storage container
  - Check that the SAS URL has not expired
  - Confirm the diabetes dataset is properly uploaded to the blob storage
- **R package errors**: Ensure all required R packages are installed and compatible
- **Docker build failures**: Check that Docker daemon is running and you have sufficient permissions
- **Schema validation errors**: Review the output format against the `schema.json` requirements
- **Environment variable errors**: Ensure all required environment variables (`SAS_URL`) are set before running the application