# EscrowAI Sample Validation Template

This repository contains sample algorithms demonstrating how to build, test, and deploy machine learning models and data analysis workflows within EscrowAI's secure Trusted Execution Environment (TEE). Each example shows how to run locally for development, in Docker containers for testing, and in EscrowAI enclaves for production.

## Repository Structure

```
EscrowAI-Sample-Validation-Template/
├── algo-template.py          # Basic template algorithm
├── Dockerfile               # Container configuration
├── run.sh                  # Entry point script
├── requirements.txt        # Python dependencies
├── schema.json            # Validation schema
└── example/
    ├── breast-cancer-training/    # PyTorch deep learning training
    ├── covid-validation/          # Image classification inference
    └── diabetes-validation-r/     # R statistical analysis
```

## Prerequisites

### Technical Requirements
- **Python 3.8+** (for local development)
- **Docker 20+** (for containerized testing)
- **R 3.6+** (for R examples)
- **Internet connection** (for downloading dependencies and models)

### EscrowAI Requirements
- EscrowAI platform access
- Understanding of Trusted Execution Environments
- Familiarity with Docker containerization

### Environment Variables
All examples require these environment variables:

- **`ENCLAVE_URL`** (Optional): EscrowAI enclave API endpoint. Defaults to `https://enclaveapi.escrow.beekeeperai.com/`
- **`SAS_URL`** (Required for testing): Shared Access Signature URL for accessing test data in Azure blob storage

## What This Repository Demonstrates

This template repository shows how to:

1. **Package algorithms** for EscrowAI's secure execution environment
2. **Access data securely** using the EnclaveSDK and SAS URLs
3. **Implement validation workflows** with schema enforcement
4. **Handle different programming languages** (Python, R)
5. **Integrate ML frameworks** (PyTorch, scikit-learn)
6. **Track experiments** using MLflow
7. **Deploy in production** within trusted execution environments

## Quick Start Guide

### Step 1: Choose an Example

- **`algo-template.py`**: Basic template for simple data processing
- **`example/breast-cancer-training/`**: Advanced PyTorch training with MLflow
- **`example/covid-validation/`**: Image classification inference
- **`example/diabetes-validation-r/`**: Statistical analysis in R

### Step 2: Set Up Environment

```bash
# Clone the repository
git clone https://github.com/BeeKeeperAI/EscrowAI-Sample-Validation-Template.git
cd EscrowAI-Sample-Validation-Template

# Set required environment variables
export ENCLAVE_URL="https://enclaveapi.escrow.beekeeperai.com/"
export SAS_URL="your_sas_url_here"
```

### Step 3: Choose Execution Method

## How to Run Examples

### Option 1: Local Development
For rapid development and testing:

```bash
# Navigate to your chosen example
cd example/breast-cancer-training  # or covid-validation, diabetes-validation-r

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ENCLAVE_URL="https://enclaveapi.escrow.beekeeperai.com/"
export SAS_URL="your_sas_url_here"

# Run directly
python training.py  # or app.py for other examples
```

**Note**: Local execution connects to the EscrowAI sandbox environment and requires a valid SAS URL for data access.

### Option 2: Docker Container
For testing containerized deployment:

```bash
# Navigate to your chosen example
cd example/breast-cancer-training

# Build the Docker image
docker build -t your-algorithm-name .

# Run the container
docker run --rm --network host \
    -e ENCLAVE_URL="https://enclaveapi.escrow.beekeeperai.com/" \
    -e SAS_URL="your_sas_url_here" \
    your-algorithm-name
```

**Important Docker Notes:**
- Use `--network host` to allow container access to host services (like MLflow)
- On macOS/Windows, use `host.docker.internal` instead of `localhost` for host services
- All required environment variables must be passed with `-e` flags

### Option 3: EscrowAI Enclave (Production)
For secure production deployment:

1. **Prepare for encryption**: 
   - Encrypt sensitive files (models, algorithms, data)
   - Keep `Dockerfile` and `run.sh` unencrypted
   - Organize files according to encryption requirements

2. **Package the algorithm**:
   Login to EscrowAI and use the Encryption Tool to package your entire algorithm directory and mark sensitive files for encryption. This will also transparently create your required secrets.yaml file which is a manifest of where files should be placed when they are unencrypted after loading.

