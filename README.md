# Aries ACA-Py Jupyter Playground - Scottish Healthcare Identification Ecosystem

## A Jupyter Notebook Based Playground for Education and Experimentation with Hyperledger Aries

## Requirements

This project is written in Python and is displayed in jupyter notebooks.

You need to install:
1. [Docker](https://docs.docker.com/get-docker/)
2. [docker-compose](https://docs.docker.com/compose/install/)
3. The **source-to-image** (s2i) tool is also required to build the docker images used in the demo. S2I can be downloaded [here](https://github.com/openshift/source-to-image). The website gives instructions for installing on other platforms like MACOS, Linux, Windows.
Verify that **s2i** is in your PATH.  If not, then edit your PATH and add the directory where **s2i** is installed.  The **manage** script will look for the **s2i** executable on your PATH.  If it is not found you will get a message asking you to download and set it on your PATH.
    - If you are using a Mac and have Homebrew installed, the following command will install s2i: `brew install source-to-image`
    - If you are using Linux, go to the [releases](https://github.com/openshift/source-to-image/releases/latest) page and download the correct distribution for your machine. Choose either the linux-386 or the linux-amd64 links for 32 and 64-bit, respectively. Unpack the downloaded tar with `tar -xvf "Release.tar.gz"`
    - If you are not sure about your Operating System you can visit [this](https://whatsmyos.com/) and/or follow the instructions.
    - You should now see an executable called s2i. Either add the location of s2i to your PATH environment variable, or move it to a pre-existing directory in your PATH. For example, `sudo cp /path/to/s2i /usr/local/bin` will work with most setups. You can test it using `s2i version`.

Ensure that Docker is running. If it is not try `sudo dockerd` in another terminal.

## Starting the Scottish Healthcare Identification Ecosystem 

This proof of concept simulates the identification processes that a healthcare professional goes through as they graduate from medical school, become a licenced professional and onboard at a new hospital.

This figure shows the actors, credentials and interactions modelled in this playground

![Scottish Healthcare Identification Ecosystem](./shs-cred-deps.png)

There are 5 actors (see the playground folder). Also feel free to add more by copying and editing the actor template.

Before you can launch the playground you must set the .env file for each of actor. The file should be under `playground/<agent_name>/.env`. 

For quick start just copy the example env files provided under each actor in the playground (example.env) and rename them to .env.

### Start a local von-network

**This POC uses a local von-network. You must start this separately from this playground. (or alternatively edit the .env files to point at a different ledger)**

Clone and run the von network following instructions in the repo - https://github.com/bcgov/von-network

### Register Public DIDs

You will need to manually register the public DIDs for the respective agents on the local von network which should be running at http://localhost:9000.

Use the form on the web interface to register the ACAPY_WALLET_SEED defined in each of the actors .env file.

Note: healthcare-professional does not have one defined as they will not be issuing any credentials.

### Launch the playground

Run:

`./manage.sh production`

This spins up all docker containers defined in the `docker-compose.yml` file and named in the DEFAULT_CONTAINERS variable defined in the `manage.sh` shell script.

To stop the playground either:

`./manage.sh stop` - this terminates the containers but persists the volumes in the postgres-db

`./manage.sh down` - terminate containers and delete all volumes


## Configuring the Playground

The playground is designed to make it easy for you to add new actors and start writing SSI ecosystem flows. 

To add an actor you need to make three changes:

* Create a folder under `playground` for that actor and make sure it has a .env file under that folder. You can copy the template `actor` folder and use the `dummy.env` file to get started but will need to edit the file.
* Define the actor services in the `docker-compose.yml`. More detailed instructions included in the comments on that file including commented out set of services for the actor `actor` that you can change.
* Add the new services to the DEFAULT_CONTAINERS variable in the `manage.sh` script

Feel free to customise Alice and Bob aswell. It makes sense to name your actors something meaningful to the usecase you are trying to model.


## Using Different Indy Networks

An aries agent points to the indy network it wishes to use to write and resolve cryptographic objects to and from. All actors in the flow should use the same network - See the ACA_PY_GENESIS_URL argument in .env files.

The master branch currently is set to use the Sovrin StagingNet.

It is also possible to use the BC Gov's Test Network VON - http://greenlight.bcovrin.vonx.io/genesis

Or a local ledger can be spun up either within the docker-compose.yml or separately by cloning the [VON codebase](https://github.com/bcgov/von-network)