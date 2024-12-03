# Set CRAN mirror before installing packages
options(repos = c(CRAN = "https://cloud.r-project.org"))

# Install required packages if not already installed
required_packages <- c("httr", "jsonlite", "dplyr", "openssl")
new_packages <- required_packages[!(required_packages %in% installed.packages()[, "Package"])]
if (length(new_packages)) install.packages(new_packages)

library(httr)
library(jsonlite)
library(dplyr)
library(openssl)

# Disable ssl certificate verification and hostname verification globally
httr::set_config(httr::config(ssl_verifypeer = FALSE, ssl_verifyhost = FALSE))

# Create the SDK configuration
enclave_url <- Sys.getenv("ENCLAVE_URL", unset = "https://enclaveapi.escrow.beekeeperai.com")

# When testing in sandbox, add a SAS URL with at minimum read and list permissions
SAS_URL <- base64_encode(Sys.getenv("SAS_URL"))

# Use the Data API class to get a list of files in the Blob container
get_file_list <- function(sas_url = SAS_URL) {
    # Initialize the query parameter with SAS URL if provided
    query <- if (!is.null(sas_url)) list(SASUrl = sas_url) else NULL
    
    # Send a GET request to the endpoint to fetch file data
    response <- GET(paste0(enclave_url, "/api/v1/data/files"), query = query)
    
    # Convert the raw response content to JSON format
    content <- fromJSON(rawToChar(response$content))

    # Return the list of files from the response
    return(content$files)
}

# Use the Data API class to securely decrypt and download a file
download_file <- function(file_name, sas_url = SAS_URL) {
    # Set up query parameters with the file name and SAS URL
    query <- list(filepath = file_name, SASUrl = sas_url)
    
    # Send a GET request to download the file
    response <- httr::GET(
        paste0(enclave_url, "/api/v1/data/file"),
        query = query,
        encode = "json"
    )
    
    # Return the content of the response, which is the downloaded file
    return(response$content)
}

# Post report to the Enclave. If schema.json exists, it will be used to validate the report.
post_report <- function(final_report) {
    # Check if schema.json exists and load it
    schema_file <- "schema.json"
    if (file.exists(schema_file)) {
        # Read and parse the schema file
        schema_content <- readLines(schema_file, warn = FALSE)
        schema <- fromJSON(paste(schema_content, collapse = ""))

        # Update final_report with schema in the correct structure
        final_report$json_schema <- schema # Remove the nested 'report' level
    }

    # Send POST request with the report
    response <- POST(
        paste0(enclave_url, "/api/v1/report"),
        body = final_report,
        encode = "json"
    )

    # Parse and return the response content
    return(fromJSON(rawToChar(response$content)))
}

# Use the Log API class to post a log message
post_log <- function(message, status = "In Progress") {
    # Prepare the log data with the message and status
    log <- list(message = message, status = status)

    # Send a POST request to log the message and status
    response <- POST(
        paste0(enclave_url, "/api/v1/log"),
        body = log,
        encode = "json"
    )

    # Optional: Return the response if needed, otherwise function is complete
    return(response)
}


# calculate Pearson's correlation
corrFunction <- function(df) {
    # Select all columns except 'Outcome'
    x <- df[, !names(df) %in% c("Outcome")]

    # Calculate correlation matrix
    corr <- cor(x, method = "pearson")

    return(corr)
}


main <- function() {
    post_log("Listing files in Blob container")
    files <- get_file_list()
    print(paste("files:", files))
    file_content <- NULL

    post_log("Finding and downloading the diabetes file")
    # Find and download the diabetes file
    target_file <- files[grepl("^diabetes.csv", files$name), ]
    print(paste("target_file:", target_file))

    if (nrow(target_file) > 0) {
        file_content <- download_file(target_file$name)
    }

    post_log("Reading and processing the diabetes file")
    if (!is.null(file_content)) {
        # Read CSV data
        text_data <- rawToChar(file_content)
        df <- read.csv(text = text_data)
        correlation <- corrFunction(df)

        # Convert correlation matrix to nested dictionary
        corr_dict <- list()
        col_names <- colnames(correlation)
        for (i in 1:nrow(correlation)) {
            row_dict <- list()
            for (j in 1:ncol(correlation)) {
                row_dict[[col_names[j]]] <- correlation[i, j]
            }
            corr_dict[[col_names[i]]] <- row_dict
        }

        result <- toJSON(corr_dict, auto_unbox = TRUE)

        # Create and post report
        escrow_report <- list(report = result)
        final_report <- list(
            json_data = escrow_report,
            name = "Diabetes (R) Correlation Report",
            status = "Completed"
        )

        # Print the final report structure before sending it
        # This helps with debugging and verification of the report format
        print(final_report)

        # Submit the report to the Enclave API and store the response
        # If schema.json exists, it will be used to validate the report.
        # The response will contain confirmation of successful submission
        response_content <- post_report(final_report)
        
        # Print the API response for verification
        # This typically includes a success message or any error details
        print(response_content)
    } else {
        post_log("Failed to download file", "Failed")
    }
}

# Run the main function
tryCatch(
    {
        main()
    },
    error = function(e) {
        print(paste("Error:", e$message))
        post_log(paste("Error:", e$message), "Failed")
    }
)
