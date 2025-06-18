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

1. Edit the `run.sh` script to include your SAS URL for data access
2. Run the application:
   ```bash
   bash run.sh
   ```

### Option 2: Docker Container
Build and run the containerized version:

```bash
# Build the Docker image
docker build -t diabetes-analysis-r .

# Run the container
docker run --rm diabetes-analysis-r
```

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

- **Data access issues**: Verify your SAS URL is correctly configured and has appropriate permissions
- **R package errors**: Ensure all required R packages are installed and compatible
- **Docker build failures**: Check that Docker daemon is running and you have sufficient permissions
- **Schema validation errors**: Review the output format against the `schema.json` requirements