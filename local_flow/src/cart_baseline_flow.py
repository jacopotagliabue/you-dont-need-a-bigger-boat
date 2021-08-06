"""

Local implementation of pipeline using Metaflow

"""

# Load env variables
try:
    from dotenv import load_dotenv
    load_dotenv('.env')
except Exception as e:
    print(e)

import os
from metaflow import FlowSpec, step, batch, current, environment, Parameter, S3
from sagemaker import tensorflow
from custom_decorators import pip, enable_decorator


class CartFlow(FlowSpec):
    """
    CartFlow is a DAG that loads and transforms session data, trains a cart-abandonment/purchase-intent
    binary prediction model, and deploys the Keras model onto SageMaker.
    """

    # uri from: https://github.com/aws/deep-learning-containers/blob/master/available_images.md
    DOCKER_IMAGE_URI = Parameter(
        name='sagemaker_image',
        help='AWS Docker Image URI for SageMaker Inference',
        default='763104351884.dkr.ecr.us-west-2.amazonaws.com/tensorflow-inference:2.3.0-gpu-py37-cu102-ubuntu18.04'
    )

    SAGEMAKER_INSTANCE = Parameter(
        name='sagemaker_instance',
        help='AWS Instance to Power SageMaker Inference',
        default='ml.t2.medium'
    )

    # this is the name of the IAM role with SageMaker permissions
    # make sure this role has access to the bucket containing the tar file!
    IAM_SAGEMAKER_ROLE = Parameter(
        name='sagemaker_role',
        help='AWS Role for SageMaker',
        default='MetaSageMakerRole'
    )

    @step
    def start(self) -> None:
        """
        Start Step for a Flow;
        """
        print(f"flow name: {current.flow_name}")
        print(f"run id: {current.run_id}")
        print(f"username: {current.username}")

        # Call next step in DAG with self.next(...)
        self.next(self.process_raw_data)

    # These compute requirements are compatible with p3.2xlarge (https://www.amazonaws.cn/en/ec2/instance-types/)
    @enable_decorator(batch(gpu=1, cpu=8, memory=60000, image=os.getenv('RAPIDS_IMAGE')),
                      flag=os.getenv('EN_BATCH', False))
    @environment(vars={'PARQUET_S3_PATH': os.environ['PARQUET_S3_PATH'],
                       'SEARCH_TRAIN_FILE_NAME': os.getenv('SEARCH_TRAIN_FILE_NAME', 'search_train.csv'),
                       'BROWSING_TRAIN_FILE_NAME': os.getenv('BROWSING_TRAIN_FILE_NAME', 'browsing_train.csv'),
                       'SKU_TO_CONTENT_FILE_NAME': os.getenv('SKU_TO_CONTENT_FILE_NAME', 'sku_to_content.csv')})
    @pip(libraries={'boto3': '1.17.11', 's3fs': '0.4.2', 'pandas': '1.2.4'})
    @step
    def process_raw_data(self) -> None:
        """
        Read data from S3 datastore and process/transform/wrangle
        """
        import os
        from typing import Dict
        from process_raw_data import process_raw_data
        from utils import get_filename
        from metaflow.metaflow_config import DATATOOLS_S3ROOT

        # get dataset S3 paths
        DATASET_PATH = os.path.join(
            DATATOOLS_S3ROOT, os.environ['PARQUET_S3_PATH'])
        SEARCH_TRAIN_PATH = os.path.join(DATASET_PATH,
                                         get_filename(os.environ['SEARCH_TRAIN_FILE_NAME'], 'parquet'))
        BROWSING_TRAIN_PATH = os.path.join(DATASET_PATH,
                                           get_filename(os.environ['BROWSING_TRAIN_FILE_NAME'], 'parquet'))
        SKU_TO_CONTENT_PATH = os.path.join(DATASET_PATH, get_filename(
            os.environ['SKU_TO_CONTENT_FILE_NAME'], 'parquet'))

        # process raw data
        processed_data = process_raw_data(search_train_path=SEARCH_TRAIN_PATH,
                                          browsing_train_path=BROWSING_TRAIN_PATH,
                                          sku_to_content_path=SKU_TO_CONTENT_PATH)

        # save as parquet onto S3
        with S3(run=self) as s3:
            # save s3 paths in dict
            self.data_paths: Dict[str, str] = dict()
            s3_root: str = s3._s3root
            for name, data in processed_data.items():
                data_path = os.path.join(s3_root, f"{name}.parquet")
                data.to_parquet(path=data_path, engine='pyarrow')
                self.data_paths[name] = data_path

        print(self.data_paths)

        self.next(self.data_validation)

    @ step
    def data_validation(self) -> None:
        """
        Perform data validation with great_expectations
        """
        from data_validation import validate_data

        validate_data(current.run_id, current.flow_name, self.data_paths)

        self.next(self.prepare_dataset)

    @ step
    def prepare_dataset(self) -> None:
        """
        Read in raw session data and build a labelled dataset for purchase/abandonment prediction
        """
        from prepare_dataset import prepare_dataset

        self.dataset = prepare_dataset(
            training_file=self.data_paths['browsing_train'], K=300000)

        self.next(self.get_model_config)

    @ step
    def get_model_config(self) -> None:
        """
        Get model hyper-params;
        It is possible in this step perform a for-each to parallel run over a range of hyper params;
        """
        from utils import return_json_file_content

        # read just a single configuration
        self.config = return_json_file_content(
            os.environ.get('MODEL_CONFIG_PATH', 'config.json'))
        self.next(self.train_model)

    # @batch decorator used to run step on AWS Batch
    # wrap batch in a switch to allow easy local testing

    @ enable_decorator(batch(gpu=1, cpu=8, image=os.getenv('BASE_IMAGE')),
                       flag=os.getenv('EN_BATCH', False))
    # @ environment decorator used to pass environment variables to Batch instance
    @ environment(vars={'WANDB_API_KEY': os.environ['WANDB_API_KEY'],
                        'WANDB_ENTITY': os.environ['WANDB_ENTITY']})
    # @ custom pip decorator for pip installation on Batch instance
    @ pip(libraries={'wandb': '0.10.30'})
    @ step
    def train_model(self) -> None:
        """
        Train an intention prediction model on GPU.
        """
        import wandb
        from model import train_lstm_model

        # initialize wandb for tracking
        wandb.init(entity=os.environ['WANDB_ENTITY'],
                   project="cart-abandonment",
                   id=current.run_id,
                   config=self.config,
                   resume='allow',
                   reinit=True)

        self.model, self.model_weights = train_lstm_model(x=self.dataset['X'],
                                                          y=self.dataset['y'],
                                                          epochs=self.config['EPOCHS'],
                                                          patience=self.config['PATIENCE'],
                                                          lstm_dim=self.config['LSTM_DIMS'],
                                                          batch_size=self.config['BATCH_SIZE'],
                                                          lr=self.config['LEARNING_RATE'])
        self.next(self.deploy)

    @ step
    def deploy(self) -> None:
        """
        Deploy model on SageMaker
        """
        import os
        from tensorflow.keras import Sequential
        from tensorflow.keras.models import model_from_json
        from deploy_model import deploy_model, tf_model_to_tar

        # load model from artifacts
        tf_model: Sequential = model_from_json(self.model)
        tf_model.set_weights(self.model_weights)

        # save model as .tar.gz onto S3 for SageMaker
        local_tar_name = tf_model_to_tar(tf_model, current.run_id)
        # save model to S3
        with open(local_tar_name, "rb") as in_file:
            data = in_file.read()
            with S3(run=self) as s3:
                url: str = s3.put(local_tar_name, data)
                # print it out for debug purposes
                print(f"Model saved at: {url}")
                # save this path for downstream reference!
                self.model_s3_path = url
                # remove local compressed model
                os.remove(local_tar_name)

        # deploy model on SageMaker
        self.endpoint_name = deploy_model(self.model_s3_path,
                                          image_uri=str(self.DOCKER_IMAGE_URI),
                                          role=str(self.IAM_SAGEMAKER_ROLE),
                                          sagemaker_instance=str(self.SAGEMAKER_INSTANCE))

        self.next(self.end)

    @ step
    def end(self) -> None:
        """
        DAG is done!
        """
        print('DAG ended!')


if __name__ == '__main__':
    CartFlow()
