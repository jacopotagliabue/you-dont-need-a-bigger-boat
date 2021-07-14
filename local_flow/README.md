# Local Flow


## Overview


![local_flow_diagram](imgs/local_flow.png)

This version of the pipeline utilises Metaflow as the main pipeline orchestrator.

As seen in the above diagram, there are four main steps in the flow:

1. Data Transformation: The dataset is read from S3 and transformed/wrangled using a GPU accelerated library [RAPIDS](https://rapids.ai/).
2. Data Validation: [Great Expectations](https://greatexpectations.io/) is used to perform data validation on the transformed data.
3. Model Training: Keras (or other ML Libraries) is used to train the model and experiment tracking is done via Weights & Biases.
4. Model Serving: The trained model is deployed on SageMaker and is exposed via a public Lambda endpoint.
   Gantry is used here for model monitoring.


## Requirements / Prerequisites

We specify certain variables and secrets in an environment file `.env` and load them
during runtime using `dotenv`. Make a copy of `.env.local` and rename it as `.env`.

We describe the basic setup required to run this flow and the environment variables required below.

### Packages

- Install required python packages as per `requirements.txt` in `local_flow`;
- Install Gantry as per the gantry [guide](https://docs.gantry.io/en/latest/how-to/installation.html).

### Docker Images

Several docker images are required for use with AWS Batch in Metaflow and
for model serving on SageMaker.

- `BASE_IMAGE`: Docker image for GPU training
- `RAPIDS_IMAGE`: Docker image with [RAPIDS](https://rapids.ai/) installed
- `DOCKER_IMAGE`: Docker image for Sagemaker endpoint

### Weights & Biases
To utilise Weights & Biases, you need to obtain your account specific API key and specify the entity which you
want to associate your tracking with.

- `WANDB_API_KEY`
- `WANDB_ENTITY`

### Sagemaker
You need to have appropriate permissions for Sagemaker in AWS and specify the instance type for deployment.
- `IAM_SAGEMAKER_ROLE`
- `SAGEMAKER_INSTANCE`

### Local Dataset Upload

We store the dataset in S3 which allows for quick access by Metaflow.

- `local_dataset_upload.py` performs upload of `.csv` dataset files into metaflow S3
  datastore (`METAFLOW_DATATOOLS_SYSROOT_S3` bucket) as `.parquet` files at `PARQUET_S3_PATH`;
- The datasets are obtained based on paths specified in the environment variables:
    - `BROWSING_TRAIN_PATH`
    - `SEARCH_TRAIN_PATH`
    - `SKU_TO_CONTENT_PATH`
- Note that there is no versioning of the dataset;
- Execute the following to upload the dataset (this might take awhile depending
  on your internet connection):
  ```
  python local_dataset_upload.py
  ```


## How to Run

### Running Metaflow

- Execute from the directory `model_flow`
- Due to Great Expectations, `--no-pylint` flag is required
- Execute the following to initate a run:
  ```
    python src/cart_baseline_flow.py --no-pylint run --max-workers 8
  ```

### Running Serverless
-  Once the flow is completed, we can expose the SageMaker model via a serverless endpoint;
-  obtain `SAGE_MAKER_ENDPOINT_NAME` from output of `deploy` step in Metaflow
- `cd` into serverless folder
-  Execute the following:
   ```
   serverless deploy --sagemaker <SAGEMAKER_ENDPOINT_NAME>
   ```

- Test endpoint by passing in click events as a string : `session=add,cart,view,remove`
