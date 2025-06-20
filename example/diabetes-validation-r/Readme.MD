# Diabetes Analysis in R - EscrowAI Example

This example demonstrates how to perform correlation analysis on diabetes datasets within EscrowAI's secure enclave environment using R. The application analyzes diabetes data and generates correlation reports while maintaining data privacy and security.

## Prerequisites

### Technical Requirements
- **R 3.6+** (for local development)
- **Docker 20+** (for containerized testing)
- **Bash shell** (for running scripts)
- **Internet connection** (for downloading dependencies)

### Knowledge Requirements
- Understanding of Docker container build system ([Docker getting-started tutorial](https://docs.docker.com/get-started/) recommended)
- Basic R programming knowledge
- Familiarity with statistical correlation analysis

### Data Requirements
- Diabetes dataset (example available at: https://www.kaggle.com/datasets/saurabh00007/diabetescsv)
- Dataset should be accessible via SAS URL for enclave execution
- **SAS URL** for accessing blob storage containing the diabetes dataset

### Environment Variables
The application requires the following environment variables:

- **`SAS_URL`** (Required): Shared Access Signature URL for accessing your blob storage containing the diabetes dataset
- **`ENCLAVE_URL`** (Optional): EscrowAI enclave API endpoint. Defaults to `https://enclaveapi.escrow.beekeeperai.com/`

## What This Example Does

This example uses BeeKeeperAI's EnclaveAPI to securely analyze diabetes data within a trusted execution environment. The application:

1. **Fetches diabetes dataset** from secure storage using EnclaveSDK
2. **Performs correlation analysis** using R statistical functions
3. **Generates comprehensive correlation reports** with statistical insights
4. **Validates output** against predefined schema requirements
5. **Posts results securely** through the EnclaveAPI

## Files in This Example

1. **`Dockerfile`** - Container environment configuration for R and dependencies
2. **`run.sh`** - Entry point script that launches the R application
3. **`app.R`** - Main R script that performs correlation analysis using EnclaveAPI
4. **`requirements.txt`** - R package dependencies (if applicable)
5. **`schema.json`** - Validation criteria for output reports ensuring data quality. In sandbox testing, this is passed as a value to validate reports. In EscrowAI production, this is loaded as validation criteria for the enclave.

## How to Run This Example

### Option 1: Local Development
For testing the R application locally before enclave deployment:

```bash
# Navigate to the example directory
cd example/diabetes-validation-r

# Install R dependencies (if running outside Docker)
# R packages are installed automatically by the script

# Set environment variables (replace with your actual values)
export ENCLAVE_URL="https://enclaveapi.escrow.beekeeperai.com"
export SAS_URL="your_sas_url_here"

# Run the application
bash run.sh
```

**Important**: When running locally, you must provide:
- `SAS_URL`: The Shared Access Signature URL for accessing your diabetes dataset in blob storage
- `ENCLAVE_URL`: The EscrowAI enclave API endpoint (defaults to sandbox if not provided)

**Note**: Local execution connects to the EscrowAI sandbox environment and requires a valid SAS URL for data access.

### Option 2: Docker Container
Build and run the containerized version:

```bash
# Navigate to the example directory
cd example/diabetes-validation-r

# Build the Docker image
docker build -t diabetes-analysis-r .

# Run the container with environment variables
docker run --rm \
  -e ENCLAVE_URL="https://enclaveapi.escrow.beekeeperai.com" \
  -e SAS_URL="your_sas_url_here" \
  diabetes-analysis-r
```

**Important Docker Notes:**
- Replace `your_sas_url_here` with your actual SAS URL for blob storage access
- The `ENCLAVE_URL` points to the EscrowAI API endpoint
- Use `--rm` flag to automatically clean up the container after execution

### Option 3: EscrowAI Enclave (Production)
For production deployment in the secure enclave:

1. **Prepare files for encryption**: 
   - Identify sensitive files like `app.R` and correlation analysis scripts for encryption
   - Keep `Dockerfile` and `run.sh` unencrypted (required by build system)
   - Keep `requirements.txt` unencrypted if referenced directly in Dockerfile

2. **Package the algorithm**: 
   Login to EscrowAI and use the Encryption Tool to package your entire algorithm directory and mark sensitive files for encryption. This will also transparently create your required secrets.yaml file which is a manifest of where files should be placed when they are unencrypted after loading.

3. **Upload to EscrowAI**: 
   - Use the EscrowAI platform interface to upload your encrypted package
   - Set data access permissions and SAS URL configuration

4. **Execute**: Run the analysis within the trusted execution environment with automatic data provisioning

## Expected Results

Upon successful execution, you should see:

- **Data loading confirmation**: Messages indicating successful dataset retrieval
- **Correlation analysis progress**: Indicators showing statistical computation progress
- **Statistical correlation results**: Detailed correlation matrices and coefficients
- **Schema validation success**: Confirmation that output meets requirements
- **Final report submission**: Status of report delivery to EscrowAI platform

## Troubleshooting

### Common Issues

**SAS URL Issues:**
- **Problem**: `SAS_URL` environment variable not set or invalid
- **Solution**: Ensure the `SAS_URL` environment variable is properly set and contains a valid Shared Access Signature URL
- **Verification**: Check that the SAS URL has read and list permissions for the blob storage container
- **Check expiration**: Verify that the SAS URL has not expired
- **Data verification**: Confirm the diabetes dataset is properly uploaded to the blob storage

**R Package Errors:**
- **Problem**: R packages fail to install or load
- **Solution**: Ensure all required R packages are installed and compatible with the R version
- **Check dependencies**: Verify that the R environment has access to CRAN repositories
- **Version conflicts**: Check for package version compatibility issues

**Docker Build Failures:**
- **Problem**: Docker build fails or takes too long
- **Solution**: Check that Docker daemon is running and you have sufficient permissions
- **Network**: Ensure stable internet connection for downloading R packages
- **Memory**: Verify sufficient system memory for R package compilation

**Schema Validation Errors:**
- **Problem**: Output doesn't match schema requirements
- **Solution**: Review the output format against the `schema.json` requirements
- **Data types**: Check that correlation results match expected data types
- **Structure**: Verify the report structure follows the schema specification

**Environment Variable Errors:**
- **Problem**: Required environment variables not found
- **Solution**: Ensure all required environment variables (`SAS_URL`) are set before running the application
- **Verification**: Use `env | grep -E "(ENCLAVE_URL|SAS_URL)"` to check current settings
- **Scope**: Ensure variables are exported and available to the R process

**Data Processing Issues:**
- **Problem**: Errors during correlation analysis
- **Solution**: Check that the diabetes dataset is in the expected format (CSV with proper headers)
- **Missing values**: Verify handling of missing or null values in the dataset
- **Data types**: Ensure numeric columns are properly formatted for statistical analysis

### Verification Commands

```bash
# Check environment variables
env | grep -E "(ENCLAVE_URL|SAS_URL)"

# Test Docker build
docker build -t test-diabetes-analysis .

# Verify R installation (if running locally)
R --version

# Test R package availability
R -e "library(corrplot); library(jsonlite); print('R packages loaded successfully')"

# Test SAS URL format (basic check)
echo $SAS_URL | grep -q "https://" && echo "SAS URL format looks correct" || echo "SAS URL may be malformed"

# Check required files exist
ls -la app.R run.sh schema.json
```

### Debug Mode

For additional debugging information, you can modify the R script to include more verbose output:

```bash
# Add debug environment variable
export DEBUG=true

# Run with debug output
bash run.sh
```

You can also run R interactively to debug issues:

```bash
# Start R session
R

# Load and test individual components
source("app.R")
```

## R-Specific Considerations

### Package Management
- The Docker container automatically installs required R packages
- For local development, ensure you have the necessary packages installed:
  ```r
  install.packages(c("jsonlite", "corrplot", "httr"))
  ```

### Memory Management
- R can be memory-intensive for large datasets
- Consider data sampling for very large diabetes datasets
- Monitor memory usage during correlation analysis

### Statistical Output
- Correlation matrices are generated in multiple formats
- Results include both Pearson and Spearman correlations
- P-values and confidence intervals are calculated where applicable

## Integration with Other Examples

This diabetes analysis example can be combined with other examples in this repository:

- **Use with COVID Validation**: Create comprehensive health analytics workflows
- **Combine with Breast Cancer Training**: Build multi-modal medical analysis pipelines
- **Template Integration**: Use as a reference for implementing other statistical analysis tasks in R

## Support and Resources

- **EscrowAI Documentation**: [Link to official docs]
- **Docker Getting Started**: https://docs.docker.com/get-started/
- **EnclaveSDK Reference**: [Link to SDK docs]
- **R Documentation**: https://www.r-project.org/
- **CRAN Package Repository**: https://cran.r-project.org/

For technical support, contact BeeKeeperAI.