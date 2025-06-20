# COVID-19 Chest X-Ray Analysis - EscrowAI Example

This example demonstrates how to perform COVID-19 diagnosis using deep learning models on chest X-ray images within EscrowAI's secure enclave environment. The application downloads chest X-ray images, applies a pre-trained COVID-19 detection model, and generates diagnostic reports while maintaining data privacy.

## Prerequisites

### Technical Requirements
- **Python 3.8+** (for local development)
- **Docker 20+** (for containerized testing)
- **Bash shell** (for running scripts)
- **Internet connection** (for downloading dependencies)

### Knowledge Requirements
- Understanding of Docker container build system ([Docker getting-started tutorial](https://docs.docker.com/get-started/) recommended)
- Basic Python programming knowledge
- Familiarity with machine learning and image classification concepts

### Data Requirements
- Chest X-ray images (automatically downloaded within the enclave)
- Pre-trained COVID-19 detection model (included in the package)
- **SAS URL** for accessing blob storage containing the X-ray images

### Environment Variables
The application requires the following environment variables:

- **`SAS_URL`** (Required): Shared Access Signature URL for accessing your blob storage containing chest X-ray images
- **`ENCLAVE_URL`** (Optional): EscrowAI enclave API endpoint. Defaults to `https://enclaveapi.escrow.beekeeperai.com/`

## What This Example Does

This example creates a container that operates within a Trusted Execution Environment to:

1. **Download chest X-ray images** securely using the EnclaveSDK
2. **Load a pre-trained deep learning model** for COVID-19 detection
3. **Process the X-ray images** through the diagnostic model
4. **Generate classification results** (COVID-19 positive/negative)
5. **Create a comprehensive validation report** with model performance metrics
6. **Post results securely** through the EnclaveAPI

## Files in This Example

1. **`Dockerfile`** - Container environment configuration specifying the runtime environment for the enclave
2. **`run.sh`** - Entry point script that starts the application in the Trusted Execution Environment
3. **`app.py`** - Main Python script that uses EnclaveSDK to access secrets, process X-ray images, and generate reports
4. **`models/multi-class-pg.pkl`** - Pre-trained COVID-19 detection model (encrypted secret)
5. **`requirements.txt`** - Python package dependencies needed to run the application
6. **`schema.json`** - Validation criteria file that enforces strict output requirements. In sandbox testing, this is passed as a value to validate reports. In EscrowAI production, this is loaded as validation criteria for the enclave.

## How to Run This Example

### Option 1: Local Development
For testing the application locally before enclave deployment:

```bash
# Navigate to the example directory
cd example/covid-validation

# Install dependencies
pip install -r requirements.txt

# Set environment variables (replace with your actual values)
export ENCLAVE_URL="https://enclaveapi.escrow.beekeeperai.com/"
export SAS_URL="your_sas_url_here"

# Run the Python application directly
python app.py
```

**Important**: When running locally, you must provide:
- `SAS_URL`: The Shared Access Signature URL for accessing your data in the blob storage
- `ENCLAVE_URL`: The EscrowAI enclave API endpoint (defaults to sandbox if not provided)

**Note**: Local execution will use the provided SAS URL to access real data, but may have limited functionality compared to enclave execution.

### Option 2: Docker Container
Build and test the containerized version:

```bash
# Navigate to the example directory
cd example/covid-validation

# Build the Docker image
docker build -t covid-validation .

# Run the container with environment variables
docker run --rm \
  -e ENCLAVE_URL="https://enclaveapi.escrow.beekeeperai.com/" \
  -e SAS_URL="your_sas_url_here" \
  covid-validation
```

**Important Docker Notes:**
- Replace `your_sas_url_here` with your actual SAS URL for blob storage access
- The `ENCLAVE_URL` points to the EscrowAI API endpoint
- Use `--rm` flag to automatically clean up the container after execution

### Option 3: EscrowAI Enclave (Production)
For production deployment in the secure enclave:

1. **Prepare for encryption**: 
   - Identify sensitive files like the model file (`models/multi-class-pg.pkl`) and `app.py` for encryption
   - Keep `Dockerfile` and `run.sh` unencrypted (required by build system)
   - Keep `requirements.txt` unencrypted if referenced directly in Dockerfile

2. **Package the algorithm**: 
   Login to EscrowAI and use the Encryption Tool to package your entire algorithm directory and mark sensitive files for encryption. This will also transparently create your required secrets.yaml file which is a manifest of where files should be placed when they are unencrypted after loading.

3. **Upload to EscrowAI**: 
   - Use the EscrowAI platform interface to upload your encrypted package
   - Set data access permissions and SAS URL configuration

4. **Execute**: Run the COVID-19 validation within the trusted execution environment with automatic data provisioning

## Expected Results

Upon successful execution, you should see:

- **Image download progress**: Confirmation of secure data retrieval
- **Model loading confirmation**: Successful loading of the pre-trained model
- **Classification results**: COVID-19 positive/negative predictions for each processed X-ray image
- **Performance metrics**: Accuracy, precision, recall, and F1-score statistics
- **Schema validation success**: Confirmation that output meets requirements
- **Final diagnostic report**: Submission status and report summary

## Troubleshooting

### Common Issues

**SAS URL Issues:**
- **Problem**: `SAS_URL` environment variable not set or invalid
- **Solution**: Ensure the `SAS_URL` environment variable is properly set and contains a valid Shared Access Signature URL
- **Verification**: Check that the SAS URL has read and list permissions for the blob storage container
- **Check expiration**: Verify that the SAS URL has not expired

**Model Loading Errors:**
- **Problem**: Cannot load `multi-class-pg.pkl` file
- **Solution**: Ensure the model file is properly encrypted and accessible in the `models/` directory
- **Check permissions**: Verify file permissions and encryption status

**Image Processing Failures:**
- **Problem**: Error processing X-ray images
- **Solution**: Verify that the input images are in the correct format (typically PNG or JPEG)
- **Check data**: Ensure images are accessible through the SAS URL and not corrupted

**Docker Build Issues:**
- **Problem**: Docker build fails or takes too long
- **Solution**: Check that all dependencies in `requirements.txt` are compatible
- **Network**: Ensure stable internet connection for downloading dependencies
- **Permissions**: Verify Docker daemon is running with sufficient permissions

**Schema Validation Errors:**
- **Problem**: Output doesn't match schema requirements
- **Solution**: Review the output format against the `schema.json` requirements
- **Debug**: Check the generated report structure and data types

**EnclaveSDK Connection Issues:**
- **Problem**: Cannot connect to EscrowAI API
- **Solution**: Verify that the `ENCLAVE_URL` is correct and accessible
- **Network**: Check internet connectivity and firewall settings
- **Configuration**: Ensure the enclave environment is properly configured

**Environment Variable Errors:**
- **Problem**: Required environment variables not found
- **Solution**: Ensure all required environment variables (`SAS_URL`) are set before running the application
- **Verification**: Use `env | grep -E "(ENCLAVE_URL|SAS_URL)"` to check current settings

### Verification Commands

```bash
# Check environment variables
env | grep -E "(ENCLAVE_URL|SAS_URL)"

# Test Docker build
docker build -t test-covid-validation .

# Verify Python dependencies
python -c "import pandas, numpy, sklearn; print('Dependencies imported successfully')"

# Test SAS URL format (basic check)
echo $SAS_URL | grep -q "https://" && echo "SAS URL format looks correct" || echo "SAS URL may be malformed"

# Check model file exists
ls -la models/multi-class-pg.pkl
```

### Debug Mode

For additional debugging information, you can modify the `app.py` to include more verbose logging:

```bash
# Add debug environment variable
export DEBUG=true

# Run with debug output
python app.py
```

## Integration with Other Examples

This COVID validation example can be combined with other examples in this repository:

- **Use with Breast Cancer Training**: Apply similar deep learning techniques to different medical imaging tasks
- **Combine with Diabetes Analysis**: Create comprehensive health analytics workflows
- **Template Integration**: Use as a reference for implementing other image classification tasks

## Support and Resources

- **Docker Getting Started**: https://docs.docker.com/get-started/
- **Scikit-learn Documentation**: https://scikit-learn.org/stable/

For technical support, contact BeeKeeperAI.
