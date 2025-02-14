# Wine Quality Prediction Project

## Overview
This project demonstrates a machine learning model for predicting wine quality based on physicochemical features. It serves as an example of how to structure a model for both local development and deployment on the EscrowAI platform for secure collaboration.

## Dataset
The dataset used in this project is from the [UCI Machine Learning Repository](http://archive.ics.uci.edu/ml/datasets/Wine+Quality).

## Prerequisites
- Python 3.7+
- MLflow
- Scikit-learn
- Pandas
- Numpy

## Usage Options

### 1. Local Development
For local development and testing:

1. Clone the repository:
```bash
git clone https://github.com/BeeKeeperAI/EscrowAI-Sample-Validation-Template
cd examples/wine-quality-sklearn
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the MLflow server:
```bash
mlflow server --host 127.0.0.1 --port 8080
```

4. Run the training script:
```bash
python train.py
```

### 2. EscrowAI Platform Deployment
To use this project on the EscrowAI platform:

1. Package this directory according to EscrowAI specifications
2. Upload to the EscrowAI platform through the web interface
3. The platform will automatically handle the execution environment and security measures

## Configuration

### Local Development
When running locally, set these environment variables:
- `MLFLOW_TRACKING_URI`: URI for MLflow tracking (default: "http://127.0.0.1:8080")
- `alpha`: ElasticNet hyperparameter (default: 0.5)
- `l1_ratio`: ElasticNet hyperparameter (default: 0.5)
- `SAS_URL`: Azure Blob Storage SAS URL with read and list permissions for your training data

### Data Storage for Local Development
When developing locally, your training data should be:
1. Stored in an Azure Blob Container
2. Accessible via a SAS URL with read and list permissions
3. Set in your environment as `SAS_URL`

This setup allows the EnclaveSDK to connect to the sandbox EnclaveAPI server and validate your implementation will work correctly when deployed to the EscrowAI platform.

### EscrowAI Platform
When running on EscrowAI:
- Environment variables will be automatically configured by the platform
- Secure data access and model validation will be handled by the platform

## Project Structure
```
wine-quality-sklearn/
├── train.py          # Main training script
├── requirements.txt  # Project dependencies
└── README.md        # This file
```

## Features
- Model Training: Trains an ElasticNet regression model on wine quality data
- MLflow Integration: Tracks experiments, parameters, and metrics
- Platform Compatibility: Works both locally and on the EscrowAI platform

## Notes
- When running locally, this project uses standard MLflow tracking
- When deployed to EscrowAI, the platform provides secure data access and validation capabilities