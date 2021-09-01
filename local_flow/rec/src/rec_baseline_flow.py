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


class RecFlow(FlowSpec):
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

        # skip for now!
        # validate_data(current.run_id, current.flow_name, self.data_paths)

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
    # @enable_decorator(batch(gpu=1, cpu=8, image=os.getenv('BASE_IMAGE')),
    #                   flag=os.getenv('EN_BATCH'))
    # @ environment decorator used to pass environment variables to Batch instance
    # @environment(vars={'WANDB_API_KEY': os.getenv('WANDB_API_KEY'),
    #                    'WANDB_ENTITY': os.getenv('WANDB_ENTITY'),
    #                    'BASE_IMAGE': os.getenv('BASE_IMAGE'),
    #                    'EN_BATCH': os.getenv('EN_BATCH')})
    # # @ custom pip decorator for pip installation on Batch instance
    # @pip(libraries={'wandb': '0.10.30', 'gensim': '4.0.1'})
    @step
    def train_model(self):
        """
        Train a prod2vec or ProdB model.
        """
        import wandb
        from model import train_prod2vec_model, train_prodb_model

        assert os.getenv('WANDB_API_KEY')
        assert os.getenv('WANDB_ENTITY')
        assert os.getenv('MODEL_CHOICE') in ['KNN','PRODB']

        # initialize wandb for tracking
        wandb.init(entity=os.getenv('WANDB_ENTITY'),
                   project="recommendation",
                   id=current.run_id,
                   config=self.config,
                   resume='allow',
                   reinit=True)

        # choose either k-NN model or BERT model
        if os.getenv('MODEL_CHOICE') == 'KNN':
            self.model, self.token_mapping = train_prod2vec_model(self.dataset)
        else:
            self.model, self.token_mapping = train_prodb_model(self.dataset)

        self.next(self.deploy)

    @step
    def deploy(self):
        """
        Deploy model on SageMaker
        """
        import json
        from deploy_model import deploy_tf_model

        # deploy onto SM
        with S3(run=self) as s3:
            self.model_s3_path, self.endpoint_name = deploy_tf_model(self.model,
                                                                     s3,
                                                                     current.run_id,
                                                                     self.token_mapping)


        self.token_mapping_fname = 'serverless/token-mapping-{}.json'.format(self.endpoint_name)
        # save mappings to serverless folder
        with open(self.token_mapping_fname, 'w') as f:
            json.dump(self.token_mapping,f)

        self.next(self.end)

    @step
    def end(self):
        """
        DAG is done!
        """
        print('DAG ended!')


if __name__ == '__main__':
    RecFlow()
