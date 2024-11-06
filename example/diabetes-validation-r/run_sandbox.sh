#!/bin/sh

# Set your SAS URL and Enclave URL
PLAINTEXT_SAS_URL="<<YOUR DATA SAS URL HERE>>"
ENCLAVE_URL="https://enclaveapi.stg.escrow.beekeeperai.com"

SAS_URL_ENCODED=$(echo -n $PLAINTEXT_SAS_URL | base64)

SAS_URL=$SAS_URL_ENCODED ENCLAVE_URL=$ENCLAVE_URL Rscript app.R
