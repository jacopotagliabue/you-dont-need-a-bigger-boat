import os
import json
import time
import boto3
from typing import Dict, Any, Union, IO

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
    response = runtime.invoke_endpoint(EndpointName=endpoint_name,
                                       ContentType=content_type,
                                       Body=model_input)
    # return the response body, properly decoded
    return json.loads(response['Body'].read().decode())


def preprocess_input(session):
    # add mask
    session = session + ['mask']
    # select N most recent
    session = session[-20:]
    # convert into indices
    session_indices = [ token_mapping['token2id'].get(_, token_mapping['token2id']['[UNK]']) for _ in session ]
    # padding
    session_indices = session_indices + [0]*(20-len(session))

    # debug
    print(session)
    print(session_indices)


    return session_indices


def argsort(seq, reverse=False):
    #http://stackoverflow.com/questions/3382352/equivalent-of-numpy-argsort-in-basic-python/3382369#3382369
    #by unutbu
    return sorted(range(len(seq)), key=seq.__getitem__, reverse=reverse)


def postprocess_response(prediction_input, response):
    mask_token_id = token_mapping['token2id']['mask']
    # masked_index = np.where(prediction_input == mask_token_id)

    masked_index = [ _ for _ in range(len(prediction_input)) if prediction_input[_]== mask_token_id][0]
    mask_prediction = response[masked_index]

    top_indices = argsort(mask_prediction, reverse=True)

    return top_indices[:10]


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

    prediction_input = preprocess_input(session)
    # input is array of array, even if we just ask for 1 prediction here
    input_payload = {'instances': [prediction_input]}
    result = get_response_from_sagemaker(model_input=json.dumps(input_payload),
                                         endpoint_name=SAGEMAKER_ENDPOINT_NAME,
                                         content_type='application/json')
    if result:
        # print for debugging in AWS Cloudwatch
        # print(result)
        # get the first item in the prediction array, as it is a 1-1 prediction
        response = result['predictions'][0]
        response = postprocess_response(prediction_input, response)
        response = [ token_mapping['id2token'][str(_)] for _ in response]
        print(response)

    return wrap_response(200, {
        "prediction":response,
        "time": time.time() - start,
        "endpoint": SAGEMAKER_ENDPOINT_NAME
    })
