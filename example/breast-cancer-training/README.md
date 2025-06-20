# Breast Cancer Detection Training - EscrowAI Example

This example demonstrates how to train a deep learning model for breast cancer detection using PyTorch within EscrowAI's secure enclave environment. The application utilizes a pre-trained ResNet101 model, fine-tunes it on breast cancer ultrasound images, and tracks the training process using MLflow.

## Prerequisites

### Knowledge Requirements
- Understanding of Docker container build system ([Docker getting-started tutorial](https://docs.docker.com/get-started/) recommended)
- Python programming with PyTorch, Pandas, and Scikit-learn
- Basic machine learning concepts, particularly image classification and transfer learning

### Technical Requirements
- Python 3.12 or higher
- Docker Version 20+
- Bash shell
- MLflow Tracking Server (for experiment tracking)

### Data Requirements
- **Breast Ultrasound Images Dataset (BUSI)** from Kaggle: [Download here](https://www.kaggle.com/datasets/aryashah2k/breast-ultrasound-images-dataset)
- Expected local structure:
  ```
  ./Dataset_BUSI_with_GT/
  ├── benign/
  ├── malignant/
  └── normal/
  ```
- SAS URL for accessing dataset in blob storage (for sandbox/enclave execution)

### Environment Variables
The application requires the following environment variables:

- **`SAS_URL`** (Optional for local, Required for sandbox): Shared Access Signature URL for accessing your blob storage containing the dataset zip file
- **`ENCLAVE_URL`** (Optional): EscrowAI enclave API endpoint. Defaults to `https://enclaveapi.escrow.beekeeperai.com/` if not provided
- **`MLFLOW_TRACKING_URI`** (Required): MLflow tracking server URL for experiment logging

## What This Example Does

This example trains a breast cancer detection model within a secure enclave environment:

1. Loads and preprocesses breast ultrasound images from the BUSI dataset
2. Fine-tunes a pre-trained ResNet101 model for 3-class classification (benign/malignant/normal)
3. Tracks training metrics, parameters, and model artifacts using MLflow
4. Validates model performance with comprehensive evaluation metrics
5. Posts training results and final model through the EnclaveAPI

## Files in This Example

1. **`Dockerfile`** - Container environment with PyTorch, MLflow, and pre-downloaded ResNet101 model
2. **`run.sh`** - Entry point script that executes the training process
3. **`training.py`** - Main training script with data loading, model training, and MLflow integration
4. **`requirements.txt`** - Python dependencies including PyTorch, MLflow, and scientific computing libraries

## How to Run This Example

### Option 1: Local Development
For testing and development:

1. **Set up environment**:
   ```bash
   # Create and activate virtual environment (recommended)
   python3 -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Start MLflow Tracking Server** (required for local development):
   
   **Option A: Simple local MLflow server**
   ```bash
   # In a separate terminal window, start MLflow server
   mlflow server --host 0.0.0.0 --port 5000
   
   # Server will be available at http://localhost:5000
   # MLflow UI will show experiments and runs
   ```
   
   **Option B: MLflow with file store and artifact store**
   ```bash
   # Create directories for MLflow storage
   mkdir -p mlflow_data/mlruns mlflow_data/artifacts
   
   # Start MLflow server with specific storage locations
   mlflow server \
       --backend-store-uri file:///$(pwd)/mlflow_data/mlruns \
       --default-artifact-root file:///$(pwd)/mlflow_data/artifacts \
       --host 0.0.0.0 \
       --port 5000
   ```
   
   **Option C: Using Docker for MLflow**
   ```bash
   # Run MLflow server in Docker container
   docker run -d \
       --name mlflow-server \
       -p 5000:5000 \
       -v $(pwd)/mlflow_data:/mlflow \
       python:3.9-slim \
       bash -c "pip install mlflow && mlflow server --host 0.0.0.0 --backend-store-uri file:///mlflow/mlruns --default-artifact-root file:///mlflow/artifacts"
   ```

3. **Configure environment variables**:
   ```bash
   # Required: MLflow tracking server
   export MLFLOW_TRACKING_URI="http://localhost:5000"
   
   # Optional: EscrowAI API endpoint (defaults to sandbox)
   export ENCLAVE_URL="https://enclaveapi.escrow.beekeeperai.com"
   
   # Optional: For sandbox data download (replace with your actual SAS URL)
   export SAS_URL="your_sas_url_for_dataset_zip"
   ```

4. **Run training**:
   ```bash
   # With local dataset (place Dataset_BUSI_with_GT in project root)
   python training.py
   
   # Or with sandbox data download (ensure SAS_URL is set)
   python training.py
   ```

   **Important**: When using sandbox data download, you must provide:
   - `SAS_URL`: The Shared Access Signature URL for accessing your dataset zip file in blob storage
   - The SAS URL must have read and list permissions for the blob storage container

   **Note**: Keep the MLflow server running in a separate terminal while training. You can monitor the training progress by opening http://localhost:5000 in your browser.

### Option 2: Docker Container
Build and run the containerized version:

```bash
# Build the Docker image
docker build -t breast-cancer-training .

# Run with local data
docker run --rm \
    -v "$(pwd)/Dataset_BUSI_with_GT:/app/Dataset_BUSI_with_GT" \
    -e MLFLOW_TRACKING_URI="http://your-mlflow-server:5000" \
    -e ENCLAVE_URL="https://enclaveapi.escrow.beekeeperai.com" \
    breast-cancer-training

# Run with sandbox data download
docker run --rm \
    -e SAS_URL="your_sas_url_for_dataset_zip" \
    -e MLFLOW_TRACKING_URI="http://your-mlflow-server:5000" \
    -e ENCLAVE_URL="https://enclaveapi.escrow.beekeeperai.com" \
    breast-cancer-training
```

### Option 3: EscrowAI Enclave
For production training in the secure enclave:

1. **Package the algorithm**: Create a zip file with `Dockerfile`, `run.sh`, `training.py`, and `requirements.txt`
2. **Upload to EscrowAI**: Upload the package to the EscrowAI platform
3. **Configure execution**: Set `MLFLOW_TRACKING_URI` if using external MLflow server
4. **Execute**: Run the training job within the trusted execution environment

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

### MLflow Issues
- **MLflow server not running**: Ensure MLflow server is started before running training
  ```bash
  # Check if MLflow server is running
  curl http://localhost:5000/health
  
  # If not running, start it:
  mlflow server --host 0.0.0.0 --port 5000
  ```
- **MLflow connection issues**: 
  - Verify `MLFLOW_TRACKING_URI` matches your running MLflow server URL
  - Check firewall settings allow connections to port 5000
  - For Docker MLflow: ensure container is running with `docker ps`
- **MLflow UI not accessible**: 
  - Visit http://localhost:5000 in your browser
  - If using Docker, check port mapping with `docker port mlflow-server`

### Data and Training Issues
- **Data not found**: Ensure `Dataset_BUSI_with_GT` is in the project root with correct structure
- **SAS URL issues**: 
  - Ensure the `SAS_URL` environment variable is properly set and contains a valid Shared Access Signature URL
  - Verify that the SAS URL has read and list permissions for the blob storage container
  - Check that the SAS URL has not expired
  - Verify zip file structure in blob storage matches expected dataset format
- **CUDA/GPU issues**: The script automatically detects and uses available GPU acceleration
- **Memory errors**: Reduce batch size in the training script if encountering out-of-memory errors
- **Environment variable errors**: Ensure all required environment variables (`MLFLOW_TRACKING_URI`) are set before running the application

### Quick MLflow Setup Check
```bash
# Verify MLflow installation
pip show mlflow

# Test MLflow server connectivity
python -c "import mlflow; print('MLflow client can connect:', mlflow.get_tracking_uri())"
```

For detailed configuration options and advanced usage, refer to the inline documentation in `training.py`.