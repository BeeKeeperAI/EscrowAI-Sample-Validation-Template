import io
import os
import json
import pandas as pd
from urllib.parse import urlparse
from fastai.learner import load_learner
from fastai.vision import *
from fastai.vision.core import *
from io import BytesIO
from sklearn.metrics import accuracy_score, recall_score,confusion_matrix
from cmath import sqrt
from typing import List, Dict, ByteString
import base64
import EnclaveSDK
from EnclaveSDK import File, Report, LogData

# Use the ENCLAVE_URL environment variable to create an SDK configuration for the Sandbox
configuration = EnclaveSDK.Configuration(os.getenv("ENCLAVE_URL", "https://enclaveapi.escrow.beekeeperai.com/"))

# Writeback URL configuration - read from V1 folder
WRITEBACK_URL_RAW = os.getenv("WRITEBACK_URL", None)
WRITEBACK_URL_B64 = None
if WRITEBACK_URL_RAW:
    WRITEBACK_URL_RAW = WRITEBACK_URL_RAW.strip().strip('"')
    WRITEBACK_URL_B64 = base64.b64encode(WRITEBACK_URL_RAW.encode()).decode()

# Finalize the creation of your API client
api_client = EnclaveSDK.ApiClient(configuration)
writeback_api = EnclaveSDK.WritebackApi(api_client)

# Use the Data API class to get a list of files in the Blob container
def get_file_list(sas_url=None) -> List[File]:
    api_instance = EnclaveSDK.DataApi(api_client)
    api_response = api_instance.api_v1_data_files_get(sas_url=sas_url)
    return api_response.files

# Use the Data API class to securely decrypt and download a file
def download_file(file_name: str, sas_url=None) -> ByteString:
    api_instance = EnclaveSDK.DataApi(api_client)
    content = api_instance.api_v1_data_file_get(file_name, sas_url=sas_url)
    return content

# Download file from writeback storage
def download_from_writeback(file_path: str, writeback_url_b64: str = None) -> bytes:
    """Download a file from writeback storage"""
    try:
        content = writeback_api.api_v1_writeback_file_get(
            file_path,
            sas_url=writeback_url_b64
        )
        
        # Ensure content is bytes
        if not isinstance(content, bytes):
            content = content.encode('utf-8')
        
        return content
    except Exception as e:
        post_log({"message": f"Error downloading {file_path} from writeback: {str(e)}", "status": "Failed"})
        raise

def get_v1_files_from_writeback(writeback_url_b64: str = None) -> List[str]:
    """
    Get list of files from V1 folder in writeback storage.
    Uses WritebackApi list endpoint to discover files.
    """
    try:
        post_log({"message": "Listing files from writeback storage", "status": "In Progress"})
        
        # Log writeback URL info
        if writeback_url_b64:
            post_log({"message": f"Using writeback URL (base64 length: {len(writeback_url_b64)})", "status": "In Progress"})
        else:
            post_log({"message": "No writeback URL provided (writeback_url_b64 is None)", "status": "In Progress"})
        
        # Use WritebackApi to list all files
        post_log({"message": "Calling api_v1_writeback_files_get...", "status": "In Progress"})
        api_response = writeback_api.api_v1_writeback_files_get(
            sas_url=writeback_url_b64
        )
        
        # Log raw response type and content
        post_log({"message": f"API response type: {type(api_response)}", "status": "In Progress"})
        post_log({"message": f"API response: {str(api_response)[:500]}", "status": "In Progress"})
        
        # Extract file list from response
        # API returns an SDK object with 'files' attribute (list of File objects)
        all_files = []
        
        # Try to access as SDK object first
        if hasattr(api_response, 'files'):
            post_log({"message": f"Response has 'files' attribute", "status": "In Progress"})
            all_files = api_response.files  # Access the files attribute directly
            post_log({"message": f"Got {len(all_files)} files from response.files attribute", "status": "In Progress"})
        elif isinstance(api_response, dict):
            post_log({"message": f"Response is dict with keys: {list(api_response.keys())}", "status": "In Progress"})
            all_files = api_response.get('files', [])
        else:
            post_log({"message": f"Response type not recognized, trying to access files", "status": "In Progress"})
        
        post_log({"message": f"Extracted {len(all_files)} file objects from response", "status": "In Progress"})
        
        # Log first few files for debugging
        if all_files:
            for i, f in enumerate(all_files[:3]):
                post_log({"message": f"File {i}: type={type(f)}, name={getattr(f, 'name', 'N/A')}", "status": "In Progress"})
        
        # Filter for V1 files - each file is a File object with 'name' attribute
        v1_files = []
        for f in all_files:
            # File objects have .name attribute
            if hasattr(f, 'name'):
                file_name = f.name
                if file_name.startswith('V1/'):
                    v1_files.append(file_name)
            elif isinstance(f, dict):
                file_name = f.get('name', '')
                if file_name.startswith('V1/'):
                    v1_files.append(file_name)
            else:
                post_log({"message": f"Unexpected file type: {type(f)}, value: {str(f)[:100]}", "status": "In Progress"})
        
        post_log({"message": f"Found {len(v1_files)} files in V1 folder (total files: {len(all_files)})", "status": "In Progress"})
        
        # Debug logging
        if len(all_files) > 0 and len(v1_files) == 0:
            sample_names = []
            for f in all_files[:5]:
                if hasattr(f, 'name'):
                    sample_names.append(f.name)
                elif isinstance(f, dict):
                    sample_names.append(f.get('name', 'N/A'))
                else:
                    sample_names.append(str(f))
            post_log({"message": f"No V1 files found. Sample file names: {sample_names}", "status": "In Progress"})
        elif len(v1_files) > 0:
            sample_v1 = v1_files[:3]
            post_log({"message": f"Sample V1 files: {sample_v1}", "status": "In Progress"})
        
        return v1_files
            
    except Exception as e:
        post_log({"message": f"Error listing files from writeback: {str(e)}", "status": "Failed"})
        post_log({"message": f"Exception type: {type(e).__name__}", "status": "Failed"})
        import traceback
        post_log({"message": f"Traceback: {traceback.format_exc()}", "status": "Failed"})
        return []

