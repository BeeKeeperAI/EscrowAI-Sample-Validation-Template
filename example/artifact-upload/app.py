import json
import os
from typing import List, Dict, ByteString
import EnclaveSDK
from EnclaveSDK import File, Report, LogData
from EnclaveSDK.rest import ApiException


# -----------------------------
# SDK client setup
# -----------------------------
configuration = EnclaveSDK.Configuration(os.getenv("ENCLAVE_URL", "https://localhost:5000"))
sas_url = None  # When testing locally, set to a real SAS URL to enable some functions
configuration.verify_ssl = False
# Optional bearer token for BearerAuth
_token = os.getenv("ESCROW_BEARER_TOKEN")
if _token:
    configuration.access_token = _token
api_client = EnclaveSDK.ApiClient(configuration)

# Artifact upload parameter is `artifact_file` per SDK docs (bytearray in multipart/form-data)
_ARTIFACT_PARAM = "artifact_file"

# -----------------------------
# Data API helpers
# -----------------------------
def get_file_list(sas_url=None) -> List[File]:
    api_instance = EnclaveSDK.DataApi(api_client)
    api_response = api_instance.api_v1_data_files_get(sas_url=sas_url)
    return api_response.files


def download_file(file_name: str, sas_url=None) -> ByteString:
    api_instance = EnclaveSDK.DataApi(api_client)
    content = api_instance.api_v1_data_file_get(file_name, sas_url=sas_url)
    return content

# -----------------------------
# Log API helper
# -----------------------------
def post_log(log: Dict) -> Dict:
    api_instance = EnclaveSDK.LogApi(api_client)
    log = LogData.from_dict(log)
    api_response = api_instance.api_v1_log_post(log)
    return api_response

# -----------------------------
# Report API helpers
# -----------------------------
def post_report(finalReport: Dict) -> Dict:
    api_instance = EnclaveSDK.ReportApi(api_client)
    report = Report.from_dict(finalReport)
    api_response = api_instance.api_v1_report_post(report)
    return api_response


def post_report_artifact(file_path_or_name: str) -> Dict:
    """
    Upload a single artifact either from local disk (default) or by downloading it
    from a SAS container first.

    If `sas_url` is provided, `file_path_or_name` is treated as the blob name inside
    that SAS container. We download bytes with `download_file(..., sas_url=...)`
    and upload them as the artifact.

    Otherwise, treat `file_path_or_name` as a local filesystem path.
    """
    api_instance = EnclaveSDK.ReportApi(api_client)

    def _strip_bkenc(name: str) -> str:
        name_l = name.lower()
        if name_l.endswith(".bkenc"):
            # remove only the final ".bkenc" suffix
            base = name[: -len(".bkenc")]
            # fallback safety: don't return empty
            return base or name
        return name

    # ---- Source selection: SAS vs local ----
    
    blob_name = file_path_or_name
    try:
        content_bytes = download_file(blob_name, sas_url=sas_url)
        if not content_bytes:
            raise FileNotFoundError(f"No content returned for blob: {blob_name}")
        original_filename = os.path.basename(blob_name) or "artifact"
        filename = _strip_bkenc(original_filename)
        if filename != original_filename:
            post_log({"message": f"[artifacts] (SAS) Using display name '{filename}' (stripped .bkenc from '{original_filename}')", "status": "In Progress"})
        else:
            post_log({"message": f"[artifacts] (SAS) Using display name '{filename}'", "status": "In Progress"})
        post_log({"message": f"[artifacts] (SAS) Downloaded: {blob_name} → bytes={len(content_bytes)}", "status": "In Progress"})
    except ApiException as e:
        body = getattr(e, "body", "").strip()
        status = getattr(e, "status", "")
        post_log({"message": f"[artifacts] (SAS) ApiException downloading {blob_name}: {status} {body}", "status": "Failed"})
        raise
    except Exception as e:
        post_log({"message": f"[artifacts] (SAS) Exception downloading {blob_name}: {e}", "status": "Failed"})
        raise
    
    # ---- Upload to Report API ----
    try:
        post_log({"message": f"[artifacts] Upload starting: {filename} (param=artifact_file, bytes={len(content_bytes)})", "status": "In Progress"})
        resp = api_instance.api_v1_report_artifact_post(artifact_file=(filename, content_bytes))
        post_log({"message": f"[artifacts] Uploaded: {filename}", "status": "In Progress"})
        return resp
    except ApiException as e:
        body = getattr(e, "body", "").strip()
        status = getattr(e, "status", "")
        post_log({"message": f"[artifacts] ApiException {filename}: {status} {body}", "status": "Failed"})
        raise
    except Exception as e:
        post_log({"message": f"[artifacts] Exception {filename}: {e}", "status": "Failed"})
        raise

def post_files_as_artifacts(sas_url: str = None) -> list:
    """
    
    Modes:
      • SAS mode: pass `sas_url` (or rely on module-level `sas_url`). We list blobs via
        `get_file_list(sas_url=...)`, filter by extension, download each, then upload.


    """
    
    # Default to the module-level `sas_url` if caller doesn’t pass one
    
    uploaded = []

    # ---------- SAS mode ----------
    
    post_log({"message": f"[artifacts] (SAS) Listing artifacts from container...", "status": "In Progress"})
    try:
        files = get_file_list(sas_url=sas_url) or []
    except ApiException as e:
        uploaded.append({"error": f"List failure {getattr(e,'status','')}: {getattr(e,'body','')}"})
        post_log({"message": f"[artifacts] (SAS) Failed to list files: {uploaded[-1]['error']}", "status": "Failed"})
        return uploaded

    ok = 0
    for f in files:
        try:
            resp = post_report_artifact(f.name)
            payload = resp.to_dict() if hasattr(resp, "to_dict") else (
                resp.model_dump(by_alias=True) if hasattr(resp, "model_dump") else {"repr": repr(resp)}
             )
            uploaded.append({"file": f.name, "response": payload})
            ok += 1
        except ApiException as e:
            uploaded.append({"file": f.name, "error": f"{getattr(e,'status','')} {getattr(e,'body','')}"})
        except Exception as e:
            uploaded.append({"file": f.name, "error": str(e)})

    post_log({"message": f"[artifacts] (SAS) Uploaded {ok}/{len(files)} files from container", "status": "In Progress"})
    return uploaded
   
 
# -----------------------------
# Main
# -----------------------------

def main():
        
    post_files_as_artifacts(sas_url=sas_url)
            
if __name__ == "__main__":
    post_log({"message": "Starting the Artifact Upload", "status": "In Progress"})
    main()
