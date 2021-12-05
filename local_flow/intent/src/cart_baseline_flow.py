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
from metaflow import FlowSpec, step, batch, current, environment, S3
from custom_decorators import pip, enable_decorator


class CartFlow(FlowSpec):
    """
    CartFlow is a DAG that loads and transforms session data, trains a cart-abandonment/purchase-intent
    binary prediction model, and deploys the Keras model onto SageMaker.
    """

    @step
    def start(self):
        """
        Start Step for a Flow;
        """
        print("flow name: %s" % current.flow_name)
        print("run id: %s" % current.run_id)
        print("username: %s" % current.username)

        # Call next step in DAG with self.next(...)
        self.next(self.process_raw_data)

    # These compute requirements are compatible with p3.2xlarge (https://www.amazonaws.cn/en/ec2/instance-types/)
    @enable_decorator(batch(gpu=1, cpu=8, memory=60000, image=os.getenv('RAPIDS_IMAGE')),
                      flag=os.getenv('EN_BATCH'))
    @environment(vars={'RAPIDS_IMAGE': os.getenv('RAPIDS_IMAGE'),
                       'PARQUET_S3_PATH': os.getenv('PARQUET_S3_PATH'),
                       'SEARCH_TRAIN_PATH': os.getenv('SEARCH_TRAIN_PATH'),
                       'BROWSING_TRAIN_PATH': os.getenv('BROWSING_TRAIN_PATH'),
                       'SKU_TO_CONTENT_PATH': os.getenv('SKU_TO_CONTENT_PATH')})
    @pip(libraries={'boto3': '1.17.11', 's3fs': '0.4.2', 'pandas': '1.2.4'})
    @step
    def process_raw_data(self):
        """
        Read data from S3 datastore and process/transform/wrangle
        """
        import os
        from process_raw_data import process_raw_data
        from utils import get_filename
        from metaflow.metaflow_config import DATATOOLS_S3ROOT

        # get dataset S3 paths
        DATASET_PATH = os.path.join(
            DATATOOLS_S3ROOT, os.getenv('PARQUET_S3_PATH'))
        SEARCH_TRAIN_PATH = os.path.join(DATASET_PATH, get_filename(
            os.getenv('SEARCH_TRAIN_PATH')) + '.parquet')
        BROWSING_TRAIN_PATH = os.path.join(DATASET_PATH, get_filename(
            os.getenv('BROWSING_TRAIN_PATH')) + '.parquet')
        SKU_TO_CONTENT_PATH = os.path.join(DATASET_PATH, get_filename(
            os.getenv('SKU_TO_CONTENT_PATH')) + '.parquet')

        # process raw data
        processed_data = process_raw_data(search_train_path=SEARCH_TRAIN_PATH,
                                          browsing_train_path=BROWSING_TRAIN_PATH,
                                          sku_to_content_path=SKU_TO_CONTENT_PATH)

        # save as parquet onto S3
        with S3(run=self) as s3:
            # save s3 paths in dict
            self.data_paths = dict()
            s3_root = s3._s3root
            for name, data in processed_data.items():
                data_path = os.path.join(s3_root, name + '.parquet')
                data.to_parquet(path=data_path, engine='pyarrow')
                self.data_paths[name] = data_path

        print(self.data_paths)

        self.next(self.data_validation)

    @step
    def data_validation(self):
        """
        Perform data validation with great_expectations
        """
        from data_validation import validate_data

        validate_data(current.run_id, current.flow_name, self.data_paths)

        self.next(self.prepare_dataset)

    @step
    def prepare_dataset(self):
        """
        Read in raw session data and build a labelled dataset for purchase/abandonment prediction
        """
        from prepare_dataset import prepare_dataset

        self.dataset = prepare_dataset(
            training_file=self.data_paths['browsing_train'], K=300000)

        self.next(self.get_model_config)

    @step
    def get_model_config(self):
        """
        Get model hyper-params;
        It is possible in this step perform a for-each to parallel run over a range of hyper params;
        """
        from utils import return_json_file_content

        # read just a single configuration
        self.config = return_json_file_content(os.getenv('MODEL_CONFIG_PATH'))
        self.next(self.train_model)

    # @batch decorator used to run step on AWS Batch
    # wrap batch in a switch to allow easy local testing

    @enable_decorator(batch(gpu=1, cpu=8, image=os.getenv('BASE_IMAGE')),
                      flag=os.getenv('EN_BATCH'))
    # @ environment decorator used to pass environment variables to Batch instance
    @environment(vars={'NEPTUNE_PROJECT': os.getenv('NEPTUNE_PROJECT'),
                       'NEPTUNE_API_TOKEN': os.getenv('NEPTUNE_API_TOKEN'),
                       'NEPTUNE_CUSTOM_RUN_ID': os.getenv('NEPTUNE_CUSTOM_RUN_ID'),
                       'WANDB_API_KEY': os.getenv('WANDB_API_KEY'),
                       'WANDB_ENTITY': os.getenv('WANDB_ENTITY'),
                       'BASE_IMAGE': os.getenv('BASE_IMAGE'),
                       'EN_BATCH': os.getenv('EN_BATCH')})
    # @ custom pip decorator for pip installation on Batch instance
    @pip(libraries={'wandb': '0.10.30', "neptune-client": "0.13.3", "neptune-tensorflow": "0.9.9"})
    @step
    def train_model(self):
        """
        Train an intention prediction model on GPU.
        """
        
        from model import train_lstm_model
        from utils import ExperimentTracker


        # initialize neptune or wandb for tracking
        tracker = ExperimentTracker(
            tracker_name='neptune', # or 'wandb'
            current_run_id=current.run_id,
            config=self.config
        )

        self.model, self.model_weights = train_lstm_model(x=self.dataset['X'],
                                                          y=self.dataset['y'],
                                                          epochs=self.config['EPOCHS'],
                                                          patience=self.config['PATIENCE'],
                                                          lstm_dim=self.config['LSTM_DIMS'],
                                                          batch_size=self.config['BATCH_SIZE'],
                                                          lr=self.config['LEARNING_RATE'],
                                                          tracker_callback=tracker.get_tracker_callback())
        self.next(self.deploy)

    @step
    def deploy(self):
        """
        Deploy model on SageMaker
        """
        import os
        from tensorflow.keras.models import model_from_json
        from deploy_model import deploy_model, tf_model_to_tar

        # load model from artifacts
        tf_model = model_from_json(self.model)
        tf_model.set_weights(self.model_weights)

        # save model as .tar.gz onto S3 for SageMaker
        local_tar_name = tf_model_to_tar(tf_model, current.run_id)
        # save model to S3
        with open(local_tar_name, "rb") as in_file:
            data = in_file.read()
            with S3(run=self) as s3:
                url = s3.put(local_tar_name, data)
                # print it out for debug purposes
                print("Model saved at: {}".format(url))
                # save this path for downstream reference!
                self.model_s3_path = url
                # remove local compressed model
                os.remove(local_tar_name)

        # deploy model on SageMaker
        self.endpoint_name = deploy_model(self.model_s3_path)

        self.next(self.end)

    @step
    def end(self):
        """
        DAG is done!
        """
        print('DAG ended!')


if __name__ == '__main__':
    CartFlow()
