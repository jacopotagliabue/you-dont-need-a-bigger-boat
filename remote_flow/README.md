# Welcome to your remote flow.

This is the remote version of the flow it uses the full set of tools:
* [Metaflow](https://metaflow.org/) for ML DAGs
* Snowflake as a data warehouse solution 
* Prefect as a general orchestrator
* dbt for data transformation
* Great Expectations for data quality
* Weights&Biases for experiment tracking
* Gantry for ML monitoring
* AWS Sagemaker / AWS lambda for model serving 
* Serverless for deploying the lambda

Being a full flow it has multiple prerequisites.

### Prerequisites

#### General management of secrets

This project manages secrets by placing them in a .env file under the `remote_flow` directory and loading
them with the `dotenv` package.  There is a sample file named `.env.local` you can use as a template. 
The different values required are 

#### Loading the data

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

This preperation step also requires the SNOWFLAKE variables set below. 

#### Metaflow

If you have an AWS profile configured with a metaflow-friendly user, and you created 
metaflow stack with CloudFormation, you can run the following command with the resources
created by CloufFormation to set up metaflow on AWS:

`metaflow configure aws --profile metaflow`

Remember to use `METAFLOW_PROFILE=metaflow` to use this profile when running a flow. Once
you completed the [setup](https://admin-docs.metaflow.org/metaflow-on-aws/deployment-guide/aws-cloudformation-deployment), you can run `flow_playground.py` to test the AWS setup is working
as expected (in particular, GPU batch jobs can run correctly).

The metaflow profile will be passed automatically to the Prefect task so make sure the profile
is named `metaflow`. 

#### Access to snowflake

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
