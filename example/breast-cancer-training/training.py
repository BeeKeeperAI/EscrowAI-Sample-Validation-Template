import copy
import os
import sys
import shutil
import time
import warnings
import zipfile
from io import BytesIO
from typing import Dict, List

import EnclaveSDK
import matplotlib.pyplot as plt
import mlflow
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from EnclaveSDK import Report, File, RequestFileData, LogData
from mlflow.models import infer_signature
from sklearn.metrics import (
    auc,
    classification_report,
    confusion_matrix,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from torch.optim import lr_scheduler
from torch.utils.data import DataLoader
from torchvision import transforms
from torchvision.datasets import ImageFolder
from torchvision.transforms import ColorJitter, RandomHorizontalFlip, RandomRotation
from tqdm import tqdm
import base64
from torchvision import models

warnings.filterwarnings("ignore")

###########################################################
#   In the following code blocks, we show how to access
#   and download files from the Enclave, and also post
#   training report at the end of training.
###########################################################

# Create the SDK configuration and instantiate the SDK client
enclave_url = os.getenv("ENCLAVE_URL", "https://enclaveapi.escrow.beekeeperai.com") # Default to sandbox for easier testing
configuration = EnclaveSDK.Configuration(enclave_url)

# Use the SAS_URL environment variable to use the Data API in the Sandbox, otherwise default to None
# This allows the script to run in a production enclave (where SAS_URL is not needed/provided)
# or in the sandbox (where SAS_URL is required for data access).
sas_url = os.getenv("SAS_URL", None)
if sas_url:
    # Ensure the SAS URL is base64 encoded if provided directly via env var
    # The EnclaveSDK might handle this differently depending on its version,
    # but this matches the reference pattern.
    try:
        # Check if it's already base64 encoded
        base64.b64decode(sas_url, validate=True)
    except Exception:
        # If not, encode it
        sas_url = base64.b64encode(sas_url.encode()).decode()

api_client = EnclaveSDK.ApiClient(configuration)


# Use the Report API class to post a json report to the Enclave
def post_report(finalReport: Dict) -> Dict:
    # Create an instance of Report API class
    api_instance = EnclaveSDK.ReportApi(api_client)

    # Use the Report model to create a report object for posting
    # the posted report will be validated against the DS-provided
    # validation schema
    report = Report.from_dict(finalReport)
    api_response = api_instance.api_v1_report_post(report)
    print(f"Report sent with a response: {api_response}")


# Use the Data API class to enumerate the files inside the blob container
def list_files(sas_url=None) -> List[File]:
    api_instance = EnclaveSDK.DataApi(api_client)
    response = api_instance.api_v1_data_files_get(sas_url=sas_url)
    return response.files


# Use the Data API class to securely decrypt and download a
# file give the `.name` attribute of the files list
def download_file(file_name: str, sas_url=None):
    api_instance = EnclaveSDK.DataApi(api_client)
    content = api_instance.api_v1_data_file_get(file_name, sas_url=sas_url)
    return content


###########################################################
#   In the following code blocks, we implement the training
#   workflow. We also tracking the training experiments using
#   MLFlow tracking. We log parameters at the start of the
#   training and metrics within the training loop.
###########################################################

# Define the labels and corresponding directories
labels = ["benign", "malignant", "normal"]
data_dir = "./Dataset_BUSI_with_GT"
batch_size = 8  # You can adjust this based on your hardware and preferences


def clear_working_dir(working_dir="./working"):
    if not os.path.exists(working_dir):
        os.mkdir(working_dir)
        return
    # Delete all files and subdirectories in the working directory
    for item in os.listdir(working_dir):
        item_path = os.path.join(working_dir, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)

    # Confirm that the directory is empty
    print("Working directory has been cleared.")


class_names = ["malignant", "normal", "benign"]
minority_classes = ["malignant", "normal"]

# Define custom data transformations for minority classes
minority_class_transforms = transforms.Compose(
    [
        RandomHorizontalFlip(p=0.9),  # Apply with 90% probability
        RandomRotation(15, expand=False, center=None),
        ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
    ]
)

# Define data transformations for train, validation, and test sets
data_transforms = {
    "train": transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            # Apply custom augmentations to minority classes
            (
                transforms.RandomApply([minority_class_transforms], p=0.5)
                if any(cls in minority_classes for cls in class_names)
                else transforms.RandomApply([], p=0.0)
            ),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    ),
    "validation": transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    ),
    "test": transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    ),
}


