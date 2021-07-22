# Welcome to your remote flow.


## Overview

We use [Prefect](https://www.prefect.io) to orchestrate the different steps of our pipeline. Each Prefect run will be a DAG with the following steps:

1. Data preparation using [dbt](https://www.getdbt.com).
2. Data validation using [Great Expectations](https://greatexpectations.io).
3. Model training using [Metaflow](https://metaflow.org) and tracked through [Weights&Biases](https://wandb.ai) and Gantry (coming soon!).
4. Model deployment using SageMaker, with a Lambda-based wrapper around it (deployed with [Serverless](https://www.serverless.com)).

![picture alt](resources/PrefectFlowSchematic.png "Prefect Flow")

Before the actual setup, we detail the role of each step and make some preliminary remarks to set the stage for our first run.

### 1. Data preparation

Data preparation is done via [dbt](https://www.getdbt.com). We _assume_ a [Snowflake](https://www.snowflake.com) instance is configured and preloaded with the data (see [Loading the data](#loading-the-data)).

The goal of this step is to produce (in a SQL-friendly, versioned, reliable way) a normalized dataset that can be loaded for training: in particular, we create views and tables which are validated in the next step.

### 2. Data validation

It's important to validate that the data we have prepared in our previous step respect a set of requirements we know as part of our data and domain knowledge. For example, this step can be used to make sure we have no duplicate events or empty sessions which could negatively effect training.

As in a real scenario data will be streaming to our source table, everytime we run the preparation step the output will be updated with the latest data. We use Great Expectations to create "expectations", that is requirements which are verified on the incoming data.


### 3. Model training

Once the data has been validated, we can launch the training.

For this step we leverage [Metaflow](https://metaflow.org), which creates its own DAG for the ML code, and allows us to specify different computing resources for each task: this is extremely helpful as it ensures we only use a GPU when we _really_ need it (or 4 or 8, if necessary, without changes in the business logic). We explained [elsewhere](https://towardsdatascience.com/noops-machine-learning-3893a42e32a4) why we like Metaflow, so we won't go much into details here.

While Metaflow handles our training steps, we use [Weights&Biases](https://wandb.ai) as a PaaS solution for tracking metrics. This allows for quick search and comparisons between training runs and experimentation runs, while centralizing the experiments of the team in one shared dashboard.

Finally, the last step inside the flow takes the model artifact from training and deploy it as a SageMaker endpoint.

### 4. Model deployment

To expose the new SageMaker endpoint to the world, we create an [AWS Lambda](https://aws.amazon.com/lambda/), which will format and route a request to our deep learning model. As done [before many times](https://github.com/jacopotagliabue/pixel_from_lambda), we leverage the Serverless framework to deploy a Lambda-based endpoint.

## Setup

Now that we have seen the individual pieces, let's set this up!

For this setup you need to create a `remote_flow/.env` file from the template `remote_flow/example.env`. Below you find a detailed guide to configure all the envs required by this project.

A `Makefile` is provided to help you launch the proper commands.

### Docker

This workflow uses [Docker](https://www.docker.com) for the two main processes (the data upload and the prefect agent execution). All the project dependencies will be installed and runned in a sandboxed environment. If you don't have Docker already installed on your computer, you can [download it from here](https://docs.docker.com/get-docker/).


### General management of secrets

The `remote_flow/.env` file will be used to create the proper environment within the Docker.

This will also copy your `~/.aws/` folder into the docker. Since everything is run locally, this is not an issue. That being said, you should avoid pushing or sharing your docker image as it will contain your `.aws` credentials. _If you want to use this set up in a production environment it may be best to pass the relevant credentials at run time_.


### Access to AWS

This project will deploy a [CloudFormation](https://aws.amazon.com/cloudformation/) stack by using Serverless (for creating a Lambda, [API Gateway](https://aws.amazon.com/api-gateway/) and a Role). The project will also deploy a SageMaker endpoint on your AWS account.

Before proceeding with the other steps, make sure to have an AWS account and make sure your user has the privileges to create the required resources (we will provide some template policies in the future to get you started); if you're using your personal AWS account, you can temporarily create a user with the Administrator role; otherwise, ask support to your AWS administrator.

_Please remember that running this project in AWS will create resources which will be billed to the owner of the account._

Make sure to set the AWS region on your `remote_flow/.env` file:

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

You will need a [Snowflake](https://www.snowflake.com) account. The flow has a preparatory step, which uploads session-like data to Snowflake. To set up Snowflake you can follow their [Getting Started guide](https://docs.snowflake.com/en/user-guide-getting-started.html).

Create a database called `SIGIR_2021`.

Once you have setup Snowflake, you need to set the following envs in your `remote_flow/.env` file:

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

The project uses the open dataset from the [2021 Coveo Data Challenge](https://www.coveo.com/en/ailabs/sigir-ecom-data-challenge). Data is freely available under a research-friendly license (go back to the main README in this repo for more information).

Download the file, unzip it and copy all the *.csv files into the `remote_flow/data` folder.

```
# No need to change `LOCAL_DATA_PATH`, it is the absolute path of the folder inside the Docker container
LOCAL_DATA_PATH=/data
BATCH_SIZE=50000
# Optional remove to process all data
# MAX_BATCHES=
```

`BATCH_SIZE` and `MAX_BATCHES` are additional parameters to ensure the data is processed in batches and doesn't eat up all your memory.

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


### dbt

[dbt](https://www.getdbt.com) is automatically installed and configured on the Docker image, no additional setup is needed.


### Great expectations

Our expectations are configured to read from the `PUBLIC` schema. For this reason it is important that `SNOWFLAKE_SCHEMA_TARGET=PUBLIC`. This demo uses the v2 API.


### Weights&Biases

These are the envs you have to set on your `remote_flow/.env` file:

```
WANDB_API_KEY=
WANDB_ENTITY=
WANDB_PROJECT=
```

1. Create a free account on [Weights&Biases](https://wandb.ai)
2. Log in and get your API Key:
   - click on your avatar on the Top Right > `Settings`
   - scroll to the `API keys` section and copy your api key
   - set your API Key on the `WANDB_API_KEY` env
3. Set your entity name on the `WANDB_ENTITY` env\
   - it is your profile name, you'll find it on `Settings` -> `Username`
4. Create a new project:
   - go back to the home and click on `+ Create new project` on the left sidebar
   - set a project name (e.g. MetaflowIntentPrediction)
   - click on `Create project`
   - set your new project name on the `WANDB_PROJECT` env


### AWS Sagemaker

Make sure your AWS user/profile can deploy a SageMaker endpoint (this is used inside Metaflow).

Set the name of the endpoint you want to create (e.g. `metaflow-intent-remote-endpoint`):

```
SAGEMAKER_ENDPOINT_NAME=metaflow-intent-remote-endpoint
```


### Serverless

Make sure your AWS user/profile can deploy a CloudFormation stack on AWS. [Serverless](https://www.serverless.com) is automatically installed on the Docker image.


### Final .env

You final `remote_flow/.env` should match [remote_flow/example.env](example.env), with all empty values filled.


## Launching

Every time you change an environment variable, _stop and restart_ the Docker container to make sure it uses the new values.

### 1. Data upload

This is a one-time step to push the toy data to Snowflake (be patient; it may take a while to upload the data). You just have to run:

```
$ make upload
```

from the `remote_flow` directory.

This will build the Docker container and run the upload process; it will read the data from your `remote_flow/data` folder and push it to the `SNOWFLAKE_SCHEMA_SOURCE` schema, after transforming the data to make it look like raw server-side logging data.


### 2. The whole #!

Once everything is setup and raw data has been uploaded, you can run:

```
$ make run
```

from the `remote_flow` directory.

This will build a new Docker container and launch the Prefect agent; wait until your terminal shows something like:

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


Now connect to your [Prefect Cloud](https://www.prefect.io/), from the `Dashboard` section click on the `FLOWS` tab; you'll see your flow ready to be executed. Click on its name, then click on the `QUICK RUN` on the top-right.

Once launched you'll see something like this on your local terminal:

```
INFO - agent | Waiting for flow runs...
INFO - agent | Deploying flow run c5f18c7f-bd3d-47d8-94ad-c6096608ddfe to execution environment...
INFO - agent | Completed deployment of flow run c5f18c7f-bd3d-47d8-94ad-c6096608ddfe
```

You can now monitor your run from Prefect UI in the cloud.


### 3. Testing the endpoint

Once the flow has successfully completed, you can query your endpoint as follows:

```
$ curl https://<your-endpoint>/dev/predict?x=start,view,add,view,view,view,detail,view,end
```
