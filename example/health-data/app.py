import os
import json
import base64
import pandas as pd
from typing import List, Dict
import EnclaveSDK
from EnclaveSDK import File, Report, LogData

# Configuration
configuration = EnclaveSDK.Configuration(os.getenv("ENCLAVE_URL", "https://enclaveapi.escrow.beekeeperai.com/"))

# SAS URL for data access
sas_url = os.getenv("SAS_URL", None)
if sas_url:
    sas_url = base64.b64encode(sas_url.encode()).decode()

api_client = EnclaveSDK.ApiClient(configuration)

# Age buckets configuration
AGE_BINS = [0, 12, 18, 30, 45, 60, 75, 120]
AGE_LABELS = ["0–12", "13–18", "19–30", "31–45", "46–60", "61–75", "76+"]

def post_log(log: Dict) -> Dict:
    api_instance = EnclaveSDK.LogApi(api_client)
    log_obj = LogData.from_dict(log)
    api_response = api_instance.api_v1_log_post(log_obj)
    return api_response

def get_file_list(sas_url=None) -> List[File]:
    api_instance = EnclaveSDK.DataApi(api_client)
    api_response = api_instance.api_v1_data_files_get(sas_url=sas_url)
    return api_response.files

def download_file(file_name: str, sas_url=None) -> bytes:
    api_instance = EnclaveSDK.DataApi(api_client)
    content = api_instance.api_v1_data_file_get(file_name, sas_url=sas_url)
    return content

def post_report(finalReport: Dict) -> Dict:
    api_instance = EnclaveSDK.ReportApi(api_client)
    
    # Check if validation.json is available
    if os.path.exists("validation.json"):
        with open("validation.json", "r") as schema:
            finalReport['json_schema'] = EnclaveSDK.ReportJsonSchema.from_dict(json.load(schema))
    
    report = Report.from_dict(finalReport)
    api_response = api_instance.api_v1_report_post(report)
    return api_response

def analyze_healthcare_data(csv_content: bytes) -> Dict:
    """
    Analyze healthcare CSV data and create age/gender distribution.
    """
    try:
        # Read CSV from bytes
        from io import BytesIO
        dataset = pd.read_csv(BytesIO(csv_content))
        
        post_log({"message": f"Loaded dataset with {len(dataset)} rows", "status": "In Progress"})
        
        # Validate required columns
        required_columns = ["Age", "Gender"]
        missing_columns = [col for col in required_columns if col not in dataset.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Create age buckets
        dataset["AgeBucket"] = pd.cut(
            dataset["Age"],
            bins=AGE_BINS,
            labels=AGE_LABELS,
            right=True,
            include_lowest=True
        )
        
        post_log({"message": "Age buckets created successfully", "status": "In Progress"})
        
        # Group by Gender and AgeBucket
        counts = dataset.groupby(["Gender", "AgeBucket"]).size()
        
        # Unstack to create the pivot table
        pivot_table = counts.unstack(fill_value=0)
        
        post_log({"message": f"Grouped data by Gender and AgeBucket", "status": "In Progress"})
        
        # Convert to report format
        report_data = {
            "total_records": len(dataset),
            "age_gender_distribution": {}
        }
        
        # Add each gender's distribution
        for gender in pivot_table.index:
            report_data["age_gender_distribution"][gender] = {}
            for age_bucket in AGE_LABELS:
                if age_bucket in pivot_table.columns:
                    count = int(pivot_table.loc[gender, age_bucket])
                    report_data["age_gender_distribution"][gender][age_bucket] = count
                else:
                    report_data["age_gender_distribution"][gender][age_bucket] = 0
        
        # Add summary statistics
        report_data["summary"] = {
            "unique_genders": len(pivot_table.index),
            "age_buckets": len(AGE_LABELS),
            "gender_totals": {}
        }
        
        for gender in pivot_table.index:
            total = int(pivot_table.loc[gender].sum())
            report_data["summary"]["gender_totals"][gender] = total
        
        post_log({"message": "Report data generated successfully", "status": "In Progress"})
        
        return report_data
        
    except Exception as e:
        post_log({"message": f"Error analyzing healthcare data: {str(e)}", "status": "Failed"})
        raise

def main():
    post_log({"message": "Starting Healthcare Data Analysis", "status": "In Progress"})
    
    # Get list of files from blob storage
    files = get_file_list(sas_url=sas_url)
    
    if not files:
        post_log({"message": "No files found in blob storage", "status": "Failed"})
        return
    
    post_log({"message": f"Found {len(files)} files in blob storage", "status": "In Progress"})
    
    # Find CSV file
    csv_file = None
    for file in files:
        if file.name.lower().endswith('.csv') or file.name.lower().endswith('.csv.bkenc'):
            csv_file = file
            break
    
    if not csv_file:
        post_log({"message": "No CSV file found in blob storage", "status": "Failed"})
        return
    
    post_log({"message": f"Processing file: {csv_file.name}", "status": "In Progress"})
    
    # Download CSV file (SDK will automatically decrypt .bkenc files)
    csv_content = download_file(csv_file.name, sas_url=sas_url)
    
    if not csv_content:
        post_log({"message": f"Failed to download file: {csv_file.name}", "status": "Failed"})
        return
    
    # Analyze the data
    report_data = analyze_healthcare_data(csv_content)
    
    # Create final report
    finalReport = {
        "json_data": {
            "report": report_data
        },
        "name": "Healthcare Age-Gender Distribution Report",
        "status": "Completed"
    }
    
    post_log({"message": f"Posting report with {report_data['total_records']} records analyzed", "status": "In Progress"})
    
    try:
        post_report(finalReport)
        post_log({"message": "Report posted successfully", "status": "Completed"})
    except Exception as e:
        post_log({"message": f"Failed to post report: {str(e)}", "status": "Failed"})

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        post_log({"message": f"Fatal error: {str(e)}", "status": "Failed"})
        raise