## Approach 1 - Data Split and create folders- excludes mask files
def data_split(data_dir):
    # Create a list to store file paths and labels
    file_paths = []
    labels = []

    # Loop through the subdirectories (benign, malignant, normal)
    for label in os.listdir(data_dir):
        label_dir = os.path.join(data_dir, label)
        if os.path.isdir(label_dir):
            for image_file in os.listdir(label_dir):
                if image_file.endswith(".png") and not (
                    image_file.endswith("_mask.png")
                    or image_file.endswith("_mask_1.png")
                    or image_file.endswith("_mask_2.png")
                ):
                    image_path = os.path.join(label_dir, image_file)
                    labels.append(label)
                    file_paths.append(image_path)

    # Create a DataFrame to store the file paths and labels
    data = pd.DataFrame({"Image_Path": file_paths, "Label": labels})

    # Split the dataset into train, validation, and test sets
    train_data, test_data = train_test_split(
        data, test_size=0.15, random_state=42, stratify=data["Label"]
    )
    train_data, val_data = train_test_split(
        train_data, test_size=0.15, random_state=42, stratify=train_data["Label"]
    )

    # Define the paths for the train, validation, and test directories
    train_dir = "./working/train"
    val_dir = "./working/validation"
    test_dir = "./working/test"

    # Create the train, validation, and test directories and subdirectories
    for label in labels:
        os.makedirs(os.path.join(train_dir, label), exist_ok=True)
        os.makedirs(os.path.join(val_dir, label), exist_ok=True)
        os.makedirs(os.path.join(test_dir, label), exist_ok=True)

    # Copy the images to the corresponding directories
    for _, row in train_data.iterrows():
        image_path = row["Image_Path"]
        label = row["Label"]
        shutil.copy(image_path, os.path.join(train_dir, label))

    for _, row in val_data.iterrows():
        image_path = row["Image_Path"]
        label = row["Label"]
        shutil.copy(image_path, os.path.join(val_dir, label))

    for _, row in test_data.iterrows():
        image_path = row["Image_Path"]
        label = row["Label"]
        shutil.copy(image_path, os.path.join(test_dir, label))


def make_dataloaders(
    data_dir="./working/", data_transforms=data_transforms, batch_size=batch_size
):
    # Create datasets for train, validation, and test
    image_datasets = {
        x: ImageFolder(root=os.path.join(data_dir, x), transform=data_transforms[x])
        for x in ["train", "validation", "test"]
    }

    # Specify batch size for dataloaders

    # Create dataloaders for train, validation, and test
    dataloaders = {
        x: DataLoader(
            image_datasets[x], batch_size=batch_size, shuffle=True, num_workers=4
        )
        for x in ["train", "validation", "test"]
    }

    # Calculate dataset sizes
    dataset_sizes = {x: len(image_datasets[x]) for x in ["train", "validation", "test"]}

    return dataloaders, dataset_sizes


def ovr_avg_roc(y_true, y_scores):
    fpr, tpr, roc_auc = {}, {}, {}
    for i in range(y_true.shape[1]):
        fpr[i], tpr[i], _ = roc_curve(y_true[:, i], y_scores[:, i])
        roc_auc[i] = auc(fpr[i], tpr[i])

    fpr_grid = np.linspace(0.0, 1.0, 1000)

    # Interpolate all ROC curves at these points
    mean_tpr = np.zeros_like(fpr_grid)

    for i in range(y_true.shape[1]):
        mean_tpr += np.interp(fpr_grid, fpr[i], tpr[i])  # linear interpolation

    # Average it and compute AUC
    mean_tpr /= y_true.shape[1]

    fpr["macro"], tpr["macro"], roc_auc["macro"] = (
        fpr_grid,
        mean_tpr,
        auc(fpr_grid, mean_tpr),
    )
    fpr["micro"], tpr["micro"], _ = roc_curve(y_true.ravel(), y_scores.ravel())
    roc_auc["micro"] = auc(fpr["micro"], tpr["micro"])

    return fpr, tpr, roc_auc


