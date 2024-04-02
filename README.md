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
4. and Post a final report.

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