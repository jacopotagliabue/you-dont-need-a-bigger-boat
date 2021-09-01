import os
import json
import time
import boto3
from typing import Dict, Any, Union, IO
import random

# grab environment variables
SAGEMAKER_ENDPOINT_NAME = os.getenv('SAGEMAKER_ENDPOINT_NAME')
# print to AWS for debug!
print(SAGEMAKER_ENDPOINT_NAME)
# instantiate AWS client for invoking sagemaker endpoint
runtime = boto3.client('sagemaker-runtime')

TOKEN_MAPPING_PATH = os.getenv('TOKEN_MAPPING_PATH','token_mapping.json')

# load token mapping
with open(TOKEN_MAPPING_PATH) as f:
    token_mapping = json.load(f)

token2id = token_mapping['token2id']
id2token = token_mapping['id2token']
VOCAB_SIZE = len(token2id)

def argsort(seq):
    #http://stackoverflow.com/questions/3382352/equivalent-of-numpy-argsort-in-basic-python/3382369#3382369
    #by unutbu
    return sorted(range(len(seq)), key=seq.__getitem__)

def wrap_response(status_code: int,
                  body: Dict[Any, Any]) -> Dict[str, Any]:
    """
    Small function to wrap the model response in an actual API response (status, body, headers).

    :param status_code: http status code
    :param body: dictionary containing model predictions
    :return:
    """
    return {
        'isBase64Encoded': False,
        'statusCode': status_code,
        'headers': {
            # this makes the function callable across domains!
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body),
    }


def get_response_from_sagemaker(model_input: str,
                                endpoint_name: str,
                                content_type: str = 'application/json'):
    """
    Function

    :param model_input: JSON dump of model input params
    :param endpoint_name: name of sagemaker endpoint
    :param content_type: content format, default to application/json
    :return:
    """
    # get raw response from sagemaker
    print(model_input)
    response = runtime.invoke_endpoint(EndpointName=endpoint_name,
                                       ContentType=content_type,
                                       Body=model_input)
    # return the response body, properly decoded
    return json.loads(response['Body'].read().decode())


def predict(event: Dict[str, Any],
            context: Any) -> Dict[str, Any]:
    """
    AWS lambda function, to handle incoming GET requests asking our model for predictions.

    :param event: standard AWS lambda event param - it contains the query parameters for the GET call
    :param context: standard AWS lambda context param - not use in this application
    :return:
    """

    print("Received event: " + json.dumps(event))
    params = event.get('queryStringParameters', {})
    response = dict()
    start = time.time()
    session_str = params.get('session', '')
    session = session_str.split(',') if session_str != '' else []

    print(session)

    # get UNK index if exist else random select from vocab
    UNK = token2id.get('[UNK]', random.randint(0,VOCAB_SIZE))
    # get mask index if exist else None, used by ProdB
    MASK = token2id.get('mask', None)
    # convert session sku to ids
    session_indices = [token2id.get(_, UNK) for _ in session]
    input_payload = {'instances': session_indices, 'mask': MASK}

    print(input_payload)
    result = get_response_from_sagemaker(model_input=json.dumps(input_payload),
                                         endpoint_name=SAGEMAKER_ENDPOINT_NAME,
                                         content_type='application/json')
    print(len(result))

    if result:
        response = result['predictions'][0]
        sorted_indices = argsort(response)
        sku_predictions = [token_mapping['id2token'][str(_)] for _ in sorted_indices]
        print(sku_predictions[:10])

    return wrap_response(200, {
        "prediction":sku_predictions[:10],
        "time": time.time() - start,
        "endpoint": SAGEMAKER_ENDPOINT_NAME
    })
