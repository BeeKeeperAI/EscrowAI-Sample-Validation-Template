# The data set used in this example is from http://archive.ics.uci.edu/ml/datasets/Wine+Quality
# P. Cortez, A. Cerdeira, F. Almeida, T. Matos and J. Reis.
# Modeling wine preferences by data mining from physicochemical properties. In Decision Support Systems, Elsevier, 47(4):547-553, 2009.

import logging
import sys
import os
import warnings
from urllib.parse import urlparse
from io import BytesIO
from typing import Dict, List, ByteString
import base64

import numpy as np
import pandas as pd
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
import EnclaveSDK
from EnclaveSDK import File

logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)

try:
    #mlflow.set_tracking_uri(os.environ['ESCROW_TRACKING_URI'])
    mlflow.set_experiment("Wine-Quality-Enclave-New")
except KeyError as e:
    logger.exception("Error in setting experiment: %s", e)
    sys.exit(1)

# Use the SAS_URL environment variables to use the Data API in the Sandbox, otherwise default to None
sas_url = os.getenv("SAS_URL", None) 
if sas_url:
    # Remove any escaping of special characters
    sas_url = sas_url.replace('\\', '')
    # Encode the cleaned URL
    sas_url = base64.b64encode(sas_url.encode()).decode()

try:
    configuration = EnclaveSDK.Configuration(os.getenv("ENCLAVE_URL", "https://enclaveapi.escrow.beekeeperai.com/"))
    api_client = EnclaveSDK.ApiClient(configuration)
except Exception as e:
    logger.exception("Failed to configure EnclaveSDK: %s", e)
    sys.exit(1)

def get_file_list() -> List[EnclaveSDK.File]:
    api_instance = EnclaveSDK.DataApi(api_client)
    api_response = api_instance.api_v1_data_files_get(sas_url=sas_url)
    return api_response.files

def download_file(file_name: str):
    api_instance = EnclaveSDK.DataApi(api_client)
    content = api_instance.api_v1_data_file_get(file_name, sas_url=sas_url)
    return content

def eval_metrics(actual, pred):
    try:
        rmse = np.sqrt(mean_squared_error(actual, pred))
        mae = mean_absolute_error(actual, pred)
        r2 = r2_score(actual, pred)
        return rmse, mae, r2
    except Exception as e:
        logger.exception("Error evaluating metrics: %s", e)
        post_log({"status": "Failed", "message": f"Error evaluating metrics: {e}"})
        return None, None, None

def post_report(finalReport):
    """
    Post a report to the server for submission.

    :param finalReport: The final report as a JSON object.
    :return: The server response as a JSON object.
    """
    # Create an instance of Report API class
    try:
        api_instance = EnclaveSDK.ReportApi(api_client)
        report = EnclaveSDK.Report.from_dict(finalReport)
        api_response = api_instance.api_v1_report_post(report)
        return api_response
    except Exception as e:
        logger.exception("Error posting report: %s", e)
        post_log({"status": "Failed", "message": f"Error posting report: {e}"})
        return None
    
def post_log(log: Dict) -> Dict:
    # Create an instance of Log API class
    api_instance = EnclaveSDK.LogApi(api_client)

    # Use the Log model to create a log object for posting
    # the posted log will be validated against the DS-provided
    # validation schema
    print(log)
    log = EnclaveSDK.LogData.from_dict(log)
    api_response = api_instance.api_v1_log_post(log)
    return api_response    

