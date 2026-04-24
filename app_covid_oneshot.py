import io
import os
import json
import base64
from typing import List, Dict
from io import BytesIO
from PIL import Image
import EnclaveSDK
from EnclaveSDK import File, LogData

# Add Report import
from EnclaveSDK import Report

# Configuration
configuration = EnclaveSDK.Configuration(os.getenv("ENCLAVE_URL", "https://enclaveapi.escrow.beekeeperai.com/"))
sas_url = os.getenv("SAS_URL", None) 
if sas_url:
    sas_url = base64.b64encode(sas_url.encode()).decode()

# Writeback URL configuration
WRITEBACK_URL_RAW = os.getenv("WRITEBACK_URL", None)
WRITEBACK_URL_B64 = None
if WRITEBACK_URL_RAW:
    WRITEBACK_URL_RAW = WRITEBACK_URL_RAW.strip().strip('"')
    WRITEBACK_URL_B64 = base64.b64encode(WRITEBACK_URL_RAW.encode()).decode()

api_client = EnclaveSDK.ApiClient(configuration)
writeback_api = EnclaveSDK.WritebackApi(api_client)

# Standard image size for all images
STANDARD_WIDTH = 256
STANDARD_HEIGHT = 256

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

def _guess_content_type(filename: str) -> str:
    fn = filename.lower()
    if fn.endswith(".png"):
        return "image/png"
    if fn.endswith(".jpg") or fn.endswith(".jpeg"):
        return "image/jpeg"
    if fn.endswith(".bmp"):
        return "image/bmp"
    if fn.endswith(".gif"):
        return "image/gif"
    if fn.endswith(".tiff") or fn.endswith(".tif"):
        return "image/tiff"
    return "application/octet-stream"

def writeback_upload_bytes(filename: str, content_bytes: bytes, metadata: Dict = None, folder: str = None) -> None:
    if metadata is None:
        metadata = {}

    # Construct filepath with folder if provided
    if folder:
        folder = folder.strip('/\\')
        filepath = f"{folder}/{filename}"
    else:
        filepath = filename

    size = len(content_bytes)
    post_log({"message": f"[writeback] Upload starting: {filepath} (bytes={size})", "status": "In Progress"})

    content_type = _guess_content_type(filename)
    post_log({"message": f"[writeback] Content-Type for {filename}: {content_type}", "status": "In Progress"})

    try:
        text = content_bytes.decode("utf-8")
        post_log({"message": f"[writeback] Sending {filepath} as UTF-8 text", "status": "In Progress"})
        write_req = EnclaveSDK.WriteFileRequest(
            content=text,
            contentType=content_type,
            overwrite=True,
            metadata=metadata,
        )
    except UnicodeDecodeError:
        post_log({"message": f"[writeback] Sending {filepath} as base64-encoded binary", "status": "In Progress"})
        b64 = base64.b64encode(content_bytes).decode("ascii")
        write_req = EnclaveSDK.WriteFileRequest(
            content=b64,
            contentType=content_type,
            contentEncoding="base64",
            overwrite=True,
            metadata=metadata,
        )

    try:
        writeback_api.api_v1_writeback_file_post(
            write_file_request=write_req,
            filepath=filepath,
            sas_url=WRITEBACK_URL_B64,
        )
        post_log({"message": f"[writeback] Uploaded: {filepath}", "status": "In Progress"})
    except Exception as e:
        post_log({"message": f"[writeback] ERROR uploading {filepath}: {e}", "status": "Failed"})
        raise

def standardize_image(image_bytes: bytes, original_format: str = None) -> tuple[bytes, str]:
    """
    Standardize image to 256x256 pixels.
    Converts RGBA to RGB if needed.
    Preserves original format when possible.
    Returns tuple of (image_bytes, format).
    """
    try:
        # Load image from bytes
        img = Image.open(BytesIO(image_bytes))
        
        # Determine output format (preserve original if possible)
        if original_format:
            output_format = original_format.upper()
        else:
            output_format = img.format if img.format else 'PNG'
        
        # Handle transparency for formats that don't support it
        if output_format in ['JPEG', 'JPG'] and img.mode in ['RGBA', 'LA', 'P']:
            # Create white background for JPEG
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ['RGBA', 'LA'] else None)
            img = background
        elif img.mode == 'RGBA' and output_format not in ['PNG', 'TIFF', 'GIF']:
            img = img.convert('RGB')
        elif img.mode not in ['RGB', 'L', 'RGBA']:
            img = img.convert('RGB')
        
        # Resize to standard size
        img_resized = img.resize((STANDARD_WIDTH, STANDARD_HEIGHT), Image.Resampling.LANCZOS)
        
        # Save to bytes with appropriate settings
        output = BytesIO()
        save_params = {}
        
        if output_format in ['JPEG', 'JPG']:
            save_params['quality'] = 95
            save_params['optimize'] = True
            output_format = 'JPEG'
        elif output_format == 'PNG':
            save_params['optimize'] = True
        
        img_resized.save(output, format=output_format, **save_params)
        return output.getvalue(), output_format.lower()
    
    except Exception as e:
        post_log({"message": f"Error standardizing image: {str(e)}", "status": "Failed"})
        raise

