# Set CRAN mirror before installing packages
options(repos = c(CRAN = "https://cloud.r-project.org"))

# Install required packages if not already installed
required_packages <- c("httr", "jsonlite", "dplyr")
new_packages <- required_packages[!(required_packages %in% installed.packages()[,"Package"])]
if(length(new_packages)) install.packages(new_packages)

library(httr)
library(jsonlite)
library(dplyr)
source("corr.R")

httr::set_config(config(ssl_verifypeer = FALSE, ssl_verifyhost = FALSE))


# Create the SDK configuration
enclave_url <- Sys.getenv("ENCLAVE_URL", unset = "https://enclaveapi.stg.escrow.beekeeperai.com")
SAS_URL <- Sys.getenv("SAS_URL")
print(paste("SAS_URL:", SAS_URL))

# Get list of files from the Blob container
get_file_list <- function(sas_url=SAS_URL) {
    query <- NULL
    if (!is.null(sas_url)){
        query = list(SASUrl=sas_url)
    }
    response <- GET(paste0(enclave_url, "/api/v1/data/files"), query = query)
    content <- fromJSON(rawToChar(response$content))
    return(content$files)
}

# Download (and decrypt a file if in EscrowAI environment)
download_file_enclave <- function(file_name) {
    body <- list(filepath = file_name)
    response <- POST(
        paste0(enclave_url, "/api/v1/data/file"),
        body = body,
        encode = "json"
    )
    return(response$content)
}

download_file_sandbox <- function(file_name, sas_url) {   
    query <- list(filepath = file_name, SASUrl = sas_url)
    response <- httr::GET(
        paste0(enclave_url, "/api/v1/data/file"),
        query = query,
        encode = "json"
    )
    return(response$content)
}

download_file <- function(file_name) {
    if (SAS_URL!="") {
        return(download_file_sandbox(file_name, SAS_URL))
    } else {
        return(download_file_enclave(file_name))
    }
}
# Post report to the Enclave
post_report <- function(final_report) {
    response <- POST(
        paste0(enclave_url, "/api/v1/report"),
        body = final_report,
        encode = "json"
    )
    return(fromJSON(rawToChar(response$content)))
}

post_log <- function(message, status) {
    log <- list(message = message, status = status)
    response <- POST(
        paste0(enclave_url, "/api/v1/log"),
        body = log,
        encode = "json"
    )
}

main <- function() {
    
    files <- get_file_list()
    print(paste("files:", files))
    file_content <- NULL

    # Find and download the diabetes file
    target_file <- files[grepl("^diabetes.csv", files$name), ]

    if (nrow(target_file) > 0) {
        file_content <- download_file(target_file$name)
    }

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
                row_dict[[col_names[j]]] <- correlation[i,j]
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

        print(final_report)

        post_report(final_report)
    }else{
        post_log("Failed to download file", "Failed")
    }
}

# Run the main function
tryCatch({
    main()
}, error = function(e) {
    post_log(paste("Error:", e$message), "Failed")
})
