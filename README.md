# metaflow-intent-prediction
An end-to-end (Metaflow-based) implementation of an intent prediction flow for kids who can't MLOps 
good and [wanna learn to do other stuff good too](https://www.youtube.com/watch?v=NQ-8IuUkJJc). 

## Overview
WIP

## Repo structure
WIP

## How to run the code
WIP

### Prerequisites

#### Download the dataset

The project uses the open dataset from the [2021 Coveo Data Challenge](https://github.com/coveooss/SIGIR-ecom-data-challenge).
Data is freely available under a research-friendly license.

#### Configure Metaflow

If you have an AWS profile configured with a metaflow-friendly user, and you created 
metaflow stack with CloudFormation, you can run the following command with the resources
created by CloufFormation to set up metaflow on AWS:

`metaflow configure aws --profile metaflow`

Remember to use `METAFLOW_PROFILE=metaflow` to use this profile when running a flow. Once
you completed the [setup](https://admin-docs.metaflow.org/metaflow-on-aws/deployment-guide/aws-cloudformation-deployment), you can run `flow_playground.py` to test the AWS setup is working
as expected (in particular, GPU batch jobs can run correctly). To run the flow with the
custom profile created, you should do:

`METAFLOW_PROFILE=metaflow python flow_playground.py run`

### Tips & Tricks

1. Parallelism Safe Guard
   - The flag `--max-workers` __should__ be used to limit the maximum number of parallel steps
   - For example `METAFLOW_PROFILE=metaflow python flow_playground.py run --max-workers 8` limits
     the maximum number of parallel tasks to 8
2. Environment Variables in AWS Batch
   - The `@environment` decorator is used in conjunction with `@batch` to pass environment variables to
     AWS Batch, which will not directly have access to env variables on your local machine
   - In the basic `CartFlow` example, we use `@environemnt` to pass the Weights & Biases API Key (amongst other things)
3. Resuming Flows
   - Resuming flows is useful during development to avoid re-running compute/time intensive steps
     such as data preparation
   - `METAFLOW_PROFILE=metaflow python flow_playground.py resume <STEP_NAME> --origin-run-id <RUN_ID>`
4. Local-Only execution
   - It may sometimes be useful to debug locally (i.e to avoid Batch startup latency), we introduce a wrapper 
     `enable_decorator` around the `@batch` decorator which enables or disables a decorator's functionality
   - We use this in conjunction with an environment variable `EN_BATCH` to toggle the functionality
    of __all__ `@batch` decorators.