def plot_roc_auc(fpr, tpr, roc_auc):
    fig, ax = plt.subplots(figsize=(6, 6))

    ax.plot(
        fpr["micro"],
        tpr["micro"],
        label=f"micro-average ROC curve (AUC = {roc_auc['micro']:.2f})",
        color="deeppink",
        linestyle=":",
        linewidth=4,
    )

    ax.plot(
        fpr["macro"],
        tpr["macro"],
        label=f"macro-average ROC curve (AUC = {roc_auc['macro']:.2f})",
        color="navy",
        linestyle=":",
        linewidth=4,
    )
    ax.legend()
    plt.title("ROC curve")
    return fig


def one_hot(array, num_classes):
    return np.squeeze(np.eye(num_classes)[array.reshape(-1)])


# Define the training function with early stopping and additional features
def training_loop(
    model,
    lossFunction,
    optimizer,
    scheduler,
    dataloaders,
    dataset_sizes,
    class_names,
    device,
    num_epochs=20,
    patience=2,
    training_parameters={},
):
    since = time.time()

    best_model_wts = copy.deepcopy(model.state_dict())
    best_loss = float("inf")  # Initialize best_loss with a large value
    consecutive_epochs_without_improvement = 0

    # Lists to store training and validation losses
    train_losses = []
    val_losses = []

    for epoch in range(num_epochs):
        print("Epoch {}/{}".format(epoch, num_epochs - 1))
        print("-" * 10)

        # Each epoch has a training and validation phase
        for phase in ["train", "validation"]:
            epoch_start = time.time()
            if phase == "train":
                model.train()  # Set model to training mode
            else:
                model.eval()  # Set model to evaluate mode

            running_loss = 0.0
            running_corrects = 0

            # Iterate over data
            for it, (inputs, labels) in enumerate(tqdm(dataloaders[phase])):
                it_start = time.time()
                inputs = inputs.to(device)
                labels = labels.to(device)

                # Zero the parameter gradients
                optimizer.zero_grad()

                # Forward
                with torch.set_grad_enabled(phase == "train"):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = lossFunction(outputs, labels)

                    # Backward + optimize only if in training phase
                    if phase == "train":
                        loss.backward()
                        optimizer.step()

                # Append training loss here
                if phase == "train":
                    train_losses.append(loss.item())  # Append training loss
                else:
                    val_losses.append(loss.item())  # Append validation loss

                step = epoch * len(dataloaders[phase]) + it

                mlflow.log_metric(f"{phase} loss", value=loss.item(), step=step)

                # Statistics
                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

                mlflow.log_metric(
                    f"{phase} running loss", value=running_loss, step=step
                )

                mlflow.log_metric(
                    f"{phase} time taken per step", (time.time() - it_start), step=step
                )

            if phase == "train":
                scheduler.step()

            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.float() / dataset_sizes[phase]

            mlflow.log_metric(f"{phase} accuracy", value=epoch_acc, step=epoch)
            mlflow.log_metric(
                f"{phase} time taken per epoch", (time.time() - epoch_start), step=epoch
            )

            print("{} Loss: {:.4f} Acc: {:.4f}".format(phase, epoch_loss, epoch_acc))

            # Early stopping: Check if validation loss improved
            if phase == "validation":
                if epoch_loss < best_loss:
                    best_loss = epoch_loss
                    best_model_wts = copy.deepcopy(model.state_dict())
                    consecutive_epochs_without_improvement = 0
                else:
                    consecutive_epochs_without_improvement += 1

                val_losses.append(epoch_loss)

        # Check if early stopping criteria are met
        if consecutive_epochs_without_improvement >= patience:
            print(f"Early stopping after {epoch} epochs")
            break

        print()

    time_elapsed = time.time() - since
    print(
        "Training complete in {:.0f}m {:.0f}s".format(
            time_elapsed // 60, time_elapsed % 60
        )
    )
    print("Best val Loss: {:.4f}".format(best_loss))

    # Load best model weights
    model.load_state_dict(best_model_wts)

    # Calculate classification report and confusion matrix for validation data
    y_true = []
    y_pred = []

    model.eval()  # Set model to evaluation mode

    with torch.no_grad():
        for inputs, labels in dataloaders["validation"]:
            inputs = inputs.to(device)
            labels = labels.to(device)

            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)

            y_true.extend(labels.cpu().numpy())
            y_pred.extend(preds.cpu().numpy())

    # Generate classification report
    target_names = [str(class_names[i]) for i in range(len(class_names))]
    print(classification_report(y_true, y_pred, target_names=target_names))

    # Generate confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    print("Confusion Matrix:")
    print(cm)

    # Define label names
    label_names = [str(class_names[i]) for i in range(len(class_names))]

    # Calculate classification report and confusion matrix on unseen test data
    y_true = []
    y_pred = []
    scores = []

    model.eval()  # Set model to evaluation mode

    with torch.no_grad():
        for inputs, labels in dataloaders["test"]:
            inputs = inputs.to(device)
            labels = labels.to(device)

            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)

            y_true.extend(labels.cpu().numpy())
            y_pred.extend(preds.cpu().numpy())
            scores = (
                np.vstack([scores, outputs.cpu().numpy()])
                if isinstance(scores, np.ndarray)
                else outputs.cpu().numpy()
            )

    # Generate classification report
    classification_rep = classification_report(
        y_true, y_pred, target_names=label_names, output_dict=True
    )

    y_true_onehot = one_hot(np.array(y_true), np.max(y_true) + 1)
    fpr_grid, mean_tpr, roc_auc = ovr_avg_roc(y_true_onehot, scores)

    mlflow.log_figure(plot_roc_auc(fpr_grid, mean_tpr, roc_auc), "ovr_roc_auc.png")

    # Generate confusion matrix
    # confusion_mat = confusion_matrix(y_true, y_pred)

    # Print the simplified classification report
    print("Simplified Classification Report:")
    print(
        pd.DataFrame(classification_rep).iloc[:-1, :]
    )  # Display without support and avg/total rows

    signature = infer_signature(inputs.cpu().numpy(), outputs.cpu().detach().numpy())

    model_info = mlflow.pytorch.log_model(
        model,
        "model",
        registered_model_name="BreastCancerPytorchModel",
        signature=signature,
        metadata=training_parameters,
    )

    return model, model_info, classification_rep

