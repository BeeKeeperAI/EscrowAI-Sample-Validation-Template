# Define a base image you want to build FROM
FROM python:3.9.16-slim

# Set the working directory
WORKDIR /app

# Use COPY to keep your local folder and file structure
COPY . .

# Write requirements.txt 
RUN pip install -r requirements.txt
RUN pip install EnclaveSDK

# Make the run.sh script executable
RUN chmod +x run.sh

# Execute the template script inside a convenient wrapper
ENTRYPOINT ["/bin/sh", "run.sh"]