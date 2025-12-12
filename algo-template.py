import EnclaveSDK
import os
import base64

enclave_url = os.getenv("ENCLAVE_URL", "https://enclaveapi.escrow.beekeeperai.com")
api_client = EnclaveSDK.ApiClient(EnclaveSDK.Configuration(enclave_url))

# =============================================================================
# STORAGE CONFIGURATION
# Set environment variables for your storage provider (Azure OR S3)
#
# For Azure: SAS_URL (and optionally WRITEBACK_URL for separate write storage)
# For S3:    S3_REGION, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, S3_BUCKET_NAME
#            (and optionally S3_WRITEBACK_BUCKET_NAME for separate write storage)
# =============================================================================

# Check which storage provider is configured
s3_region = os.getenv("S3_REGION")
sas_url = os.getenv("SAS_URL")

if s3_region:
    # S3 Configuration for reading data
    storage_params = {
        "s3_region": s3_region,
        "s3_access_key_id": os.getenv("S3_ACCESS_KEY_ID"),
        "s3_secret_access_key": os.getenv("S3_SECRET_ACCESS_KEY"),
        "s3_bucket_name": os.getenv("S3_BUCKET_NAME"),
        "s3_prefix": os.getenv("S3_PREFIX", ""),
    }
    # For writeback: allow separate credentials and bucket
    writeback_params = {
        "s3_region": os.getenv("S3_WRITEBACK_REGION", s3_region),
        "s3_access_key_id": os.getenv("S3_WRITEBACK_ACCESS_KEY_ID", os.getenv("S3_ACCESS_KEY_ID")),
        "s3_secret_access_key": os.getenv("S3_WRITEBACK_SECRET_ACCESS_KEY", os.getenv("S3_SECRET_ACCESS_KEY")),
        "s3_bucket_name": os.getenv("S3_WRITEBACK_BUCKET_NAME", os.getenv("S3_BUCKET_NAME")),
        "s3_prefix": os.getenv("S3_WRITEBACK_PREFIX", ""),
    }
    print("Using S3 storage")

elif sas_url:
    # Azure Configuration
    sas_url_b64 = base64.b64encode(sas_url.encode()).decode()
    storage_params = {"sas_url": sas_url_b64}

    # For writeback: use WRITEBACK_URL if set, otherwise same as read
    writeback_url = os.getenv("WRITEBACK_URL", sas_url)
    writeback_url_b64 = base64.b64encode(writeback_url.encode()).decode()
    writeback_params = {"sas_url": writeback_url_b64}
    print("Using Azure storage")

else:
    print("Error: Set SAS_URL (Azure) or S3_REGION (S3) environment variables")
    exit(1)


def main():
    """Main function demonstrating all EnclaveSDK operations"""

    ###
    # 1. List available data files
    ###
    api_data = EnclaveSDK.DataApi(api_client)
    response = api_data.api_v1_data_files_get(**storage_params)
    print(f"Found {len(response.files)} data files:")
    for f in response.files[:5]:
        print(f"  - {f.name}")

    ###
    # 2. Fetch a data file
    ###
    if response.files:
        file_content = api_data.api_v1_data_file_get(response.files[0].name, **storage_params)
        print(f"Downloaded: {response.files[0].name}")

    ###
    # 3. Post a log message
    ###
    api_log = EnclaveSDK.LogApi(api_client)
    api_log.api_v1_log_post(EnclaveSDK.LogData(message="Starting algorithm", status="In Progress"))
    print("Posted log message")

    ###
    # 4. Writeback: Create a file (POST)
    ###
    api_writeback = EnclaveSDK.WritebackApi(api_client)
    write_request = EnclaveSDK.WriteFileRequest(
        content="Hello from writeback!",
        content_type="text/plain",
        overwrite=False
    )
    response = api_writeback.api_v1_writeback_file_post(
        write_file_request=write_request,
        filepath="algorithm-outputs/test-output.txt",
        **writeback_params
    )
    print(f"Created file: {response.filepath}")

    ###
    # 5. Writeback: List files
    ###
    response = api_writeback.api_v1_writeback_files_get(**writeback_params)
    print(f"Writeback storage has {len(response.files)} files")

    ###
    # 6. Writeback: Read a file (GET)
    ###
    content = api_writeback.api_v1_writeback_file_get(
        filepath="algorithm-outputs/test-output.txt",
        **writeback_params
    )
    print(f"Read back content: {content[:50] if len(content) > 50 else content}")

    ###
    # 7. Writeback: Update a file (PUT)
    ###
    write_request = EnclaveSDK.WriteFileRequest(
        content="Updated content!",
        content_type="text/plain",
        overwrite=True
    )
    response = api_writeback.api_v1_writeback_file_put(
        write_file_request=write_request,
        filepath="algorithm-outputs/test-output.txt",
        **writeback_params
    )
    print(f"Updated file: {response.filepath}")

    ###
    # 8. Writeback: Delete a file (DELETE)
    ###
    api_writeback.api_v1_writeback_file_delete(
        filepath="algorithm-outputs/test-output.txt",
        **writeback_params
    )
    print("Deleted file: algorithm-outputs/test-output.txt")

    ###
    # 9. Upload an artifact (image, chart, etc.)
    ###
    # Uncomment to upload a file as a report artifact:
    # api_report = EnclaveSDK.ReportApi(api_client)
    # with open("chart.png", "rb") as f:
    #     api_report.api_v1_report_artifact_post(artifact_file=f)
    # print("Uploaded artifact")

    ###
    # 10. Validate a report
    ###
    api_report = EnclaveSDK.ReportApi(api_client)
    report = {
        "json_data": {"report": {"result": "success", "score": 0.95}},
        "json_schema": {"report": {"type": "dict", "allow_unknown": True}},
        "name": "Algorithm Results",
        "status": "Completed"
    }
    validation = api_report.api_v1_validate_post(EnclaveSDK.Report.from_dict(report))
    print(f"Validation: {validation.status}")

    ###
    # 11. Post final report
    ###
    api_log.api_v1_log_post(EnclaveSDK.LogData(message="Algorithm complete", status="Completed"))

    final_report = {
        "json_data": {"report": {"result": "success", "score": 0.95}},
        "name": "Algorithm Results",
        "status": "Completed"
    }
    api_report.api_v1_report_post(EnclaveSDK.Report.from_dict(final_report))
    print("Posted final report")


if __name__ == "__main__":
    main()
