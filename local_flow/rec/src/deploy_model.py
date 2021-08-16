"""

Deploy a tensorflow model onto SageMaker

"""
import os
import time
import shutil
import tarfile
import numpy as np

import tensorflow as tf
from sagemaker.tensorflow import TensorFlowModel
from sagemaker.tensorflow.serving import  Model
from sagemaker.serializers import CSVSerializer
from sagemaker.deserializers import JSONDeserializer

from metaflow import S3

from urllib.parse import urlparse
import sagemaker
from gensim.models import KeyedVectors


def deploy_model(vectors_s3_path: str,
                 model: KeyedVectors,
                 k=10,
                 feature_dim=48,
                 sample_size=65536):
    """
    Entry point for deploy step

    :param model_s3_path: S3 path of model to deploy
    :return: name of endpoint
    """

    # generate a signature for the endpoint using timestamp
    endpoint_name = 'rec-knn-{}-endpoint'.format(int(round(time.time() * 1000)))
    


    # print out the name, so that we can use it when deploying our lambda
    print("\n\n================\nEndpoint name is: {}\n\n".format(endpoint_name))

    parsed = urlparse(vectors_s3_path)
    bucket = parsed.netloc
    prefix = parsed.path.strip('/').split('/')[:-1]
    TARGET_S3_OUTPUT_PATH = u's3://%s' % os.path.join(bucket, *prefix)


    # knn hyper params
    hyperparams = {
        'k': k,
        'index_metric': 'COSINE',
        'feature_dim': feature_dim,
        'sample_size': sample_size,
        'predictor_type': 'classifier'
    }

    # set up the estimator
    knn_model = sagemaker.estimator.Estimator(image_uri='174872318107.dkr.ecr.us-west-2.amazonaws.com/knn:1',
                                            role=os.getenv('IAM_SAGEMAKER_ROLE'),
                                            instance_count=1,
                                            instance_type='ml.m5.large',
                                            output_path=TARGET_S3_OUTPUT_PATH,
                                            sagemaker_session=sagemaker.Session())

    # set hyper params
    knn_model.set_hyperparameters(**hyperparams)

    # setup fit input data
    fit_input = {
        'train': sagemaker.inputs.TrainingInput(
            s3_data=vectors_s3_path,
            content_type='text/csv; label_size=1')
    }

    # fit model
    knn_model.fit(fit_input)

    predictor = knn_model.deploy(initial_instance_count=1,
                                 instance_type=os.getenv('SAGEMAKER_INSTANCE'),
                                 endpoint_name=endpoint_name,
                                 serializer=CSVSerializer(),
                                 deserializer=JSONDeserializer())

    # for debugging w/o re-deployment
    # predictor = sagemaker.Predictor(endpoint_name=endpoint_name,
    #                                 sagemaker_session=sagemaker.Session())
    # predictor.serializer = CSVSerializer()
    # predictor.deserializer = JSONDeserializer()

    # test knn model
    test_key = model.index_to_key[0]
    test_vector = model[test_key]

    gensim_preds = np.array([model.key_to_index[_[0]] for _ in model.similar_by_key(test_key, topn=k+1)])[1:]

    result = predictor.predict(
        test_vector,
        initial_args={"ContentType": "text/csv",
                      "Accept": "application/json; verbose=true"}
    )['predictions'][0]

    print(result)
    result = np.array(result['labels'])[::-1]

    print('SM KNN : {}'.format(result))
    print('GS KNN : {}'.format(gensim_preds))


    print(np.array_equal(gensim_preds, result))



    return endpoint_name
