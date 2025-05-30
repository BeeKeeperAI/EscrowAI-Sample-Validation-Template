# Breast Cancer Detection Training Example using PyTorch and MLflow

This example demonstrates how to train a deep learning model for breast cancer detection using PyTorch. It utilizes a pre-trained ResNet101 model, fine-tunes it on a breast cancer dataset, and tracks the training process using MLflow. The script is designed to be adaptable for local execution, testing against the EnclaveAPI Sandbox, and deployment in a production EscrowAI enclave.

**Upon successful execution (in any mode), you should generally expect to see:**
*   Training progress logged to your console.
*   Metrics, parameters, and the trained model logged to your MLflow server.
*   A final status message in the console indicating the report has been posted (if using EnclaveSDK for reports).

## 1. Prerequisites

### Knowledge

*   **Docker**: Understanding of Docker concepts (building images, running containers, environment variables, volume mounting). Refer to the [Docker documentation](https://docs.docker.com/get-started/) if needed.
*   **Python**: Familiarity with Python programming, including libraries like PyTorch, Pandas, and Scikit-learn.
*   **Machine Learning**: Basic understanding of machine learning concepts, particularly image classification and transfer learning.

### Technical Requirements

*   **Python 3.12+** (for running script directly)
*   **Docker 20+** (for containerized execution)
*   **Bash** (or a compatible shell)
*   Required Python packages (listed in `requirements.txt`)

### Dataset: Breast Ultrasound Images (BUSI)

*   **Download**: The `Dataset_BUSI_with_GT` can be obtained from Kaggle: [Breast Ultrasound Images Dataset](https://www.kaggle.com/datasets/aryashah2k/breast-ultrasound-images-dataset).
*   **Citation**: Al-Dhabyani W, Gomaa M, Khaled H, Fahmy A. Dataset of breast ultrasound images. Data in Brief. 2020 Feb;28:104863. DOI: 10.1016/j.dib.2019.104863.
*   **Expected Local Structure**:
    ```
    ./Dataset_BUSI_with_GT/
    ├── benign/
    │   └── (Ultrasound images)
    ├── malignant/
    │   └── (Ultrasound images)
    └── normal/
        └── (Ultrasound images)
    ```
*   **Local Usage**: For local testing (running `python training.py` directly or with Docker using a local mount), download and extract the dataset. Ensure the `Dataset_BUSI_with_GT` directory is in the project root (same level as `training.py`). The script will prioritize using this local data if found.
*   **Sandbox Data Provisioning**: If you intend for the script to *download* data using the EnclaveAPI Sandbox:
    1.  Create a zip file containing the `Dataset_BUSI_with_GT` directory itself. For example, if your structure is `MyProject/Dataset_BUSI_with_GT/...`, you would zip the `Dataset_BUSI_with_GT` folder, not just its contents. The resulting zip file (e.g., `Dataset_BUSI_with_GT.zip`) should, upon extraction, create the `Dataset_BUSI_with_GT` directory in the current location.
    2.  Upload this zip file to your Azure Blob Storage container.
    3.  You will then need to provide a `SAS_URL` (see "Critical Configurations" below).

### Critical Configurations for Local/Sandbox Runs & MLflow

For successful local execution or when testing against the EnclaveAPI Sandbox, and for MLflow integration, specific environment variables are key. The `training.py` script reads these at runtime.

*   **MLflow Tracking Server (`MLFLOW_TRACKING_URI`)**:
    *   **Importance**: Essential for logging all experiment parameters, metrics, and the trained model to a central server.
    *   **Setup**: You need an accessible MLflow Tracking Server. Set the `MLFLOW_TRACKING_URI` environment variable to point to your server's address (e.g., `http://your-mlflow-server:5000`). Ensure this server is network-accessible from where `training.py` executes (your local machine or the Docker container).
    *   **Default**: If not set, MLflow defaults to logging to a local `./mlruns` directory. This is useful for quick local tests but not for persistent or shared tracking.

*   **EnclaveAPI Endpoint (`ENCLAVE_URL`)**:
    *   **Importance**: Required for *all* EnclaveSDK calls (e.g., logging with `post_log`, posting reports with `post_report`, and data fetching if `SAS_URL` is also used) when running outside a true EscrowAI enclave (i.e., locally or in a Docker container for testing). This tells the SDK where to send its requests.
    *   **Default & Override**: The script defaults to `https://enclaveapi.escrow.beekeeperai.com` (the public sandbox). This can be overridden by setting the `ENCLAVE_URL` environment variable if you are using a different sandbox instance or a local mock server.

*   **Sandbox Data Access (`SAS_URL`)**:
    *   **Importance**: Only required if you want the script to *download* the dataset via the EnclaveAPI Sandbox (i.e., the `Dataset_BUSI_with_GT` directory is not present locally in the project root, and you want the script to fetch it using `ENCLAVE_URL` and this `SAS_URL`).
    *   **Setup**: Provide a Shared Access Signature URL for your Azure Blob Storage container where the zipped dataset (e.g., `Dataset_BUSI_with_GT.zip`, structured as described above) is stored. This **must** be provided as the `SAS_URL` environment variable.
    *   **Encoding**: The script will automatically Base64 encode the `SAS_URL` if it's not already encoded.
    *   **Permissions**: The SAS token must grant at least read and list permissions for the container.

## 2. Files in this Example
*   **`Dockerfile`**: Defines the Docker container environment.
    *   It installs dependencies, copies project files (setting `WORKDIR /app`).
    *   Crucially, it pre-downloads the `resnet101.pth` model to `/app/resnet101.pth`.
*   **`requirements.txt`**: Python packages required for the project.
*   **`run.sh`**: Entry point for the Docker container, executing `python training.py`.
*   **`training.py`**: The core script. Handles:
    *   Data acquisition: Prioritizes local `Dataset_BUSI_with_GT`. If not found, attempts download via EnclaveSDK (requires `ENCLAVE_URL` to point to the sandbox and `SAS_URL` for data location).
    *   Model loading:
        *   Inside Docker (where `WORKDIR` is `/app`): Uses `/app/resnet101.pth` (placed by `Dockerfile`).
        *   For direct local runs: Checks for `resnet101.pth` in the current directory, downloading it if not found (requires internet access).
    *   Preprocessing, training, evaluation, and MLflow logging.
    *   EnclaveSDK for logs and final report posting (requires `ENCLAVE_URL` to be set to your sandbox for local/Docker sandbox runs).

## 3. How to Run This Example

There are three primary ways to run this example: directly via `python training.py` for local development, using Docker for various scenarios, and deploying to a production EscrowAI enclave.

### A. Building the Docker Image (Common Step for Dockerized Runs)

```bash
docker build -t breast-cancer-training .
```
This image includes all dependencies and the `resnet101.pth` model, making container runs self-contained regarding the base model.

### B. Running with Docker

When running with Docker:
*   Set `MLFLOW_TRACKING_URI` if not using local `mlruns` (see MLflow section for default behavior).
*   `ENCLAVE_URL` must be resolvable by the container for SDK calls (logs, reports, and data downloads if used). It defaults to the public sandbox (`https://enclaveapi.escrow.beekeeperai.com`); set `ENCLAVE_URL` if you use a custom sandbox or need to specify it.
*   `SAS_URL` is only needed if the container should download the data via the Sandbox.

**Scenario 1: Docker with Local Data & Remote MLflow**

   Mount your local dataset. SDK calls (logs, reports) will target the `ENCLAVE_URL` (default public sandbox or your custom one).

   ```bash
   # Ensure Dataset_BUSI_with_GT is in your current directory
   docker run --rm \
       -v "$(pwd)/Dataset_BUSI_with_GT:/app/Dataset_BUSI_with_GT" \
       -e MLFLOW_TRACKING_URI="http://your-mlflow-server:5000" \
       # Optional: -e ENCLAVE_URL="https://your-custom-sandbox-url.com" \
       breast-cancer-training
   ```
   **Expected Outcome**: Training logs in console. Run appears in your MLflow server. Final report status logged via SDK to the specified `ENCLAVE_URL`.

**Scenario 2: Docker with EnclaveAPI Sandbox for Data Download & Remote MLflow**

   The container will download data using `SAS_URL` and target `ENCLAVE_URL` for this and other SDK calls.

   ```bash
   docker run --rm \
       -e SAS_URL="your_actual_sas_url_string_for_zipped_data" \
       -e MLFLOW_TRACKING_URI="http://your-mlflow-server:5000" \
       -e ENCLAVE_URL="https://your-sandbox-url.com" # Or let it default if using public sandbox
       breast-cancer-training
   ```
   *   Ensure your zipped `Dataset_BUSI_with_GT.zip` (structured as described under "Dataset") is in the Azure Blob container your `SAS_URL` points to.
   *   **Expected Outcome**: Data download logs, then training logs in console. Run appears in your MLflow server. Final report status logged via SDK to the specified `ENCLAVE_URL`.

### C. Running Locally (Direct Script Execution with `python training.py`)

This is useful for rapid development and debugging.

1.  **Prepare Environment & Data**:
    *   **(Recommended) Set up a Python Virtual Environment**:
        To avoid conflicts with your global Python packages, it's highly recommended to use a virtual environment for this project.
        ```bash
        # Navigate to the example directory if you haven't already
        # cd example/breast-cancer-training

        # Create a virtual environment (e.g., named .venv)
        python3 -m venv .venv

        # Activate the virtual environment
        # On macOS and Linux:
        source .venv/bin/activate
        # On Windows (Git Bash or WSL):
        # source .venv/Scripts/activate
        # On Windows (Command Prompt or PowerShell):
        # .venv\Scripts\activate.bat
        ```
        You should see `(.venv)` at the beginning of your shell prompt, indicating the virtual environment is active. All subsequent `pip install` commands will install packages into this isolated environment.
    *   Install dependencies: `pip install -r requirements.txt`
    *   **Data**: Place `Dataset_BUSI_with_GT` (structured as shown above) in the project root (script prioritizes this).
    *   **MLflow**: `export MLFLOW_TRACKING_URI="http://your-mlflow-server:5000"` (or let it default to `./mlruns`).
    *   **EnclaveSDK (for logs/reports/sandbox data)**: `export ENCLAVE_URL="https://your-sandbox-url.com"` (defaults to `https://enclaveapi.escrow.beekeeperai.com` if not set). This is needed for any SDK interaction.
    *   **ResNet Model**: If `resnet101.pth` is not in the root, the script will try to download it.

2.  **Run Script**:
    *   **Using local data**:
        ```bash
        # Ensure ENCLAVE_URL and MLFLOW_TRACKING_URI are set as desired
        python training.py
        ```
    *   **Forcing Sandbox data download** (remove or rename local `Dataset_BUSI_with_GT` directory first):
        ```bash
        export SAS_URL="your_actual_sas_url_string_for_zipped_data"
        # Ensure ENCLAVE_URL and MLFLOW_TRACKING_URI are set as desired
        python training.py
        ```
   **Expected Outcome (for both local scenarios)**: Training logs in console. Run appears in your MLflow server. Final report status logged via SDK to the specified `ENCLAVE_URL`.

### D. Running in the EscrowAI Enclave (Production)

1.  **Package Algorithm**: Create a zip file containing `Dockerfile`, `run.sh`, `training.py`, and `requirements.txt`.
2.  **Upload to EscrowAI**: Upload this package to the EscrowAI platform.
3.  **Configure Execution**:
    *   **Data**: Data will be provisioned by the Data Steward within the enclave. The script's EnclaveSDK data calls will access this. `SAS_URL` **should not** be set.
    *   **Secrets**: Designate `training.py` for encryption via the EscrowAI platform UI if desired.
    *   **Environment Variables**: `ENCLAVE_URL` is automatically set by the EscrowAI environment to point to the production Enclave API. Set `MLFLOW_TRACKING_URI` if needed for your production MLflow setup.
4.  **Execute**: Run the job. EscrowAI handles decryption (if applicable) and execution within the TEE.

## 4. MLflow Tracking Details

The `training.py` script logs the following to your configured MLflow Tracking Server (viewable via its web UI):
*   **Parameters**: Batch Size, Epochs, Patience, Learning Rate, Step Size, Gamma, Accelerator type.
*   **Metrics**: Loss and accuracy per step/epoch for training and validation phases, overall classification report metrics (precision, recall, f1-score per class), and macro/micro averages for OVR ROC AUC.
*   **Figures**: A plot of the One-vs-Rest (OVR) ROC AUC curve (`ovr_roc_auc.png`).
*   **Model**: The trained PyTorch model, registered as `BreastCancerPytorchModel`.

Ensure your MLflow server is accessible from where the `training.py` script executes (e.g., your local machine, or the Docker container).

## 5. Troubleshooting Tips

*   **MLflow Connection Issues**:
    *   Ensure `MLFLOW_TRACKING_URI` is correct and the server is network-accessible.
    *   If not set, results will be in a local `mlruns` folder in the execution directory.
*   **Data Not Found**:
    *   **Local**: Verify `Dataset_BUSI_with_GT` is in the project root with the correct internal structure.
    *   **Sandbox Download (`SAS_URL`)**: Double-check the `SAS_URL` itself, its permissions (read/list on container), that the zipped data is in the blob container, and that the zip file is structured to extract `Dataset_BUSI_with_GT` folder.
*   **EnclaveSDK Errors (logs/reports/sandbox data access)**:
    *   Ensure `ENCLAVE_URL` is correctly set to your intended sandbox environment (or allowed to default to the public one if that's your target).
    *   If using `SAS_URL` for data, `