3. **Upload to EscrowAI**:
   - Use the EscrowAI platform interface
   - Upload your encrypted package

4. **Execute**: Run within the trusted execution environment with automatic data provisioning

## Algorithm Package Structure

Every EscrowAI algorithm must include:

```bash
algorithm-package/
├── Dockerfile          # Container environment (NEVER encrypt)
├── run.sh             # Entry point script (do not encrypt if referenced by Dockerfile)
├── your-algorithm.py  # Main algorithm code (can encrypt)
├── requirements.txt   # Dependencies (do not encrypt if referenced by Dockerfile)
├── schema.json       # Validation schema (can encrypt)
└── models/           # Model files (encrypt for security)
```

### Key Components

- **`Dockerfile`**: Defines the container environment and dependencies
- **`run.sh`**: Entry point that launches your algorithm
- **Algorithm code**: Your main processing logic using EnclaveSDK
- **`requirements.txt`**: Python/R package dependencies
- **`schema.json`**: Output validation requirements (passed as value in sandbox, loaded as validation criteria in EscrowAI production)

## Schema Validation

The `schema.json` file serves different purposes depending on your execution environment:

### Sandbox Testing
- **Purpose**: Passed as a value to the EnclaveSDK for immediate validation
- **Usage**: Your algorithm code reads and uses the schema to validate outputs before posting reports
- **Flexibility**: Can be modified and tested quickly during development

### EscrowAI Production
- **Purpose**: Loaded as validation criteria into the EscrowAI platform
- **Usage**: The enclave automatically validates all outputs against the pre-loaded schema
- **Security**: Schema is part of the trusted execution environment configuration

This dual approach allows for flexible development testing while ensuring strict validation in production deployments.

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENCLAVE_URL` | No | `https://enclaveapi.escrow.beekeeperai.com/` | EscrowAI API endpoint |
| `SAS_URL` | Yes* | None | Blob storage access URL |
| `MLFLOW_TRACKING_URI` | No** | None | MLflow server URL |

*Required for sandbox testing and some production scenarios
**Required only for examples using MLflow

## Security and Encryption

### Files to Encrypt
- Algorithm source code (for IP protection)
- Model files and weights
- Configuration files with sensitive parameters
- Any proprietary data processing logic

### Files to Keep Unencrypted
- `Dockerfile` (required by build system)
- `run.sh` (entry point must be readable)
- `requirements.txt` (if referenced directly in Dockerfile)

## Troubleshooting

### Common Issues

**SAS URL Problems:**
- Ensure URL is properly formatted and not expired
- Verify read and list permissions on blob storage
- Check that data files exist in the specified container

**Docker Issues:**
- Use `--network host` for accessing host services
- On macOS/Windows, use `host.docker.internal:5000` instead of `localhost:5000`
- Ensure Docker daemon is running with sufficient permissions

**Environment Variable Issues:**
- Verify all required variables are set: `env | grep -E "(ENCLAVE_URL|SAS_URL)"`
- Use quotes around URLs containing special characters
- Check variable spelling and case sensitivity

**MLflow Connection Issues:**
- Start MLflow server: `mlflow server --host 0.0.0.0 --port 5000`
- Test connectivity: `curl http://localhost:5000/health`
- Use correct host reference in Docker containers

### Verification Commands

```bash
# Check environment variables
env | grep -E "(ENCLAVE_URL|SAS_URL|MLFLOW_TRACKING_URI)"

# Test Docker build
docker build -t test-build .

# Verify MLflow server
curl http://localhost:5000/health

# Test Python dependencies
python -c "import EnclaveSDK; print('SDK imported successfully')"
```

## Example-Specific Documentation

Each example includes detailed README files with specific instructions:

- **[Breast Cancer Training](example/breast-cancer-training/README.md)**: PyTorch deep learning with MLflow tracking
- **[COVID Validation](example/covid-validation/README.md)**: Image classification inference
- **[Diabetes Analysis](example/diabetes-validation-r/README.md)**: Statistical analysis in R

## Support and Resources

- **Docker Getting Started**: https://docs.docker.com/get-started/
- **MLflow Documentation**: https://mlflow.org/docs/latest/index.html

For technical support, contact BeeKeeperAI.
