import EnclaveSDK
import os
import base64

enclave_url = os.getenv("ENCLAVE_URL", "https://enclaveapi.escrow.beekeeperai.com")
configuration = EnclaveSDK.Configuration(enclave_url)

# Use the SAS_URL environment variables to use the Data API in the Sandbox, otherwise default to None
sas_url = os.getenv("SAS_URL", None)
if sas_url:
    sas_url = base64.b64encode(sas_url.encode()).decode()

api_client = EnclaveSDK.ApiClient(configuration)

def main():
    """Main function demonstrating how to use EnclaveSDK"""
    
    #### 
    # 1. List available data files
    ###
    # Create an instance of Data API class and list files in blob storage
    api_data_instance = EnclaveSDK.DataApi(api_client)
    api_response = api_data_instance.api_v1_data_files_get(sas_url=sas_url)
    
    ###
    # 2. Fetch data files
    ###
    for file in api_response.files:
      file_content = api_data_instance.api_v1_data_file_get(file.name, sas_url=sas_url)
      print(file.name)

    ### 
    # 3. Post a log message
    ###
    api_log_instance = EnclaveSDK.LogApi(api_client)
    api_response = api_log_instance.api_v1_log_post(EnclaveSDK.LogData(message="Log message from algo-template.py"))

    ###
    # 4. Validate a report with in-line schema
    ###
    api_report_instance = EnclaveSDK.ReportApi(api_client)
    report = {"json_data": {"report": "Performance Report"},
              "json_schema": { 
                "report": { "type": "string",
               "allowed": [ "Performance Report" ] } 
               },
              "name": "EscrowAI Algorithm Package", 
              "status": "Completed"}
    api_response = api_report_instance.api_v1_validate_post(EnclaveSDK.Report.from_dict(report))

    ###
    # 5. Post report
    ###
    # Create an instance of Report API class
    api_report_instance = EnclaveSDK.ReportApi(api_client)
    report = {"json_data": {"report": "Performance Report"}, 
              "name": "EscrowAI Algorithm Package", 
              "status": "Completed"}
    api_response = api_report_instance.api_v1_report_post(EnclaveSDK.Report.from_dict(report))

if __name__ == "__main__":
    main()