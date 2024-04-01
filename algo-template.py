import EnclaveSDK

# Set the code to access the Enclave API inside the enclave as follows:
configuration = EnclaveSDK.Configuration("https://localhost:5000")
api_client = EnclaveSDK.ApiClient(configuration)

def main():
    """Main function demonstrating how to use EnclaveSDK"""
    
    #### 
    # 1. List available data files
    ###
    # Create an instance of Data API class and list files in blob storage
    api_data_instance = EnclaveSDK.DataApi(api_client)
    api_response = api_data_instance.api_v1_data_files_get()
    
    ###
    # 2. Fetch data files
    ###
    for file in api_response.files:
      api_response = api_data_instance.api_v1_data_file_get(file.name)
      break

    ### 
    # 3. Post a log message
    ###
    api_log_instance = EnclaveSDK.LogApi(api_client)
    api_response = api_log_instance.api_v1_log_post(EnclaveSDK.LogData(message="Log message from algo-template.py"))
  
    ###
    # 4. Post report
    ###
    # Create an instance of Report API class
    api_report_instance = EnclaveSDK.ReportApi(api_client)
    report = {"json_data": {"report": "Performance Report"}, 
              "name": "EscrowAI Algorithm Package", 
              "status": "Completed"}
    api_response = api_report_instance.api_v1_report_post(EnclaveSDK.Report.from_dict(report))

if __name__ == "__main__":
    main()