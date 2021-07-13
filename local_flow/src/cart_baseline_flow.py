"""

    Baseline implemented using Metaflow

"""

# Load env variables
try:
    from dotenv import load_dotenv
    load_dotenv('.env')
except Exception as e:
    print(e)

import os
from metaflow import FlowSpec, step, batch, current, environment, S3, Parameter
from custom_decorators import pip, enable_decorator

class CartFlow(FlowSpec):

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

    @batch(gpu=1, cpu=8, image=os.getenv('RAPIDS_IMAGE'), memory=80000)
    @environment(vars={'RAPIDS_IMAGE': os.getenv('RAPIDS_IMAGE'),
                       'PARQUET_S3_PATH': os.getenv('PARQUET_S3_PATH'),
                       'SEARCH_TRAIN_PATH': os.getenv('SEARCH_TRAIN_PATH'),
                       'BROWSING_TRAIN_PATH': os.getenv('BROWSING_TRAIN_PATH'),
                       'SKU_TO_CONTENT_PATH': os.getenv('SKU_TO_CONTENT_PATH')})
    @pip(libraries={'boto3':'1.17.11', 's3fs':'0.4.2', 'pandas': '1.2.4'})
    @step
    def process_raw_data(self):
        """
        Read data from S3 datastore and process/transform/wrangle
        """
        import os
        import pandas as pd
        from process_raw_data import process_raw_data
        from utils import get_filename
        from metaflow.metaflow_config import DATATOOLS_S3ROOT

        DATASET_PATH = os.path.join(DATATOOLS_S3ROOT,os.getenv('PARQUET_S3_PATH'))
        SEARCH_TRAIN_PATH =  os.path.join(DATASET_PATH, get_filename(os.getenv('SEARCH_TRAIN_PATH'))+ '.parquet')
        BROWSING_TRAIN_PATH = os.path.join(DATASET_PATH, get_filename(os.getenv('BROWSING_TRAIN_PATH')) + '.parquet')
        SKU_TO_CONTENT_PATH = os.path.join(DATASET_PATH, get_filename(os.getenv('SKU_TO_CONTENT_PATH')) + '.parquet')

        os.system('nvidia-smi')

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
        import pandas as pd
        import great_expectations as ge
        from datetime import datetime

        # add great_expectations/plugins to path
        import sys
        sys.path.append('great_expectations')
        from plugins.custom_expectation import ExpectAverageSessionLengthToBeBetween

        context = ge.data_context.DataContext()
        for data_name,data_path in self.data_paths.items():
            data = pd.read_parquet(data_path, engine='pyarrow')
            context.run_checkpoint(checkpoint_name='intent_checkpoint',
                                   batch_request={
                                        'datasource_name':'s3_parquet',
                                        'data_connector_name':'runtime_data_connector',
                                        'data_asset_name':data_name,
                                        'runtime_parameters':{
                                            # bug in GE prevents it from reading parquet directly
                                           'batch_data': data
                                        },
                                        'batch_identifiers':{
                                            "run_id" : current.run_id,
                                            "data_name" : data_name
                                        }
                                   },
                                   run_name= '-'.join([current.flow_name, current.run_id, data_name]),
                                   run_time=datetime.utcnow(),
                                   expectation_suite_name=data_name)
        context.build_data_docs()
        context.open_data_docs()
        self.next(self.prepare_dataset)


    @step
    def prepare_dataset(self):
        """
        Read in raw session data and build a labelled dataset for purchase/abandonment prediction
        """
        from prepare_dataset import prepare_dataset

        self.dataset = prepare_dataset(training_file=self.data_paths['browsing_train'], K=300000)

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
    @environment(vars={'WANDB_API_KEY': os.getenv('WANDB_API_KEY'),
                       'WANDB_ENTITY' : os.getenv('WANDB_ENTITY'),
                       'BASE_IMAGE': os.getenv('BASE_IMAGE'),
                       'EN_BATCH': os.getenv('EN_BATCH')})
    # @ custom pip decorator for pip installation on Batch instance
    @pip(libraries={'wandb': '0.10.30'})
    @step
    def train_model(self):
        """
        Train a intention prediction model on GPU.
        """
        import wandb
        from model import train_lstm_model

        assert os.getenv('WANDB_API_KEY')
        assert os.getenv('WANDB_ENTITY')

        wandb.init(entity=os.getenv('WANDB_ENTITY'),
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

    @step
    def deploy(self):
        """
        Deploy model on SageMaker
        """
        from sagemaker.tensorflow import TensorFlowModel
        from tensorflow.keras.models import model_from_json
        import tensorflow as tf
        import numpy as np
        import tarfile
        import time
        import os
        import shutil

        # generate a signature for the endpoint using timestamp
        self.endpoint_name = 'intent-{}-endpoint'.format(int(round(time.time() * 1000)))

        # print out the name, so that we can use it when deploying our lambda
        print("\n\n================\nEndpoint name is: {}\n\n".format(self.endpoint_name))

        # load model from artifacts
        tf_model = model_from_json(self.model)
        tf_model.set_weights(self.model_weights)

        model_name = "intent-model-{}/1".format(current.run_id)
        local_tar_name = 'model-{}.tar.gz'.format(current.run_id)

        # save model to push to S3
        tf_model.save(filepath=model_name)
        with tarfile.open(local_tar_name, mode="w:gz") as _tar:
            _tar.add(model_name, recursive=True)

        with open(local_tar_name, "rb") as in_file:
            data = in_file.read()
            with S3(run=self) as s3:
                url = s3.put(local_tar_name, data)
                # print it out for debug purposes
                print("Model saved at: {}".format(url))
                # save this path for downstream reference!
                self.model_s3_path = url

        os.remove(local_tar_name)
        shutil.rmtree(model_name.split('/')[0])

        # create sagemaker tf model
        model = TensorFlowModel(
            model_data=self.model_s3_path,
            image_uri=os.getenv('DOCKER_IMAGE'),
            role=os.getenv('IAM_SAGEMAKER_ROLE'))

        # deploy sagemaker model
        predictor = model.deploy(
            initial_instance_count=1,
            instance_type=os.getenv('SAGEMAKER_INSTANCE'),
            endpoint_name=self.endpoint_name)

        # prepare a test input
        test_inp = {'instances' : tf.one_hot(np.array([[0,1,1,3,4,5]]),
                                             on_value=1,
                                             off_value=0,
                                             depth=7).numpy() }
        result = predictor.predict(test_inp)
        print(test_inp, result)
        assert result['predictions'][0][0] > 0

        self.next(self.end)

    @step
    def end(self):
        """
        DAG is done!
        """
        print('DAG ended!')


if __name__ == '__main__':
    CartFlow()
