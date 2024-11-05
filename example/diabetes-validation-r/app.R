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
enclave_url <- Sys.getenv("ENCLAVE_URL", unset = "https://localhost:5000")

# Get list of files from the Blob container
get_file_list <- function() {
    response <- GET(paste0(enclave_url, "/api/v1/data/files"))
    content <- fromJSON(rawToChar(response$content))
    return(content$files)
}

# Download and decrypt a file
download_file <- function(file_name) {
    body <- list(filepath = file_name)
    response <- POST(
        paste0(enclave_url, "/api/v1/data/file"),
        body = body,
        encode = "json"
    )
    return(response$content)
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

main <- function() {
    files <- get_file_list()
    file_content <- NULL

    # Find and download the diabetes file
    target_file <- files[files$name == "diabetes.csv.bkenc", ]
    if (nrow(target_file) > 0) {
        file_content <- download_file(target_file$name)
    }

    if (!is.null(file_content)) {
        # Read CSV data
        text_data <- rawToChar(file_content)
        df <- read.csv(text = text_data)
        
        correlation <- corrFunction(df)
        result <- toJSON(correlation)

        # Create and post report
        escrow_report <- list(report = result)
        final_report <- list(
            json_data = escrow_report,
            name = "Diabetes (R) Correlation Report",
            status = "Completed"
        )

        print(final_report)

        post_report(final_report)
    }
}

# Run the main function
main()
