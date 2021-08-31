"""

Deploy a tensorflow model onto SageMaker

"""
import os
import time
import shutil
import tarfile
import numpy as np

from tensorflow.keras import Model
from tensorflow.keras.models import model_from_json

from sagemaker.tensorflow import TensorFlowModel


def tf_model_to_tar(tf_model: Model, run_id: int, ):
    """
    Saves tensorflow model as compressed file

    :param run_id: current Metaflow run id
    :param tf_model: tensorflow model
    :return:
    """

    model_name = "intent-model-{}/1".format(run_id)
    local_tar_name = 'model-{}.tar.gz'.format(run_id)

    # save model locally
    tf_model.save(filepath=model_name)
    # save model as .tar.gz
    with tarfile.open(local_tar_name, mode="w:gz") as _tar:
        _tar.add(model_name, recursive=True)
    # remove local model
    shutil.rmtree(model_name.split('/')[0])

    return local_tar_name


def deploy_tf_model(model, s3, run_id):



    # load model from json and weights
    tf_model = model_from_json(model['model'],custom_objects=model.get('custom_objects', None))
    tf_model.set_weights(model['weights'])

    # save model as .tar.gz onto S3 for SageMaker
    local_tar_name = tf_model_to_tar(tf_model, run_id)

    # save model to S3
    with open(local_tar_name, "rb") as in_file:
        data = in_file.read()
        url = s3.put(local_tar_name, data)
        # print it out for debug purposes
        print("Model saved at: {}".format(url))
        # save this path for downstream reference!
        model_s3_path = url
        # remove local compressed model
        os.remove(local_tar_name)


    # generate a signature for the endpoint using timestamp
    endpoint_name = 'intent-{}-endpoint'.format(int(round(time.time() * 1000)))

    # print out the name, so that we can use it when deploying our lambda
    print("\n\n================\nEndpoint name is: {}\n\n".format(endpoint_name))

    # create sagemaker tf model
    model = TensorFlowModel(
        model_data=model_s3_path,
        image_uri=os.getenv('DOCKER_IMAGE'),
        role=os.getenv('IAM_SAGEMAKER_ROLE'),
        entry_point='src/knn_sm_inference/inference.py')

    # deploy sagemaker model
    predictor = model.deploy(
        initial_instance_count=1,
        instance_type=os.getenv('SAGEMAKER_INSTANCE'),
        endpoint_name=endpoint_name)

    # prepare a test input and check response
    test_inp = {'instances': np.array([[1,2,3,4,5]+[0]*15])}

    result = predictor.predict(test_inp)

    # print(test_inp, result)
    # assert result['predictions'][0][0] > 0

    assert result['predictions']

    return model_s3_path, endpoint_name

