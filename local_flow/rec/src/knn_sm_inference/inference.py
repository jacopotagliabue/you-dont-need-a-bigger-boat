import json


def input_handler(data, context):
    # read input data
    data_str = data.read().decode("utf-8")
    jsonlines = data_str.split("\n")
    session = json.loads(jsonlines[0])["instances"]
    # select most-recent for kNN model for prediction
    return json.dumps({'instances':[session[-1]]})

def output_handler(response, context):
    # pass through
    response_content_type = context.accept_header
    return json.dumps(response.json()), response_content_type
