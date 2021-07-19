# Local Flow


## Overview


![local_flow_diagram](imgs/local_flow.png)

This version of the pipeline utilizes Metaflow as the main pipeline orchestrator. This README provides an overview of
the local version of pipeline and contains setup instructions specific to this version. For the general prerequisites,
Metaflow setup and background information about the pipeline, please refer to the main README.


As seen in the above diagram, there are four main steps in the flow:

1. Data Transformation: The dataset is read from S3 and transformed/wrangled using a GPU accelerated library [RAPIDS](https://rapids.ai/).
2. Data Validation: [Great Expectations](https://greatexpectations.io/) is used to perform data validation on the transformed data.
3. Model Training: Keras (or other ML Libraries) is used to train the model and experiment tracking is done via Weights & Biases.
4. Model Serving: The trained model is deployed on SageMaker and is exposed via a public Lambda endpoint.

[comment]: <> (   Gantry is used here for model monitoring.)


## Requirements / Prerequisites

We specify certain variables and secrets in an environment file `.env` and load them
during runtime using `dotenv`. Make a copy of `.env.local` and rename it as `.env`.

We describe the basic setup required to run this flow, and the environment variables required below.

### Packages

- Install required python packages as per `requirements.txt` in `local_flow`;

[comment]: <> (- Install Gantry as per the gantry [guide]&#40;https://docs.gantry.io/en/latest/how-to/installation.html&#41;.)

### Docker Images

Several docker images are required for use with AWS Batch in Metaflow and
for model serving on SageMaker.

- `BASE_IMAGE`: Docker image for GPU training
- `RAPIDS_IMAGE`: Docker image with [RAPIDS](https://rapids.ai/) installed
- `DOCKER_IMAGE`: Docker image for Sagemaker endpoint

### Weights & Biases
To utilise Weights & Biases, you need to obtain your account specific API key and specify the entity which you
want to associate your tracking with. You can create an account [here](https://app.wandb.ai/login?signup=true).
Further information about W&B environment variables can be found
[here](https://docs.wandb.ai/guides/track/advanced/environment-variables).

- `WANDB_API_KEY`
- `WANDB_ENTITY`

### Sagemaker
You need to have appropriate permissions for Sagemaker in AWS and specify the instance type for deployment.
  - `IAM_SAGEMAKER_ROLE`
  - `SAGEMAKER_INSTANCE`

### Serverless

For serverless, make a copy of `settings.ini.template` found in the `serverless` directory
and rename it to `serverless.ini`. It should contain the credentials with permissions for SageMaker.
   - `SAGE_USER`
   - `SAGE_SECRET`
   - `SAGE_REGION`

### Local Dataset Upload

We store the dataset in S3 which allows for quick access by Metaflow.

- `local_dataset_upload.py` performs the upload of the `.csv` dataset files
  (`browsing_train.csv`, `search_train.csv`, ...) into metaflow S3
  datastore (`METAFLOW_DATATOOLS_SYSROOT_S3` bucket) as `.parquet` files at `PARQUET_S3_PATH`;
- Specify the absolute paths to the dataset files in the following environment variables:
    - `BROWSING_TRAIN_PATH`
    - `SEARCH_TRAIN_PATH`
    - `SKU_TO_CONTENT_PATH`
- Note that there is no versioning of the dataset;
- Execute the following to upload the dataset (this might take a while depending
  on your internet connection):
  ```
  python local_dataset_upload.py
  ```
### ML Model Configuration

We define the parameters for our model configuration in a `config.json` as specified in
the environment variable `MODEL_CONFIG_PATH`.

## How to Run

### Running Metaflow

- Execute from the directory `local_flow`;
- Due to Great Expectations, `--no-pylint` flag is required;
- Execute the following to initate a run:

  ```
    python src/cart_baseline_flow.py --no-pylint run --max-workers 8
  ```
- You can also specify the Metaflow profile associated with your Metaflow setup as per the main README:

  ```
    METAFLOW_PROFILE=<METAFLOW_PROFILE_NAME> python src/cart_baseline_flow.py --no-pylint run --max-workers 8
  ```

### Running Serverless
-  Once the flow is completed, we can expose the SageMaker model via a serverless endpoint;
-  Obtain `SAGE_MAKER_ENDPOINT_NAME` from output of `deploy` step in Metaflow;
- `cd` into serverless folder;
-  Execute the following:
   ```
   serverless deploy --sagemaker <SAGEMAKER_ENDPOINT_NAME>
   ```
- You can also specify an AWS profile that is configured with the required permissions for serverless:
  ```
  serverless deploy --sagemaker <SAGEMAKER_ENDPOINT_NAME> --aws-profile <AWS_SERVERLESS_PROFILE>
  ```

- Test your endpoint by passing in click events as follows:
   ```
   https://<SERVERLESS_ENDPOINT>/dev/predict?session=add,cart,view,remove
   ```