if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    np.random.seed(40)

    try:
        # First get list of available files
        files = get_file_list()
        target_file = None
        
        # Look for the wine quality file
        for file in files:
            if 'winequality-red.csv' in file.name:
                target_file = file.name
                break
                
        if not target_file:
            error_msg = "Could not find winequality-red.csv in available files"
            logger.error(error_msg)
            post_log({"status": "Failed", "message": error_msg})
            sys.exit(1)
            
        file_content = download_file(target_file)
        if file_content:
            data_io = BytesIO(file_content)
            data = pd.read_csv(data_io, sep=";")
            post_log({"status": "In Progress", "message": "Successfully loaded wine quality data"})
    except Exception as e:
        logger.exception("Error reading data: %s", e)
        post_log({"status": "Failed", "message": f"Error reading data: {e}"})
        sys.exit(1)

    try:
        # Split the data into training and test sets. (0.75, 0.25) split.
        train, test = train_test_split(data)

        # The predicted column is "quality" which is a scalar from [3, 9]
        train_x = train.drop(["quality"], axis=1)
        test_x = test.drop(["quality"], axis=1)
        train_y = train[["quality"]]
        test_y = test[["quality"]]
    except Exception as e:
        logger.exception("Error with data preparation: %s", e)
        post_log({"status": "Failed", "message": f"Error with data preparation: {e}"})
        sys.exit(1)

    # Reading in run parameters entered when a send run request is clicked
    try:
        alpha = float(os.getenv('alpha', 0.3))
        l1_ratio = float(os.getenv('l1_ratio', 0.8))
    except KeyError as e:
        logger.exception("Alpha or l1_ratio environment variable not set: %s", e)
        post_log({"status": "Failed", "message": f"Alpha or l1_ratio environment variable not set: {e}"})
        sys.exit(1)
    except ValueError as e:
        logger.exception("Invalid value for alpha or l1_ratio: %s", e)
        post_log({"status": "Failed", "message": f"Invalid value for alpha or l1_ratio: {e}"})
        sys.exit(1)

    try:
        lr = ElasticNet(alpha=alpha, l1_ratio=l1_ratio, random_state=42)
        lr.fit(train_x, train_y)
        predicted_qualities = lr.predict(test_x)
    except Exception as e:
        logger.exception("Error training or predicting with model: %s", e)
        post_log({"status": "Failed", "message": f"Error training or predicting with model: {e}"})
        sys.exit(1)

    try:
        rmse, mae, r2 = eval_metrics(test_y, predicted_qualities)
        logger.info(f"Elasticnet model (alpha={alpha:f}, l1_ratio={l1_ratio:f}):")
        logger.info(f"  RMSE: {rmse}")
        logger.info(f"  MAE: {mae}")
        logger.info(f"  R2: {r2}")
    except Exception as e:
        logger.exception("Error in model evaluation: %s", e)
        post_log({"status": "Failed", "message": f"Error in model evaluation: {e}"})
        sys.exit(1)

    try:
        # Sending the run parameters to MLFlow
        mlflow.log_param("alpha", alpha)
        mlflow.log_param("l1_ratio", l1_ratio)
        # Sending the netrics to MLFlow
        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("r2", r2)
        mlflow.log_metric("mae", mae)

        predictions = lr.predict(train_x)
        signature = infer_signature(train_x, predictions)
        tracking_url_type_store = urlparse(mlflow.get_tracking_uri()).scheme

       # Model registry does not work with file store
        if tracking_url_type_store != "file":
           # Register the model
           # There are other ways to use the Model Registry, which depends on the use case,
           # please refer to the doc for more information:
           # https://mlflow.org/docs/latest/model-registry.html#api-workflow
            
            mlflow.sklearn.log_model(
                lr, "model", registered_model_name="ElasticnetWineModel", signature=signature
            )
        else:
            mlflow.sklearn.log_model(lr, "model", signature=signature)
    except Exception as e:
        logger.exception("Error logging to MLflow: %s", e)
        post_log({"status": "Failed", "message": f"Error logging to MLflow: {e}"})
        mlflow.end_run(mlflow.entities.RunStatus.FAILED)
        sys.exit(1)
    
    mlflow.end_run()

    try:
        dummy_data = "Wine experiment"

        json_data = {
            "report": dummy_data,
        }

        finalReport = {
            "json_data": json_data,
            "name": "Sklearn Model",
            "status": "Completed",
        }
        
        response = post_report(finalReport)
        logger.info(f"Report posted successfully: {response}")
    except Exception as e:
        logger.exception("Error constructing or posting final report: %s", e)
        post_log({"status": "Failed", "message": f"Error constructing or posting final report: {e}"})
        sys.exit(1)
