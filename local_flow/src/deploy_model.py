import os
import time
import shutil
import tarfile
import numpy as np
import tensorflow as tf
from sagemaker.tensorflow import TensorFlowModel

def tf_model_to_tar(run_id:int, tf_model):

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

def deploy_model(model_s3_path: str):

  # generate a signature for the endpoint using timestamp
  endpoint_name = 'intent-{}-endpoint'.format(int(round(time.time() * 1000)))

  # print out the name, so that we can use it when deploying our lambda
  print("\n\n================\nEndpoint name is: {}\n\n".format(endpoint_name))

  # create sagemaker tf model
  model = TensorFlowModel(
    model_data=model_s3_path,
    image_uri=os.getenv('DOCKER_IMAGE'),
    role=os.getenv('IAM_SAGEMAKER_ROLE'))

  # deploy sagemaker model
  predictor = model.deploy(
    initial_instance_count=1,
    instance_type=os.getenv('SAGEMAKER_INSTANCE'),
    endpoint_name=endpoint_name)

  # prepare a test input and check response
  test_inp = {'instances': tf.one_hot(np.array([[0, 1, 1, 3, 4, 5]]),
                                      on_value=1,
                                      off_value=0,
                                      depth=7).numpy()}
  result = predictor.predict(test_inp)
  print(test_inp, result)
  assert result['predictions'][0][0] > 0

  return endpoint_name
