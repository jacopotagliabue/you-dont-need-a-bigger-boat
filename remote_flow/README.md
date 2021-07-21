# Welcome to your remote flow.


## Overview

We used [Prefect](https://www.prefect.io) to orchestrate the different stage of the end-to-end process. Prefect will construct a run a DAG comprised of:
1. A data preparation task using [DBT](https://www.getdbt.com)
2. Data validation tasks using [Great Expectations](https://greatexpectations.io)
3. A model training task using [Metaflow](https://metaflow.org) and tracked through [Weights&Biases](https://wandb.ai) and Gantry
4. A deployment task which creates a Lambda function (using [Serverless](https://www.serverless.com)) to expose a public endpoint to our SageMaker model

![picture alt](resources/PrefectFlowSchematic.png "Prefect Flow")


### 1. Data preparation

Data preparation is done via [DBT](https://www.getdbt.com). We assume you have a [Snowflake](https://www.snowflake.com) DB configure and preloaded with some sample raw data (see [Loading the data](#loading-the-data)).

This step is in charge of most data processing. The goal is to produce a usable dataset that can be loaded in memory for training. We create views and tables which will then be validated in the next step.


### 2. Data validation

It's important to validate that the data we've prepared in our previous step follows a set of hypothesis required for training a model. For example, this step can be used to make sure we have no duplicate events or empty sessions which could negatively effect training.

As in a real scenario data will be streaming in to our source table, everytime we run the preparation step the output will be updated with the latest data. For this reason, constant validation is required.

We use [Great Expectations](https://greatexpectations.io) to create Expectations which are sets of validation we can run on the data.


### 3. Model training

Once the data has been validated, we can launch the training step.

For this step we use [Metaflow](https://metaflow.org). Metaflow will create its own DAG for the training procedure and allow us to specify different compute resources to each task. This is extremely helpful as it ensure we use a GPU when we need a GPU.

There many other advantages to using Metaflow, such as build artifact management and the possibility of resuming failed flow, for a full list of features please consult their [website](https://metaflow.org/).

While Metaflow handles our training steps we use [Weights&Biases](https://wandb.ai) for tracking training metrics.

Weights&Biases allows us to register run metrics and training parameters. This allows for quick search and comparisons between training runs and experimentation runs.

At this step the model is deployed as a SageMaker endpoint, this acts as our model registry.


### 4. Model deployment

To expose the newly trained SageMaker endpoint to the world, we create an [AWS Lambda](https://aws.amazon.com/lambda/) which will format and route a request to our SageMaker endpoint.

We do so through the use of [Serverless](https://www.serverless.com).



## Setup

Now that we have seen the individual pieces, let's set this up!

For this setup you need to create a `remote_flow/.env` file from the template `remote_flow/example.env`. Below you will find a detailed guide to configure all the envs required by this project.

A `Makefile` is provided to help you launch the proper commands.


### Docker

This workflow heavily uses [Docker](https://www.docker.com) for the 2 main processes involved on this project (the data upload and the prefect agent execution). All the project dependencies will be installed and runned in a sandboxed environment.

If you don't have Docker already installed on your computer, you can [download it from here](https://docs.docker.com/get-docker/).


### General management of secrets

The `remote_flow/.env` file will be used to create the proper environment within the Docker.

This will also copy your `~/.aws/` folder into the docker. Since everything is run locally, this is not an issue. That being said, you should avoid pushing or sharing your docker image as it will contain your `.aws` credentials. If you want to use this set up in a production environment it may be best to pass the relevant credentials at run time.


### Access to AWS

This project will deploy a [CloudFormation](https://aws.amazon.com/cloudformation/) stack by using [Serverless](https://www.serverless.com) into AWS (for creating an [Lambda Function](https://aws.amazon.com/lambda/), [API Gateway](https://aws.amazon.com/api-gateway/) and an AWS Role).

The project will also deploy a [SageMaker](https://aws.amazon.com/sagemaker/) endpoint on your AWS account.

Before proceeding with the other steps described in this guide, make sure to have an AWS account and your user has all the privileges to create all the required resources; If you're using your personal AWS account, you can temporarily create a user with the Administrator role; otherwise, ask support to your AWS administrator.

Make sure to set the AWS region you want to use on your `remote_flow/.env` file:

```
AWS_DEFAULT_REGION=us-west-2
```


#### AWS profile

If you've [already configured](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html) an AWS profile on your local computer, you can simply set its name on your `AWS_PROFILE` env:

```
AWS_PROFILE=REPLACE_MY_VALUE
```


#### AWS credentials

Otherwise, you can also explicitly set your `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` envs on the `remote_flow/.env` file:

```
AWS_ACCESS_KEY_ID=REPLACE_MY_VALUE
AWS_SECRET_ACCESS_KEY=REPLACE_MY_VALUE
```


### Access to Snowflake

You will need a [Snowflake](https://www.snowflake.com) database. The flow has a preparatory step which will upload session like data to this database. To set up Snowflake you can follow their [Getting Started guide](https://docs.snowflake.com/en/user-guide-getting-started.html).

Create a database called `SIGIR_2021`.

Once you have setup Wsnowflake you need to set all the following envs in your `remote_flow/.env` file:

```
SNOWFLAKE_USER=
SNOWFLAKE_PWD=
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_ROLE=
SNOWFLAKE_WAREHOUSE=
SNOWFLAKE_DB=SIGIR_2021
SNOWFLAKE_SCHEMA_SOURCE=SIGIR_2021_DEMO
SNOWFLAKE_SCHEMA_TARGET=PUBLIC
```


### Loading the data

The project uses the open dataset from the [2021 Coveo Data Challenge](https://github.com/coveooss/SIGIR-ecom-data-challenge).
Data is freely available under a research-friendly license.

Download the file, unzip it and copy all the *.csv files into the `remote_flow/data` folder.

```
# No need to change `LOCAL_DATA_PATH`, it is the absolute path of the folder inside the Docker container
LOCAL_DATA_PATH=/data
BATCH_SIZE=50000
# Optional remove to process all data
# MAX_BATCHES=
```

`BATCH_SIZE` and `MAX_BATCHES` are additional parameters to set to ensure the data is processed in batches and doesn't eat up all your memory.

This preparation step also requires the Snowflake variables.


### Metaflow

Please refer to the [setup instructions](../README.md) at the root level of this repository.

Additionally, you will want to make sure that these values are properly set:

```
METAFLOW_PROFILE=metaflow
MODEL_CONFIG_PATH=config.json
# You can set a value for `BASE_IMAGE` if you want to use a custom Docker image, or you can leave it empty
# BASE_IMAGE=
EN_BATCH=1
```

**Important: You need to have an aws profile named `metaflow` which has the required permissions.**


### Prefect

These are the envs you have to set on your `remote_flow/.env` file:

```
PREFECT__CLOUD__AUTH_TOKEN=
PREFECT_PROJECT_NAME=
PREFECT_FLOW_NAME=
PREFECT__SERVER__HOST=https://api.prefect.io
```

1. Create a free account on [Prefect](https://www.prefect.io)
2. Log in and create a new API Key:
   - click on your avatar on the Top Right > `Account Settings`
   - on the sidebar, click on `API Keys`
   - click on `CREATE AN API KEY`, set a name (e.g. MetaflowIntentPrediction) and click on `CREATE`
   - set your new API Key on the `PREFECT__CLOUD__AUTH_TOKEN` env
3. Create a new project:
   - click on the drop-down menu `PROJECT: All projects` on the right side of the dashboard
   - click on `New Project`
   - set your project name (e.g. MetaflowIntentPrediction) and click on `ADD PROJECT`
   - set your new project name on the `PREFECT_PROJECT_NAME` env
4. Set the flow name on the `PREFECT_FLOW_NAME` env (e.g. RemoteFlow)


### DBT

[DBT](https://www.getdbt.com) is automatically installed and configured on the Docker image, no additional setup is needed.


### Great expectations

Our expectations are configured to read from the `PUBLIC` schema. For this reason it is important that `SNOWFLAKE_SCHEMA_TARGET=PUBLIC`.

This demo used the v2 API.


### Weights&Biases

These are the envs you have to set on your `remote_flow/.env` file:

```
WANDB_API_KEY=
WANDB_PROJECT=
WANDB_ENTITY=
```

1. Create a free account on [Weights&Biases](https://wandb.ai)
2. Log in and get your API Key:
   - click on your avatar on the Top Right > `Settings`
   - scroll to the `API keys` section and copy your api key
   - set your API Key on the `WANDB_API_KEY` env
3. Create a new project:
   - go back to the home and click on `+ Create new project` on the left sidebar
   - set a project name (e.g. MetaflowIntentPrediction)
   - click on `Create project`
   - set your new project name on the `WANDB_PROJECT` env
4. Set a entity name on the `WANDB_ENTITY` env (e.g. CartAbandonment)


### AWS Sagemaker

Make sure your AWS user/profile can deploy a SageMaker endpoint. This is used during the Metaflow step.

Set the name of the endpoint you want to create (e.g. `metaflow-intent-remote-endpoint`):

```
SAGEMAKER_ENDPOINT_NAME=metaflow-intent-remote-endpoint
```


### Serverless

Make sure your AWS user/profile can deploy a CloudFormation stack on AWS. [Serverless](https://www.serverless.com) is automatically installed on the Docker image.


### Final .env

You final `remote_flow/.env` should match [remote_flow/example.env](example.env) with all empty values filled.



## Launching

Every time you change an environment variable, make sure to stop and restart the Docker container to make sure it uses your new values.


### 1. Data upload

This is a one-time step to push the toy data to Snowflake. Be patient; it will take a while having to upload ~8 GB of data. You just have to run:

```
$ make upload
```

from the `remote_flow` directory.

This will build the Docker container and run the upload process; it will read the data from your `remote_flow/data` folder and push it to the `SNOWFLAKE_SCHEMA_SOURCE` schema after transforming the data to make it look like raw server-side logging data.


### 2. The whole #!

Once everything is setup and your raw data has been uploaded, you can run:

```
$ make run
```

from the `remote_flow` directory.

This will build a new Docker container and launch the Prefect agent; Wait until your terminal doesn't show you something like:

```
INFO - agent | Registering agent...
INFO - agent | Registration successful!

 ____            __           _        _                    _
|  _ \ _ __ ___ / _| ___  ___| |_     / \   __ _  ___ _ __ | |_
| |_) | '__/ _ \ |_ / _ \/ __| __|   / _ \ / _` |/ _ \ '_ \| __|
|  __/| | |  __/  _|  __/ (__| |_   / ___ \ (_| |  __/ | | | |_
|_|   |_|  \___|_|  \___|\___|\__| /_/   \_\__, |\___|_| |_|\__|
                                           |___/

INFO - agent | Starting LocalAgent with labels ['268dca2f9aaf']
INFO - agent | Agent documentation can be found at https://docs.prefect.io/orchestration/
INFO - agent | Waiting for flow runs...
```


Now connect to your [Prefect Cloud](https://www.prefect.io/), from the `Dashboard` section click on the `FLOWS` tab; you'll see your flow ready to be executed. Click on its name, then click on the `RUN` tab and finally click on `RUN` to launch it.

Once launched you'll see something like this on your local terminal:

```
INFO - agent | Waiting for flow runs...
INFO - agent | Deploying flow run c5f18c7f-bd3d-47d8-94ad-c6096608ddfe to execution environment...
INFO - agent | Completed deployment of flow run c5f18c7f-bd3d-47d8-94ad-c6096608ddfe
```

You can now monitor your task from Prefect.


### 3. Testing the endpoint

Once the flow has successfully completed you can query your endpoint as follows:

```
$ curl https://<your-endpoint>/dev/predict?x=start,view,add,view,view,view,detail,view,end
```
