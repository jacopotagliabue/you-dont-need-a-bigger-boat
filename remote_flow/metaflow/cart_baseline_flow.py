"""

    Baseline implemented using Metaflow

"""

# Load env variables
import tarfile
import time

try:
    from dotenv import load_dotenv
    load_dotenv('.env')
except Exception as e:
    print(e)

import os
from metaflow import FlowSpec, step, batch, current, environment, Parameter, S3
from custom_decorators import pip, enable_decorator

class CartFlow(FlowSpec):
    """
    CartFlow is a DAG that, given a shopping session with an add-to-cart as input, predicts
    whether or not the session is going to end with a purchase. The flow starts by reading data prepared by
    dbt in Snowflake, and leverage GPUs for training and SageMaker for serving.

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
    def start(self):
        """
        Start Step for a Flow;
        """
        print("flow name: %s" % current.flow_name)
        print("run id: %s" % current.run_id)
        print("username: %s" % current.username)

        # Call next step in DAG with self.next(...)
        self.next(self.prepare_dataset)

    @step
    def prepare_dataset(self):
        """
        Read in raw session data and build a labelled dataset for purchase/abandonment prediction
        """
        from prepare_dataset import prepare_dataset

        self.dataset = prepare_dataset()

        self.next(self.get_model_config)

    @step
    def get_model_config(self):
        '''
        Get model hyper-params;
        It is possible in this step perform a for-each to parallel run over a range of hyper params;
        '''
        from utils import return_json_file_content

        # read just a single configuration
        self.config = return_json_file_content(os.getenv('MODEL_CONFIG_PATH'))
        self.next(self.train_model)


    # @batch decorator used to run step on AWS Batch
    # wrap batch in a switch to allow easy local testing
    @enable_decorator(batch(gpu=1, cpu=8, image=os.getenv('BASE_IMAGE')),
                     flag=int(os.getenv('EN_BATCH')))
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
        Train a regression model on the random dataset, on GPU.
        """
        import wandb
        from model import train_lstm_model
        import tensorflow as tf
        from tensorflow.keras.preprocessing.sequence import pad_sequences
        # from gantry.summarize import SummarizationContext
        # import gantry.sdk as gantry_sdk

        assert os.getenv('WANDB_API_KEY')
        assert os.getenv('WANDB_ENTITY')
        assert os.getenv('WANDB_PROJECT')

        wandb.init(entity=os.getenv('WANDB_ENTITY'),
                   project=os.getenv('WANDB_PROJECT'),
                   id=current.run_id,
                   config=self.config,
                   resume='allow',
                   reinit=True)

        self.model, self.model_weights, x_model = train_lstm_model(x=self.dataset['X'],
                                                          y=self.dataset['y'],
                                                          epochs=self.config['EPOCHS'],
                                                          patience=self.config['PATIENCE'],
                                                          lstm_dim=self.config['LSTM_DIMS'],
                                                          batch_size=self.config['BATCH_SIZE'],
                                                          lr=self.config['LEARNING_RATE'])

        model_name = "metaflow-intent-prediction-remote-model-{}/1-{}".format(self.config['LEARNING_RATE'], time.time())
        local_tar_name = 'model-{}.tar.gz'.format(self.config['LEARNING_RATE'])
        x_model.save(filepath=model_name)
        max_len = max(len(_) for _ in self.dataset['X'][0:1000])
        X_train = pad_sequences(self.dataset['X'][0:1000], padding="post", value=7, maxlen=max_len)
        self.X = tf.one_hot(X_train, depth=7)
        self.y = x_model.predict(self.X, batch_size=self.config['BATCH_SIZE'])
        # zip keras folder to a single tar file
        with tarfile.open(local_tar_name, mode="w:gz") as _tar:
            _tar.add(model_name, recursive=True)
        # metaflow nice s3 client needs a byte object for the put
        # IMPORTANT: if you're using the metaflow local setup,
        # you have to upload the model to S3 for
        # sagemaker using custom code - replace the metaflow client here with a standard
        # boto call and a target bucket over which you have writing permissions
        # remember to store in self.s3_path the final full path of the model tar file, to be used
        # downstream by sagemaker!
        with open(local_tar_name, "rb") as in_file:
            data = in_file.read()
            with S3(run=self) as s3:
                url = s3.put(local_tar_name, data)
                # print it out for debug purposes
                print("Model saved at: {}".format(url))
                # save this path for downstream reference!
                self.s3_path = url

        self.next(self.deploy)

    # @step
    # def send_to_gantry(self):
    #     from gantry.summarize import SummarizationContext
    #     import gantry.sdk as gantry_sdk
    #
    #     gantry_sdk.init()
    #
    #     with SummarizationContext("loan_pred") as ctx:
    #         ctx.register(inputs=self.dataset['X'], outputs=self.predictions)
    #         gantry_sdk.set_reference(ctx)
    #
    #     self.next(self.deploy)

    @step
    def deploy(self):
        """
        Use SageMaker to deploy the model as a stand-alone, PaaS endpoint, with our choice of the underlying
        Docker image and hardware capabilities.
        Available images for inferences can be chosen from AWS official list:
        https://github.com/aws/deep-learning-containers/blob/master/available_images.md
        Once the endpoint is deployed, you can add a further step with for example behavioral testing, to
        ensure model robustness (e.g. see https://arxiv.org/pdf/2005.04118.pdf). Here, we just "prove" that
        the endpoint is up and running!
        """
        from sagemaker.tensorflow import TensorFlowModel
        from sagemaker.session import Session
        from model import make_predictions
        import boto3


        # The default sagemaker role does not seem to have the required permission to list tags which is needed
        # to update the endpoint.
        boto_session = boto3.session.Session(region_name=os.getenv('SAGE_REGION', 'us-west-2'),
                                                  aws_access_key_id=os.getenv('SAGE_USER'),
                                                  aws_secret_access_key=os.getenv('SAGE_SECRET'))

        sagemaker_client = boto_session.client('sagemaker')

        sagemaker_session = Session(boto_session)

        # generate a signature for the endpoint, using learning rate and timestamp as a convention
        self.endpoint_name = os.getenv('SAGEMAKER_ENDPOINT_NAME', 'metaflow-intent-remote-endpoint')
        # print out the name, so that we can use it when deploying our lambda
        print("\n\n================\nEndpoint name is: {}\n\n".format(self.endpoint_name))
        model = TensorFlowModel(
            model_data=self.s3_path,
            image_uri=self.DOCKER_IMAGE_URI,
            role=self.IAM_SAGEMAKER_ROLE)
        # #check if the endpoint already exists
        if sagemaker_client.list_endpoints(NameContains='metaflow-intent-remote-endpoint').get('Endpoints', []):
            predictor = model.predictor_cls(self.endpoint_name, sagemaker_session)
            predictor.update_endpoint()
        else:
            predictor = model.deploy(initial_instance_count=1,
                instance_type=self.SAGEMAKER_INSTANCE,
                endpoint_name=self.endpoint_name)


        self.endpoint_prediction = make_predictions(predictor)
        assert self.endpoint_prediction
        print('First prediction')
        print(self.endpoint_prediction)
        self.next(self.end)

    @step
    def end(self):
        """
        DAG is done!
        """
        print('DAG ended!')


if __name__ == '__main__':
    CartFlow()