def post_log(message: str, status: str = "In Progress"):
    """Helper function to log both to console and EnclaveAPI"""
    print(f"[{status}] {message}")  # Console logging
    try:
        api_instance = EnclaveSDK.LogApi(api_client)
        log_data = LogData(message=message, status=status)
        api_instance.api_v1_log_post(log_data)
    except Exception as e:
        print(f"Failed to post log to EnclaveAPI: {str(e)}")

def check_data_directory(data_dir: str):
    """Helper function to check data directory structure"""
    post_log(f"Checking directory: {data_dir}")
    
    if not os.path.exists(data_dir):
        post_log(f"Directory does not exist: {data_dir}", status="Failed")
        return False
        
    # List all contents
    contents = os.listdir(data_dir)
    post_log(f"Directory contents: {contents}")
    
    # Count files in each subdirectory
    for subdir in contents:
        full_path = os.path.join(data_dir, subdir)
        if os.path.isdir(full_path):
            files = os.listdir(full_path)
            post_log(f"Subdirectory '{subdir}' contains {len(files)} files")
            
    return True

def main():
    post_log("Starting breast cancer detection training pipeline")
    
    local_data_path = "./Dataset_BUSI_with_GT"

    try:
        post_log("Loading configuration parameters")
        patience = 2
        lr = float(os.environ.get("learning_rate", 0.00005))
        epochs = int(os.environ.get("epochs", 2))
        step_size = 7
        gamma = 0.1

        # Add device initialization
        post_log("Setting up compute device")
        device = torch.device(
            "cuda" if torch.cuda.is_available() 
            else "mps" if torch.backends.mps.is_available() 
            else "cpu"
        )
        post_log(f"Using device: {device}")

        # Initialize the model
        post_log("Initializing ResNet model")
        try:
            # Create the ResNet101 model architecture first
            Resnet101 = models.resnet101(weights=None)  # Start with no weights
            
            if os.path.exists("resnet101.pth"):
                # Load the state dictionary (weights) from the downloaded file
                state_dict = torch.load("resnet101.pth", map_location='cpu')
                Resnet101.load_state_dict(state_dict)
                post_log("Loaded pre-trained ResNet101 weights from file")
            else:
                post_log("Downloading pre-trained ResNet101 model from torchvision")
                Resnet101 = models.resnet101(weights=models.ResNet101_Weights.DEFAULT)
                # Save the state dictionary for future use
                torch.save(Resnet101.state_dict(), "resnet101.pth")
                post_log("Saved downloaded model weights to resnet101.pth")
        except Exception as e:
            post_log(f"Error loading pre-trained model: {str(e)}", status="Failed")
            raise

        # Modify model for fine-tuning
        for param in Resnet101.parameters():
            param.requires_grad = True
        Resnet101.fc = nn.Linear(Resnet101.fc.in_features, len(class_names))
        Resnet_fineTuning = Resnet101.to(device)

        # Setup optimizer and scheduler
        optimizer = optim.Adam(Resnet_fineTuning.parameters(), lr=lr)
        Decay_Learning_Rate = lr_scheduler.StepLR(optimizer, step_size=step_size, gamma=gamma)
        Loss_Function = nn.CrossEntropyLoss()

        post_log("Setting up MLflow tracking")
        mlflow.set_experiment("Breast Cancer Detection")
        
        # Data acquisition: Prioritize local data, then EnclaveSDK
        if os.path.exists(local_data_path) and os.path.isdir(local_data_path):
            post_log(f"Found local dataset at {local_data_path}, using it directly.")
            # Ensure the data_dir variable used by data_split points to this local path
            # This is already the default for data_dir, so no change needed if local_data_path matches global data_dir
            if data_dir != local_data_path:
                 # This case should ideally not happen if we standardize on local_data_path for local check
                 post_log(f"Warning: Global data_dir \"{data_dir}\" differs from local_data_path \"{local_data_path}\". Using {local_data_path}.", status="In Progress")
                 # data_split will use its own data_dir argument, which we will set to local_data_path
                 pass # No direct assignment needed here, but data_split call will use local_data_path value

        else:
            post_log(f"Local dataset not found at {local_data_path}. Attempting to fetch via EnclaveSDK.")
            if not sas_url and not enclave_url.startswith("https://localhost"):
                 post_log("SAS_URL is not configured and ENCLAVE_URL does not look like a local debug endpoint. This is expected in a production enclave. Data must be provisioned by the Data Steward.", status="In Progress")
                 # In a true enclave, files would be pre-provisioned. If list_files returns empty, it means no data from DS.
            elif not sas_url:
                post_log("SAS_URL is not configured. Cannot fetch data for sandbox/local testing without it if data isn't already present locally.", status="Failed")
                # Potentially raise an error or exit if data is critical and not found locally and no SAS_URL for sandbox
                raise ValueError("SAS_URL must be set for Sandbox/remote data fetching if local data is not present.")

            post_log(f"Fetching files using EnclaveSDK...")
            if sas_url:
                post_log(f"SAS URL is configured (first 50 chars): {sas_url[:50]}...")
            
            files = list_files(sas_url=sas_url)
            if not files:
                post_log("No files found via EnclaveSDK. Ensure data is uploaded to Azure Blob container for Sandbox or provisioned by Data Steward in enclave.", status="Failed")
                raise FileNotFoundError("No data files found via EnclaveSDK.")
            post_log(f"Found {len(files)} files to process via EnclaveSDK")

            for idx, file in enumerate(files, 1):
                post_log(f"Processing file {idx}/{len(files)}: {file.name}")
                file_content = download_file(file.name, sas_url=sas_url)
                if file_content:
                    data_io = BytesIO(file_content)
                    with zipfile.ZipFile(data_io, "r") as zip_ref:
                        # Ensure extraction happens into the root, so Dataset_BUSI_with_GT is at ./Dataset_BUSI_with_GT
                        zip_ref.extractall("./") 
                    post_log(f"Successfully extracted {file.name} to ./ ")
                else:
                    post_log(f"Failed to download {file.name}", status="In Progress")
            
            # After extraction, the data should be at local_data_path
            if not os.path.exists(local_data_path):
                post_log(f"Data extraction did not result in expected path: {local_data_path}", status="Failed")
                raise FileNotFoundError(f"Extracted data not found at {local_data_path}")

        post_log("Preparing data loaders")
        
        # Add logging to clear_working_dir
        post_log(f"Contents before clear_working_dir: {os.listdir('.')}")
        clear_working_dir()
        
        post_log(f"Current after clearning working directory: {os.getcwd()}")
        
        # data_split will use the data_dir argument passed to it.
        # If local data was found, it uses local_data_path. If downloaded, it should also be at local_data_path.
        check_data_directory(local_data_path) # Check the standardized path
        data_split(data_dir=local_data_path)  # Explicitly use local_data_path
        dataloaders, dataset_sizes = make_dataloaders()
        post_log(f"Dataset sizes: {dataset_sizes}")

        post_log("Starting MLflow run")
        
        with mlflow.start_run():
            post_log("Logging training parameters to MLflow")
            training_parameters = {
                "Batch Size": batch_size,
                "Epochs": epochs,
                "Patience": patience,
                "Learning Rate": lr,
                "Step Size": step_size,
                "Gamma": gamma,
                "Accelerator": device.type
            }
            mlflow.log_params(training_parameters)

            post_log("Initializing model and starting training")
            model, model_info, class_rep = training_loop(
                Resnet_fineTuning,
                Loss_Function,
                optimizer,
                Decay_Learning_Rate,
                dataloaders,
                dataset_sizes,
                class_names,
                device,
                num_epochs=epochs,
                patience=patience,
                training_parameters=training_parameters,
            )

            post_log("Training completed, logging metrics")
            if isinstance(class_rep, dict):
                for class_name, metrics in class_rep.items():
                    if isinstance(metrics, dict):
                        for metric_name, value in metrics.items():
                            metric_key = f"{class_name}_{metric_name}"
                            mlflow.log_metric(metric_key, value)
                            post_log(f"Logged metric: {metric_key} = {value}")

            post_log("Saving model to MLflow")
            mlflow.pytorch.log_model(model, "breast_cancer_model")

            if os.path.exists("training_plot.png"):
                post_log("Logging training plot")
                mlflow.log_artifact("training_plot.png")

        post_log("Preparing final report")
        finalReport = {
            "json_data": {"report": class_rep},
            "name": "Breast Cancer Training",
            "status": "Completed",
        }
        post_report(finalReport)
        post_log("Training pipeline completed successfully", status="Completed")

    except Exception as e:
        import traceback
        error_msg = f"Training pipeline failed: {str(e)}\n{traceback.format_exc()}"
        post_log(error_msg, status="Failed")
        mlflow.end_run(status="FAILED")
        raise

if __name__ == "__main__":
    try:
        post_log("Initializing breast cancer detection pipeline")
        main()
    except Exception as e:
        post_log(f"Fatal error in main pipeline: {str(e)}", status="Failed")
        sys.exit(1)
