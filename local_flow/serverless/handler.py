import sys
sys.path.append('packages')

import boto3
import json
import configparser
import time
import os

from uuid import uuid4

import gantry

# link gantry to kinesis stream
gantry.init(logs_location="firehose://gantry-demo-kinesis-stream")


# read config file
config = configparser.ConfigParser()
config.read('settings.ini')
# grab environment variables
SAGEMAKER_ENDPOINT_NAME = os.getenv('SAGEMAKER_ENDPOINT_NAME','intent-1624889175387-endpoint')
# print to AWS for debug!
print(SAGEMAKER_ENDPOINT_NAME)
# instantiate AWS client for invoking sagemaker endpoint
runtime = boto3.client('runtime.sagemaker')


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
    # static "feature store"
    action_map = {
        'start' : [1,0,0,0,0,0,0],
        'end' : [0,1,0,0,0,0,0],
        'add' : [0,0,1,0,0,0,0],
        'remove' : [0,0,0,1,0,0,0],
        'purchase' : [0,0,0,0,1,0,0],
        'detail' : [0,0,0,0,0,1,0],
        'view' : [0,0,0,0,0,0,1],
        'empty' : [0,0,0,0,0,0,0]
    }

    print("Received event: " + json.dumps(event))
    params = event['queryStringParameters']
    response = dict()
    start = time.time()
    session_str = params.get('session','')
    session = session_str.split(',') if session_str != '' else []

    print(session)
    session_id = str(uuid4())
    session = ['start'] + session + ['end']

    session_onehot = [ action_map[_] if _ in action_map else action_map['empty'] for _ in session]
    input_payload = { 'instances': [ session_onehot ] }  # input is array of array, even if we just ask for 1 prediction here
    result = get_response_from_sagemaker(json.dumps(input_payload),
                                         SAGEMAKER_ENDPOINT_NAME,
                                         content_type='application/json')
    if result:
        # print for debugging in AWS Cloudwatch
        print(result)

        # get the first item in the prediction array, as it is a 1-1 prediction
        response = result['predictions'][0][0]
        # log predictions on gantry!
        gantry.log_prediction_event(
            "gantry_local_flow_test",
            inputs={'seq_length': len(session) },
            outputs={"label": response },
            feedback_id={'id': session_id }
        )

    return wrap_response(status_code=200, body={
        "prediction": response,
        "time": time.time() - start,
        "endpoint": SAGEMAKER_ENDPOINT_NAME
    })


if __name__ == '__main__':
    input_payload = { 'instances' : [
                                     [[1, 0, 0, 0, 0, 0, 0],
                                      [0, 0, 0, 0, 1, 0, 0]],
                                     ]
                    }
    result = get_response_from_sagemaker(json.dumps(input_payload),
                                SAGEMAKER_ENDPOINT_NAME,
                                content_type='application/json')
    print(result)
