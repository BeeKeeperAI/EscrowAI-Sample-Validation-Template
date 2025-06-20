# Breast Cancer Detection Training - EscrowAI Example

This example demonstrates how to train a deep learning model for breast cancer detection using PyTorch within EscrowAI's secure enclave environment. The application utilizes a pre-trained ResNet101 model, fine-tunes it on breast cancer ultrasound images, and tracks the training process using MLflow.

## Prerequisites

### Technical Requirements
- Docker Version 20+
- MLflow (for experiment tracking)
- Internet connection (for downloading pre-trained model weights)

### Data Requirements
- **Breast Ultrasound Images Dataset (BUSI)** from Kaggle: [Download here](https://www.kaggle.com/datasets/aryashah2k/breast-ultrasound-images-dataset)
- **SAS URL** for accessing dataset in Azure blob storage (for sandbox/enclave execution)

### Environment Variables
The application requires the following environment variables:

- **`SAS_URL`** (Required for sandbox): Shared Access Signature URL for accessing your blob storage containing the dataset zip file
- **`MLFLOW_TRACKING_URI`** (Required): MLflow tracking server URL for experiment logging
- **`ENCLAVE_URL`** (Optional): EscrowAI enclave API endpoint. Defaults to `https://enclaveapi.escrow.beekeeperai.com/`

## What This Example Does

This example trains a breast cancer detection model:

1. Downloads and extracts breast ultrasound images from Azure blob storage using the SAS URL
2. Fine-tunes a pre-trained ResNet101 model for 3-class classification (benign/malignant/normal)
3. Tracks training metrics, parameters, and model artifacts using MLflow
4. Validates model performance with comprehensive evaluation metrics
5. Posts training results through the EnclaveAPI

## Files in This Example

1. **`Dockerfile`** - Container environment with PyTorch, MLflow, and pre-downloaded ResNet101 model
2. **`run.sh`** - Entry point script that executes the training process
3. **`training.py`** - Main training script with data loading, model training, and MLflow integration
4. **`requirements.txt`** - Python dependencies including PyTorch, MLflow, and scientific computing libraries

**Note**: This example focuses on training and MLflow integration. For validation workflows that require output schema validation, a `schema.json` file would be passed as a value in sandbox testing or loaded as validation criteria in EscrowAI production.

## Quick Start Guide

### Step 1: Start MLflow Server

First, install MLflow and start the tracking server:

```bash
# Install MLflow
pip install mlflow

# Create directories for MLflow storage
mkdir -p mlflow_data/mlruns mlflow_data/artifacts

# Start MLflow server (keep this running in a separate terminal)
mlflow server \
    --backend-store-uri file://$(pwd)/mlflow_data/mlruns \
    --default-artifact-root file://$(pwd)/mlflow_data/artifacts \
    --host 0.0.0.0 \
    --port 5000
```

The MLflow UI will be available at http://localhost:5000

### Step 2: Build Docker Image

```bash
# Build the Docker image
docker build -t breast-cancer-training .
```

### Step 3: Run Training with SAS URL

```bash
# Run with sandbox data download using SAS URL
docker run --rm --network host \
    -e MLFLOW_TRACKING_URI="http://host.docker.internal:5000" \
    -e ENCLAVE_URL="https://enclaveapi.escrow.beekeeperai.com" \
    -e SAS_URL="your_sas_url_here" \
    breast-cancer-training
```

**Example with SAS URL:**
```bash
docker run --rm --network host \
    -e MLFLOW_TRACKING_URI="http://host.docker.internal:5000" \
    -e ENCLAVE_URL="https://enclaveapi.escrow.beekeeperai.com" \
    -e SAS_URL="yoursasurlhere" \
    breast-cancer-training
```

## Alternative: Run with Local Dataset

If you have the dataset locally, you can mount it into the container:

```bash
# Download and extract the BUSI dataset to ./Dataset_BUSI_with_GT/
# Then run with local data
docker run --rm --network host \
    -v "$(pwd)/Dataset_BUSI_with_GT:/app/Dataset_BUSI_with_GT" \
    -e MLFLOW_TRACKING_URI="http://host.docker.internal:5000" \
    -e ENCLAVE_URL="https://enclaveapi.escrow.beekeeperai.com" \
    breast-cancer-training
```

Expected local dataset structure:
```
./Dataset_BUSI_with_GT/
├── benign/
├── malignant/
└── normal/
```

## Expected Results

Upon successful execution, you should see:
- Training progress with loss and accuracy metrics per epoch
- MLflow experiment tracking with:
  - Training parameters (batch size, learning rate, epochs)
  - Metrics (loss, accuracy, F1-score, ROC AUC)
  - Model artifacts and ROC curve plots
- Final classification report with per-class performance
- Model registration in MLflow as `BreastCancerPytorchModel`

## MLflow Integration

The training script logs comprehensive metrics to MLflow:
- **Parameters**: Batch size, epochs, learning rate, optimizer settings
- **Metrics**: Training/validation loss and accuracy, classification metrics
- **Artifacts**: ROC AUC curves, confusion matrices, trained model
- **Model Registry**: Automatic model registration for deployment

## Troubleshooting

### Common Issues

**MLflow Connection Issues:**
- Ensure MLflow server is running: `curl http://localhost:5000/health`
- For Docker on macOS/Windows, use `host.docker.internal:5000` instead of `localhost:5000`
- Check that port 5000 is not blocked by firewall

**SAS URL Issues:**
- Ensure the SAS URL is properly formatted and not expired
- Verify the SAS URL has read and list permissions for the blob storage container
- Check that the dataset zip file exists in the specified blob storage container

**Docker Network Issues:**
- Use `--network host` flag to allow container to access host services
- On some systems, you may need to use the host's IP address instead of `host.docker.internal`

**Data Issues:**
- If using local data, ensure the `Dataset_BUSI_with_GT` directory structure is correct
- Verify that image files are in PNG format and not corrupted

### Verification Commands

```bash
# Check if MLflow server is running
curl http://localhost:5000/health

# Check Docker image was built successfully
docker images | grep breast-cancer-training

# Test MLflow connectivity from Python
python -c "import mlflow; mlflow.set_tracking_uri('http://localhost:5000'); print('MLflow connection successful')"
```

## EscrowAI Enclave Deployment

For production deployment in the EscrowAI enclave:

1. **Package**: Login to EscrowAI and use the Encryption Tool to package your entire algorithm directory and mark sensitive files for encryption. This will also transparently create your required secrets.yaml file which is a manifest of where files should be placed when they are unencrypted after loading.
2. **Upload**: Upload the package to the EscrowAI platform
4. **Execute**: Run the training job within the trusted execution environment

The enclave will automatically handle data provisioning and secure execution.