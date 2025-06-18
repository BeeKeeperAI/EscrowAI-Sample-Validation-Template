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

2. **Configure environment variables**:
   ```bash
   export MLFLOW_TRACKING_URI="http://your-mlflow-server:5000"
   export ENCLAVE_URL="https://enclaveapi.escrow.beekeeperai.com"  # Default sandbox
   ```

3. **Run training**:
   ```bash
   # With local dataset (place Dataset_BUSI_with_GT in project root)
   python training.py
   
   # Or with sandbox data download
   export SAS_URL="your_sas_url_for_dataset_zip"
   python training.py
   ```

### Option 2: Docker Container
Build and run the containerized version:

```bash
# Build the Docker image
docker build -t breast-cancer-training .

# Run with local data
docker run --rm \
    -v "$(pwd)/Dataset_BUSI_with_GT:/app/Dataset_BUSI_with_GT" \
    -e MLFLOW_TRACKING_URI="http://your-mlflow-server:5000" \
    breast-cancer-training

# Run with sandbox data download
docker run --rm \
    -e SAS_URL="your_sas_url_for_dataset_zip" \
    -e MLFLOW_TRACKING_URI="http://your-mlflow-server:5000" \
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

- **MLflow connection issues**: Verify `MLFLOW_TRACKING_URI` is accessible from your execution environment
- **Data not found**: Ensure `Dataset_BUSI_with_GT` is in the project root with correct structure
- **Sandbox data download**: Check `SAS_URL` permissions and verify zip file structure in blob storage
- **CUDA/GPU issues**: The script automatically detects and uses available GPU acceleration
- **Memory errors**: Reduce batch size in the training script if encountering out-of-memory errors

For detailed configuration options and advanced usage, refer to the inline documentation in `training.py`.