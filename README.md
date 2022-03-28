# PaohYTRServiceDataImport

NOTE: This repository is not in use currently as it was not possible to take Kompassi-YTR to the state where it could serve its current functions and at the same time serve as the data source of Palveluohjain!!!

# Introduction
This repository is for fetching service data from YTR. Service data is transformed into a rather simple document format and stored into MongoDB for service match engine to use. This container can be invoked on-demand in Azure Container Instances to match the data in MongoDB and source system(s). This container can then be scheduled to start with Azure Logic Apps.

This service can be tested by running it as local container.

# Getting Started

Deploying locally:

You need an accessible MongoDB server and Docker installed on your local machine.

1. Ensure that you have a MongoDB to run on your host machine in port 27017 or use external MongoDB server, Mongo must have database `service_db` with collection `services`. Locally, you can use the predefined Mongo container from `mongo` directory in `ServiceMatchEngine` repository. If you use that, remember to fill Mongo username and password to the Mongo container `docker-compose.yaml` file of Mongo container. Then, run `docker-compose up -d` in the `mongo` directory to start the Mongo container.
2. If you run Mongo locally **without the predefined mongo container** allow access from external IPs to MongoDB by editing Mongo configuration file, by default you cannot access MongoDB from any other IP but the host
3. Add your Mongo connection info to `ServiceDataImport/ServiceDataImportFunctionApp/local.settings.json` file. This file is only used to test the function locally.  **DO NOT PUSH THIS FILE INTO REPO AFTER ADDING YOUR DETAILS**
4. Add your Mongo host, username and password to `docker-compose.yml` file under repository root, not the one under `mongo`. If you used the Mongo container, use the same credentials.
5. Run `docker-compose up -d --build` to build images and launch containers, rerun to build it again when needed.


Deploying to Azure cloud:

There is a pipeline in YTRServiceDataImport repository to automatically deploy changes of function into Azure Container Instance testing or production when a change happens in `dev` or `main` branch.
