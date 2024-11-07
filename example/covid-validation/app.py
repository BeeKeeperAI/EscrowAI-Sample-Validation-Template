import io
import os
import json
import pandas as pd
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
# Use the SAS_URL environment variables to use the Data API in the Sandbox, otherwise default to None
sas_url = os.getenv("SAS_URL", None) 
if sas_url:
    sas_url = base64.b64encode(sas_url.encode()).decode()

# Finalize the creation of your API client
api_client = EnclaveSDK.ApiClient(configuration)

# Use the Data API class to get a list of files in the Blob container
def get_file_list(sas_url=None) -> List[File]:
    api_instance = EnclaveSDK.DataApi(api_client)
    api_response = api_instance.api_v1_data_files_get(sas_url=sas_url)

    return api_response.files

# Use the Data API class to securely decrypt and download a file give the `.name` attribute of the files list
def download_file(file_name: str, sas_url=None) -> ByteString:
    api_instance = EnclaveSDK.DataApi(api_client)
    content = api_instance.api_v1_data_file_get(file_name, sas_url=sas_url)

    return content

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
    files = get_file_list(sas_url=sas_url)
    results = []
    if files:
        for file in files:
            if file.name.split("/")[0] != "covid" and file.name.split("/")[0] != "nofinding" and file.name.split("/")[0] != "pneumonia":
                post_log({"message": f"When looking for the data labels in the parent folder name of covid/nofinding/pneumonia, this file ({file.name}) was not correctly labeled", "status": "In Progress"})

            file_content = download_file(file.name, sas_url=sas_url)
            if file_content:                
                pred_class = getPred(model, file_content)
                if(pred_class == ""):
                    post_log({"message": f"The model did not return a prediction for the file ({file.name})", "status": "In Progress"})
                    continue
                actual_class = file.name.split('/')[0]
                if(pred_class == "nofinding" or pred_class == "pneumonia"):
                    reducedResult = "nofinding"
                else:
                    reducedResult = "covid"
                if(actual_class == "nofinding" or actual_class== "pneumonia"):
                    reducedActual = "nofinding"
                else:
                    reducedActual = "covid"

                results.append({'blob.name':file.name, 'actual':reducedActual, 'prediction':reducedResult})

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