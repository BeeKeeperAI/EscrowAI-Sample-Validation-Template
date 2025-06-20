FROM r-base:4.3.2

# Install system dependencies and R packages in a single layer
RUN apt-get update -y && \
    apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    build-essential \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /r-packages && \
    Rscript -e 'install.packages(c("httr", "jsonlite", "dplyr"), repos="https://cloud.r-project.org", lib="/r-packages")'

# Set R library path
ENV R_LIBS_USER=/r-packages

# Set up application
WORKDIR /app
COPY *.R .
COPY run.sh .
COPY *.bkenc .

# Ensure the secrets.yaml file is copied to the container when encrypting
COPY *.yaml . 

# Make the run script executable
RUN chmod +x run.sh

# Set the start command
ENTRYPOINT [ "./run.sh" ]
