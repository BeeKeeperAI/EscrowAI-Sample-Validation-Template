# An Example of Diabetes Analysis in EscrowAI

In this example, you will learn how to analyze diabetes data using BeeKeeperAI's EscrowAI platform. This demo shows how to perform correlation analysis on diabetes datasets within a secure enclave environment.

## What prerequisites do I need to be successful?

### Docker Knowledge

This template assumes an understanding of the Docker container build system. If you're new to Docker or need a refresher, the Docker documentation is quite strong and the first half of the [getting-started tutorial](https://docs.docker.com/get-started/) on Docker.com can be very helpful.

### Technical Prerequisites

You will need the following items installed on your development machine to execute these steps:

- R
- Docker Version 20+
- Bash

## What is this example?

This example demonstrates how to use BeeKeeperAI's EnclaveAPI to securely analyze diabetes data. The application performs correlation analysis on the dataset within an enclave environment. In this repository, you will find:

1. An example [Dockerfile](Dockerfile) 
2. An example [app.R](app.R) (this performs the main correlation analysis)
3. An example [corr.R](corr.R) (this contains the correlation function implementation)
4. An example of a validation criteria file [schema.json](schema.json) which enforces strict output requirements for a final report

## How do I run this sample?

The application can be run in three ways: without a container, inside a local Docker container, and within an EscrowAI enclave. For testing, you can use the public diabetes dataset available here: https://www.kaggle.com/datasets/saurabh00007/diabetescsv

## Running locally without a container

Before working with the encrypted version, you can test the R application locally. To do so, you will need to edit the `run_sandbox.sh` script to include your SAS URL. Then, you can run the script:

```bash
bash run.sh
```

## Running in the EscrowAI Enclave

To run this example inside the EscrowAI enclave, you will need to encrypt files on interest. You should take note not to encrypt the following files:

- Dockerfile
- run.sh

After encrypting the files, you will need to zip the files up and upload them to the EscrowAI platform. Then, you will be ready to run this example inside the enclave.