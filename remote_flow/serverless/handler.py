import boto3
import json
import configparser
import time
import os

# read config file
config = configparser.ConfigParser()
config.read('settings.ini')
# grab environment variables
SAGEMAKER_ENDPOINT_NAME = config['sagemaker']['SAGEMAKER_ENDPOINT_NAME']
# print to AWS for debug!
print(SAGEMAKER_ENDPOINT_NAME)
# instantiate AWS client for invoking sagemaker endpoint
runtime = boto3.client('runtime.sagemaker',
                       aws_access_key_id=config['sagemaker']['SAGE_USER'],
                       aws_secret_access_key=config['sagemaker']['SAGE_SECRET'],
                       region_name=config['sagemaker'].get('SAGE_REGION', 'us-west-2')
                       )


def encode_input(request_session):
    """
    Helper function to map the input terms to their one hot encoding.
    :param request_session: string representation of a list of events
    :return: Array of 1-hot encoding vectors (as lists)
    """
    one_hot_encoding = {
        'start': [1, 0, 0, 0, 0, 0, 0],
        'end': [0, 1, 0, 0, 0, 0, 0],
        'add': [0, 0, 1, 0, 0, 0, 0],
        'remove': [0, 0, 0, 1, 0, 0, 0],
        'purchase': [0, 0, 0, 0, 1, 0, 0],
        'detail': [0, 0, 0, 0, 0, 1, 0],
        'view': [0, 0, 0, 0, 0, 0, 1],
        'empty': [0, 0, 0, 0, 0, 0, 0]
    }
    return [one_hot_encoding.get(action.strip(), 'empty') for action in request_session.split(',')]


def wrap_response(status_code: int, body: dict):
    """
    Small function to wrap the model response in an actual API response (status, body, headers).

    :param status_code: http status code
    :param body: dictionary containing model predictions
    :return:
    """
    return {
        'statusCode': status_code,
        'body': json.dumps(body),
        'headers': {
            'Access-Control-Allow-Origin': '*'  # this makes the function callable across domains!
        }
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


def predict(event, context):
    """
    AWS lambda function, to handle incoming GET requests asking our model for predictions.

    :param event: standard AWS lambda event param - it contains the query parameters for the GET call
    :param context: standard AWS lambda context param - not use in this application
    :return:
    """
    print("Received event: " + json.dumps(event))
    params = event['queryStringParameters']
    response = dict()
    start = time.time()

    input_payload = {'instances': [encode_input(params.get('x', 'empty'))]}  # input is array of array, even if we just ask for 1 prediction here
    result = get_response_from_sagemaker(json.dumps(input_payload),
                                         SAGEMAKER_ENDPOINT_NAME,
                                         content_type='application/json')
    if result:
        # print for debugging in AWS Cloudwatch
        print(result)
        response = result['predictions']

    return wrap_response(status_code=200, body={
        "prediction": response,
        "time": time.time() - start,
        "endpoint": SAGEMAKER_ENDPOINT_NAME
    })