# Use the Log API class to post a log message
def post_log(log: Dict) -> Dict:
    # Create an instance of Log API class
    api_instance = EnclaveSDK.LogApi(api_client)

    # Use the Log model to create a log object for posting
    log = LogData.from_dict(log)
    api_response = api_instance.api_v1_log_post(log)

    return api_response

# Use the Report API to post a report
def post_report(finalReport: Dict) -> Dict:
    # Create an instance of Report API class
    api_instance = EnclaveSDK.ReportApi(api_client)

    # Check if schema.json is available and read it into json_schema
    if os.path.exists("schema.json"):
        with open("schema.json", "r") as schema:
            finalReport['json_schema'] = EnclaveSDK.ReportJsonSchema.from_dict(json.load(schema))

    # Use the Report model to create a report object for posting
    # the posted report will be validated against the DS-provided
    # validation schema
    report = Report.from_dict(finalReport)
    api_response = api_instance.api_v1_report_post(report)
    return api_response

# Get the folder the file is in for a label (for inference)
def label_func(x): return x.parent.name 

# Function to get the prediction
def getPred(model, file_content):
    uploadedImage = load_image(BytesIO(file_content)).reshape(256,256)

    # Convert RGBA to RGB if needed
    if uploadedImage.mode == 'RGBA':
        uploadedImage = PILImage(uploadedImage.convert('RGB'))
    # This will be either nofinding, pneumonia, or covid
    pred_class,pred_idx,outputs = model.predict(PILImage(uploadedImage))

    return pred_class

def generateReport(results):
    reportJSON = {}

    # Store the results in a StringIO object
    output = io.StringIO()

    # Create a DataFrame of the results and extract the actual and predicted values
    resultsDf = pd.DataFrame(results)
    if resultsDf.empty:
        post_log({"message": "No results to generate a report", "status": "Failed"})
    
    # Generate the test and prediction values
    y_test = resultsDf['actual'].tolist()
    y_pred = resultsDf['prediction'].tolist()
    
    try:
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    except ValueError as e:
        post_log({"message": f"Not enough data to calculate confusion matrix: {str(e)}", "status": "Failed"})
        exit(1)
        
    # Calculate the sample size
    n = len(y_test)

    try:
        # Calculate and print the accuracy with confidence interval 
        accuracy = accuracy_score(y_test, y_pred)
        accuracyCI = 1.96*(sqrt(accuracy)-(1-accuracy))/n
        print('Accuracy: {:.2f} ± {} (95% CI, n={})'.format(accuracy, round(abs(accuracyCI),4), n), file=output)
        if 'accuracy' not in reportJSON:
            reportJSON['accuracy'] = {}
        reportJSON['accuracy'] = {'value': accuracy, 'CI': round(abs(accuracyCI),4), 'n': n}

        # Calculate and print the specificity with confidence interval
        specificity = tn/(tn+fp)
        specificityCI = 1.96*(sqrt(specificity)-(1-specificity))/n
        print('Specificity: {:.2f} ± {} (95% CI, n={})'.format(specificity, round(abs(specificityCI),4), n), file=output)
        if 'specificity' not in reportJSON:
            reportJSON['specificity'] = {}
        reportJSON['specificity'] = {'value': specificity, 'CI': round(abs(specificityCI),4), 'n': n}

        # Calculate and print the sensitivity with confidence interval
        sensitivity = recall_score(y_test, y_pred, average='weighted')
        sensitivityCI = 1.96*(sqrt(sensitivity)-(1-sensitivity))/n
        print('Sensitivity: {:.2f} ± {} (95% CI, n={})'.format(sensitivity, round(abs(sensitivityCI),4), n), file=output)
        if 'sensitivity' not in reportJSON:
            reportJSON['sensitivity'] = {}
        reportJSON['sensitivity'] = {'value': sensitivity, 'CI': round(abs(sensitivityCI),4), 'n': n}
    except Exception as e:
        print(f"An error occurred while calculating metrics: {str(e)}")

    return reportJSON

