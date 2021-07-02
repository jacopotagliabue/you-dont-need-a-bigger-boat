#Welcome to your remote flow.

###Overview

We used Prefect to orchestrate the different stage of the end-to-end process. Prefect will construct a run a DAG
comprised of: 
1. A data preparation task using DBT
2. Data validation tasks using Great Expectations
3. A model training task using Metaflow and tracked through Weights&Biases and Gantry
4. A deployment task which creates a lambda to expose a public endpoint to our SageMaker model

![picture alt](resources/PrefectFlowSchematic.png "Prefect Flow")

####1. Data preparation

Data preparation is done via DBT. We assume you have a Snowflake DB configure and preloaded with some sample 
raw data (see [Loading the data](#loading-the-data)). 

This step is in charge of most data processing. The goal is to produce a usable dataset that can be loaded in 
memory for training. We create views and tables which will then be validated in the next step.

####2. Data validation

It's important to validate that the data we've prepared in our previous step follows a set of hypothesis required
for training a model. For example this step can be used to make sure we have no duplicate events or empty sessions
which could negatively effect training. 

As in a real scenario data will be streaming in to our source table, everytime we run the preparation step the output
will be updated with the latest data. For this reason, constant validation is required. 

We use Great Expectation to create Expectations which are sets of validation we can run on the data.

####3. Model training

Once the data has been validated, we can launch the training step. For this step we use Metaflow. Metaflow will create its own
DAG for the training procedure and allow us to specify different compute resources to each task. This is extremely helpful as it
ensure we use a GPU when we need a GPU. There many other advantages to using Metaflow, such as build artifact management and the
possibility of resuming failed flow, for a full list of features please consult their [website](https://metaflow.org/). 

While Metaflow handles our training steps, we use two other tools for tracking:  Weights&Biases for training metrics and Gantry
online metrics. 

Weights&Biases allows us to register run metrics and training parameters to an external server. This allows for quick search and 
comparisons between training runs and experimentation runs. 

Gantry on the other hand allows us to compare our training data to the data the model receives once deployed. This allows for the 
early detection of data or model drift and accurate tracking of performance metrics for deployed models.

At this step the model is deployed as a SageMaker endpoint, this acts as our model registry. 

####4. Model deployment

To expose the newly trained SageMaker endpoint to the world, we create a lambda which will format and route a request to our SageMaker endpoint. 
We so so through the use of serverless.


###Setup

Now that we have seen the individual pieces, let's set this up!

####General management of secrets

This project manages secrets by placing them in a .env file under the `remote_flow` directory and loading
them with the `dotenv` package.  There is a sample file named `.env.local` you can use as a template. 

####Loading the data

The project uses the open dataset from the [2021 Coveo Data Challenge](https://github.com/coveooss/SIGIR-ecom-data-challenge).
Data is freely available under a research-friendly license.

Add the path to the `.env` file under 
```
LOCAL_DATA_PATH='path to your data'
```

We recommend using an absolute data path for this demo.

There are additional parameters to set to ensure the data is processed in batches and doesn't
eat up all your memory. 

```
BATCH_SIZE=set the number of rows you want to load at once
MAX_BATCHES=max number of batches to process (optional, remove from .env to process all the data)
```

This preparation step also requires the SNOWFLAKE variables set [below](access-to-snowflake). 

####Metaflow

Please refer to the [setup instructions](../README.md) at the root level of this repository.

####Access to Snowflake

You will need a snowflake database. The flow has a preperatory step which will upload session
like data to this database. To set up snowflake you can follow their [Getting Started guide](https://docs.snowflake.com/en/user-guide-getting-started.html).

Once you have setup snowflake you need to add the following:
```
SNOWFLAKE_USER=
SNOWFLAKE_PWD=
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_ROLE=
SNOWFLAKE_WAREHOUSE=
SNOWFLAKE_DB=
SNOWFLAKE_SCHEMA_SOURCE=schema to put the "raw" data in
SNOWFLAKE_SCHEMA_TARGET=schema for the transformed view and tables
```

#### Prefect

#### dbt

#### Great expectations

#### Weights&Biases

#### Gantry

#### AWS Sagemaker

#### Serverless

#### Final .env

You final `.env` should have all the following values:
```
SNOWFLAKE_USER=
SNOWFLAKE_PWD=
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_ROLE=
SNOWFLAKE_WAREHOUSE=
SNOWFLAKE_DB=
SNOWFLAKE_SCHEMA_SOURCE=
SNOWFLAKE_SCHEMA_TARGET=
SNOWFLAKE_PRODUCTS_TABLE=
SNOWFLAKE_SNAPSHOT_TABLE=

PREFECT__CLOUD__AUTH_TOKEN=
PREFECT_AGENT_KEY_ANDREW=
PREFECT_AGENT_KEY_NO=
PREFECT_PROJECT_NAME=
PREFECT_PROFILE_DIR=
PREFECT__SERVER__HOST=

LOCAL_DATA_PATH=
BATCH_SIZE=

DBT_PROFILES_DIR=

WANDB_API_KEY=
WANDB_ENTITY=

BROWSING_TRAIN_PATH=
MODEL_CONFIG_PATH=

BASE_IMAGE=
EN_BATCH=
SAGEMAKER_ENDPOINT_NAME=
```
