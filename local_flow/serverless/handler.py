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


def wrap_response(status_code: int,
                  body: Dict[Any, Any]) -> Dict[str, Any]:
    """
    Small function to wrap the model response in an actual API response (status, body, headers).

    :param status_code: http status code
    :param body: dictionary containing model predictions
    :return:
    """
    return {
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


def predict(event: Dict[str, Any],
            context: Any) -> Dict[str, Any]:
    """
    AWS lambda function, to handle incoming GET requests asking our model for predictions.

    :param event: standard AWS lambda event param - it contains the query parameters for the GET call
    :param context: standard AWS lambda context param - not use in this application
    :return:
    """
    # static "feature store"
    action_map = {
        'start': [1, 0, 0, 0, 0, 0, 0],
        'end': [0, 1, 0, 0, 0, 0, 0],
        'add': [0, 0, 1, 0, 0, 0, 0],
        'remove': [0, 0, 0, 1, 0, 0, 0],
        'purchase': [0, 0, 0, 0, 1, 0, 0],
        'detail': [0, 0, 0, 0, 0, 1, 0],
        'view': [0, 0, 0, 0, 0, 0, 1],
        'empty': [0, 0, 0, 0, 0, 0, 0]
    }

    print("Received event: " + json.dumps(event))
    params = event.get('queryStringParameters', {})
    response = dict()
    start = time.time()
    session_str = params.get('session', '')
    session = session_str.split(',') if session_str != '' else []

    print(session)

    session = ['start'] + session + ['end']

    session_onehot = [
        action_map[_] if _ in action_map else action_map['empty']
        for _ in session
    ]
    # input is array of array, even if we just ask for 1 prediction here
    input_payload = {'instances': [session_onehot]}
    result = get_response_from_sagemaker(model_input=json.dumps(input_payload),
                                         endpoint_name=SAGEMAKER_ENDPOINT_NAME,
                                         content_type='application/json')
    if result:
        # print for debugging in AWS Cloudwatch
        print(result)
        # get the first item in the prediction array, as it is a 1-1 prediction
        response = result['predictions'][0][0]

    return wrap_response(200, {
        "prediction": response,
        "time": time.time() - start,
        "endpoint": SAGEMAKER_ENDPOINT_NAME
    })


if __name__ == '__main__':
    input_payload = {
        'instances': [
            [
                [1, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 1, 0, 0]
            ],
        ]
    }
    result = get_response_from_sagemaker(model_input=json.dumps(input_payload),
                                         endpoint_name=SAGEMAKER_ENDPOINT_NAME,
                                         content_type='application/json')
    print(result)
