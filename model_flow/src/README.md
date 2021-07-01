### Requirements

- Install python requirements as per `requirements.txt` in main folder;
- Install gantry as per the gantry [guide](https://docs.gantry.io/en/latest/tutorials/local.html).

### Local Dataset Upload 

- `local_dataset_upload.py` performs upload of .csv dataset files into metaflow S3 datastore as .parquet files at `PARQUET_S3_PATH`
-  There is no versioning of the dataset
- The datasets are obtained based on paths specified in  environment variables `BROWSING_TRAIN_PATH`, `SEARCH_TRAIN_PATH`,`SKU_TO_CONTENT_PATH` in the `.env` file.
- It is required that Metaflow is configured for use with the artifact store
- __Note__: The data is already stored in S3, so technically this step can be skipped.


### Docker Images

- `BASE_IMAGE` : Docker image for GPU training
- `RAPIDS_IMAGE` : Docker image with [RAPIDS](https://rapids.ai/) installed 
- `DOCKER_IMAGE_URI`: Docker image for Sagemaker endpoint 

### Running Metaflow

- Execute from the directory `model_flow`
- Due to Great Expectations, `--no-pylint` flag is required.

### Running Serverless