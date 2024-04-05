# Sample Validation Template

In EscrowAI, an algorithm is your program (such as data query, inference, or model training) that processes data in an EscrowAI-managed TEE running in the Data Steward’s environment. For proper execution, your algorithm code must be packaged according to the guidelines detailed here. The algorithm package is converted to a docker container by EscrowAI.

## Contents of the algorithm package

A container is a standard unit of software that packages up code and all its dependencies so the application runs quickly and reliably from one computing environment to another. A Docker container image is a lightweight, standalone, executable package of software that includes everything needed to run an application: code, runtime, system tools, system libraries and settings.

These details include sample code you can use as a template for your algorithm package, an [example validation criteria file](schema.json) for use in EscrowAI, and how to create the algorithm package. After you create your algorithm package, you will encrypt and upload it to EscrowAI.

NOTE: even if you are unfamiliar with creating a docker container, the below steps will assist you in preparing your code to be packaged into an EscrowAI-compatible container.

The package has the following components:

* Dockerfile - A set of instructions to define your algorithm's container environment as seen in [Dockerfile](Dockerfile).
* Entry point -  A file that defines the starting point of your code as seen in [run.sh](run.sh).
* Algorithm code - Your code as seen in [algo-template.py](algo-template.py).
* Python requirements - The set of required python libraries to run your code as seen in [requirements.txt](requirements.txt).

### Dockerfile

The Dockerfile is a set of instructions to define your algorithm's container environment.

### Entry point

When your container starts, it executes an entry point script that actually starts your algorithm program. The example entry point here is called `run.sh`.  

The script name `run.sh` is only an example. You can name your entry point script whatever you like, as long as that same script name is specified for the value of the ENTRYPOINT variable in your Dockerfile.

### Your algorithm code

NOTE: if you are used to analyzing data in an Integrated Development Environment like a Jupyter Notebook, Visual Studio Code, Spider, or PyCharm (all commonly found in Anaconda), you will need to convert your code into production code and add in the EscrowAI SDK as demonstrated in this repository. If this is at all confusing, please reach out to your engineering contact and they will happily assist you with preparing your code to be added to an EscrowAI container.

The example `algo-template.py` calls the EscrowAI Enclave API to:

1. List available data files,
2. Fetch data files,
3. Post a log message,
4. Validate a report with in-line schema,
5. and Post a final report.

### Requirements.txt

The example `requirements.txt` is used to install the required python packages needed by your algorithm. This code is designed to use the latest version of the EnclaveSDK and you should add any additional packages you need for your code.

## Folder structure for algorithm package

Put your files at the top level of a folder like

```bash
sample-validation-template/
├── Dockerfile
├── run.sh
├── algo-template.py
└── requirements.txt
```

## Early Access: Using the EnclaveAPI Sandbox

When pointing the EnclaveSDK to the Enclave Sandbox (sandbox.dev.escrow.beekeeperai.com), you can perform the set of example API calls provided in this repository locally before deploying in EscrowAI. The code has the configuration required to point at the Enclave Sandbox and you need to uncomment those configurations to point at the sandbox. This system is under active development and is presented as-is.

## Preparing to Encrypt Your Secrets

When you are preparing to upload your code to EscrowAI, you will use EscrowAI's encryption utility and provide a Content Encryption Key (CEK) and select the files in your algorithm package you deem secret. It is critical to remember that the system that builds your algorithm package relies on an unencrypted Dockerfile and requires any referenced file in your Dockerfile to be unencrypted as well. For example, a reference to a secret file as an entrypoint for your algorithm should be wrapped with a script like [run.sh](run.sh). References to files that need to be placed into your container using something like `COPY` should not be referenced directly, but instead should be referenced by the folder they are inside and are destined for (e.g., `COPY mysecretfolder /app/mysecretfolder`).

SGX NOTE: When you are using Intel's SGX environments, you derive additional file-system encryption by targeting your secrets at the `/app` folder. You can achieve this by, for example, using `COPY` to keep files in `/app` and changing your `WORKDIR` early in your Dockerfile to `/app`.
