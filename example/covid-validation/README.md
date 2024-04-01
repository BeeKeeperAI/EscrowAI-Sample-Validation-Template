# An Example of COVID Inference in EscrowAI

In this example, you will be able to play with a simple use case of BeeKeeperAI's EscrowAI platform. Going through this example, you will be able to see how a container can be created, how a python script can be executed, and how an example with encrypted contents can be delivered to an enclave.

## What prerequisites do I need to be successful?

### Docker Knowledge

This template assumes an understanding of the Docker container build system. If you're new to Docker or need a refresher, the Docker documentation is quite strong and the first half of the [getting-started tutorial](https://docs.docker.com/get-started/) on Docker.com can be very helpful.

## What is this example?

This example is meant to be a container that downloads chest x-ray images inside a Trusted Execution Environment and tests a deep learning diagnosis model of Covid-19. In this repository, you will find the following files which you can adapt to your application:

1. An example [Dockerfile](Dockerfile) (this is how your container is built and specifies the environment your code will use in an enclave)
2. An example [app.py](app.py) (tihs code uses the EnclaveSDK to access secrets in an enclave, processes example chest x-rays, and creates a report for EscrowAI with the results of this covid model validation run)
3. An example secret ([multi-class-pg.pkl](models/multi-class-pg.pkl)) model
4. An example of a container entrypoint [run.sh](run.sh) which is pointed to by the Dockerfile and which starts your code in a Trusted Execution Environment
5. An example of a set of python requirements [requirements.txt](requirements.txt) which defines the python packages needed to run your app.py
6. An example of a validation criteria file [schema.json](schema.json) which enforces strict output requirements for a final report

## What do I do with tihs code?

You will simply zip this set of code up and upload it to the EscrowAI platform and you should be ready to run this example!
