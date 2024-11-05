# Build stage
FROM r-base:latest AS builder

# Install system dependencies for building packages
RUN apt-get update -y && \
    apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev

# Create directory for installed R packages
RUN mkdir -p /r-packages
ENV R_LIBS_USER=/r-packages

# Install R packages
RUN Rscript -e 'install.packages(c("httr", "jsonlite", "dplyr"), repos="https://cloud.r-project.org", lib="/r-packages")'

# Runtime stage
FROM r-base:latest

# Install only runtime system dependencies
RUN apt-get update -y && \
    apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Create directory and copy installed packages
RUN mkdir -p /r-packages
COPY --from=builder /r-packages /r-packages
ENV R_LIBS_USER=/r-packages

WORKDIR /app

COPY . .

# Make the run.sh script executable
RUN chmod +x run.sh

# set the start command
ENTRYPOINT [ "./run.sh" ]