def is_image_file(filename: str) -> bool:
    """Check if file is an image based on extension (including .bkenc encrypted files)"""
    # Remove .bkenc extension if present
    if filename.lower().endswith('.bkenc'):
        filename = filename[:-6]  # Remove '.bkenc'
    
    image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.tif']
    return any(filename.lower().endswith(ext) for ext in image_extensions)

def get_original_filename(encrypted_filename: str) -> str:
    """Extract original filename from encrypted filename (remove .bkenc)"""
    if encrypted_filename.lower().endswith('.bkenc'):
        return encrypted_filename[:-6]
    return encrypted_filename

def post_report(finalReport: Dict) -> Dict:
    """Post a report using the Report API"""
    api_instance = EnclaveSDK.ReportApi(api_client)
    
    # Check if schema.json is available and read it into json_schema
    if os.path.exists("schema.json"):
        with open("schema.json", "r") as schema:
            finalReport['json_schema'] = EnclaveSDK.ReportJsonSchema.from_dict(json.load(schema))
    
    report = Report.from_dict(finalReport)
    api_response = api_instance.api_v1_report_post(report)
    return api_response

def main():
    post_log({"message": "Starting image standardization process", "status": "In Progress"})
    
    # Get list of files from blob storage
    files = get_file_list(sas_url=sas_url)
    
    if not files:
        post_log({"message": "No files found in blob storage", "status": "Failed"})
        return
    
    post_log({"message": f"Found {len(files)} files in blob storage", "status": "In Progress"})
    
    processed_count = 0
    skipped_count = 0
    error_count = 0
    
    for file in files:
        # Check if the underlying file (without .bkenc) is an image
        if not is_image_file(file.name):
            post_log({"message": f"Skipping non-image file: {file.name}", "status": "In Progress"})
            skipped_count += 1
            continue
        
        try:
            post_log({"message": f"Processing image: {file.name}", "status": "In Progress"})
            
            # Download file (SDK will automatically decrypt .bkenc files)
            file_content = download_file(file.name, sas_url=sas_url)
            
            if not file_content:
                post_log({"message": f"Failed to download file: {file.name}", "status": "In Progress"})
                error_count += 1
                continue
            
            # Get original filename (without .bkenc extension)
            original_name = get_original_filename(file.name)
            
            # Get original format from extension
            original_ext = os.path.splitext(original_name)[1].lower()
            format_map = {'.jpg': 'jpeg', '.jpeg': 'jpeg', '.png': 'png', '.bmp': 'bmp', 
                         '.gif': 'gif', '.tiff': 'tiff', '.tif': 'tiff'}
            original_format = format_map.get(original_ext, 'png')
            
            # Standardize the image (preserving format)
            standardized_bytes, output_format = standardize_image(file_content, original_format)
            
            # Preserve folder structure from original path
            # Get directory path (e.g., 'covid/', 'pneumonia/', 'nofinding/')
            original_dir = os.path.dirname(original_name)
            
            # Extract filename from path (preserve extension based on format)
            original_filename = os.path.basename(original_name)
            base_name = os.path.splitext(original_filename)[0]
            
            # Use appropriate extension for output format
            ext_map = {'jpeg': '.jpg', 'png': '.png', 'bmp': '.bmp', 'gif': '.gif', 'tiff': '.tiff'}
            new_extension = ext_map.get(output_format, '.png')
            new_filename = f"{base_name}{new_extension}"
            
            # Combine V1 folder with original directory structure
            if original_dir:
                writeback_folder = f"V1/{original_dir}"
            else:
                writeback_folder = "V1"
            
            # Upload to V1 folder maintaining original directory structure
            writeback_upload_bytes(
                new_filename,
                standardized_bytes,
                metadata={
                    "original_file": file.name,
                    "decrypted_file": original_name,
                    "original_format": original_format,
                    "output_format": output_format,
                    "original_size": str(len(file_content)),
                    "standardized_size": str(len(standardized_bytes)),
                    "width": str(STANDARD_WIDTH),
                    "height": str(STANDARD_HEIGHT)
                },
                folder=writeback_folder
            )
            
            processed_count += 1
            post_log({"message": f"Successfully processed: {file.name} -> {writeback_folder}/{new_filename}", "status": "In Progress"})
        
        except Exception as e:
            post_log({"message": f"Error processing {file.name}: {str(e)}", "status": "In Progress"})
            error_count += 1
    
    # Log final summary
    post_log({
        "message": f"Image standardization complete - Processed: {processed_count}, Skipped: {skipped_count}, Errors: {error_count}",
        "status": "In Progress"
    })
    
    # Generate and post report
    report_data = {
        "total_files_read": len(files),
        "total_files_processed": processed_count,
        "files_skipped": skipped_count,
        "files_errored": error_count,
        "standard_dimensions": f"{STANDARD_WIDTH}x{STANDARD_HEIGHT}",
        "processing_summary": {
            "success_rate": round((processed_count / len(files) * 100), 2) if len(files) > 0 else 0,
            "total_files": len(files),
            "successful": processed_count,
            "skipped": skipped_count,
            "errors": error_count
        }
    }
    
    # Wrap in "report" key to match validation schema
    finalReport = {
        "json_data": {
            "report": report_data
        },
        "name": "Image Standardization Report",
        "status": "Completed"
    }
    
    post_log({"message": f"Final report: {json.dumps(finalReport, indent=2, default=str)}", "status": "In Progress"})

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        post_log({"message": f"Fatal error: {str(e)}", "status": "Failed"})
        raise