def load_model():
    try:
        model = load_learner('models/multi-class-pg.pkl')
        post_log({"message": "Model loaded successfully", "status": "In Progress"})
        return model
    except Exception as e:
        post_log({"message": f"An error occurred while loading the model: {str(e)}", "status": "Failed"})
        exit(1) # Exit the script if the model fails to load

def main():
    model = load_model()
    
    post_log({"message": "Reading files from V1 folder in writeback location", "status": "In Progress"})
    
    # Get list of V1 files from writeback
    try:
        v1_file_paths = get_v1_files_from_writeback(WRITEBACK_URL_B64)
    except Exception as e:
        post_log({"message": f"Failed to get V1 file list: {str(e)}", "status": "Failed"})
        return
    
    if not v1_file_paths:
        post_log({"message": "No files found in V1 folder of writeback location", "status": "Failed"})
        return
    
    post_log({"message": f"Found {len(v1_file_paths)} files in V1 folder", "status": "In Progress"})
    
    results = []
    processed_count = 0
    error_count = 0
    
    for file_path in v1_file_paths:
        # Extract the folder structure from V1/subfolder/filename
        # Example: V1/covid/image.png -> covid
        path_parts = file_path.split('/')
        if len(path_parts) < 3:
            post_log({"message": f"File {file_path} does not have expected folder structure V1/label/filename", "status": "In Progress"})
            continue
        
        # The label is the folder between V1 and the filename
        actual_class = path_parts[1]  # e.g., 'covid', 'pneumonia', 'nofinding'
        
        if actual_class not in ["covid", "nofinding", "pneumonia"]:
            post_log({"message": f"File {file_path} has unexpected label: {actual_class}. Expected covid/nofinding/pneumonia", "status": "In Progress"})
            continue
        
        try:
            post_log({"message": f"Processing {file_path}", "status": "In Progress"})
            
            # Download file from writeback location
            file_content = download_from_writeback(file_path, WRITEBACK_URL_B64)
            
            if not file_content:
                post_log({"message": f"Failed to download file: {file_path}", "status": "In Progress"})
                error_count += 1
                continue
            
            pred_class = getPred(model, file_content)
            if pred_class == "":
                post_log({"message": f"The model did not return a prediction for the file ({file_path})", "status": "In Progress"})
                error_count += 1
                continue
            
            # Reduce classification to binary: covid vs nofinding
            if pred_class == "nofinding" or pred_class == "pneumonia":
                reducedResult = "nofinding"
            else:
                reducedResult = "covid"
            
            if actual_class == "nofinding" or actual_class == "pneumonia":
                reducedActual = "nofinding"
            else:
                reducedActual = "covid"

            results.append({'blob.name': file_path, 'actual': reducedActual, 'prediction': reducedResult})
            post_log({"message": f"Processed {file_path}: actual={reducedActual}, predicted={reducedResult}", "status": "In Progress"})
            processed_count += 1
            
        except Exception as e:
            post_log({"message": f"Error processing {file_path}: {str(e)}", "status": "In Progress"})
            error_count += 1

    post_log({"message": f"Processing complete - Success: {processed_count}, Errors: {error_count}", "status": "In Progress"})

    rawReport = {}
    rawReport['report'] = generateReport(results)

    print(json.dumps(rawReport, indent=4))
    finalReport = {
        "json_data": rawReport,
        "name": "COVID-19 X-Ray Classification Report",
        "status": "Completed",
    }
    post_report(finalReport)

if __name__ == "__main__":
    post_log({"message": "Starting the COVID-19 X-Ray Classification Report"})
    main()