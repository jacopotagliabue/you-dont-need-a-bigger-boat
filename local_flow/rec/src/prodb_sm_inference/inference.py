import json


def input_handler(data, context):
    # read input data
    data_str = data.read().decode("utf-8")
    jsonlines = data_str.split("\n")
    session = json.loads(jsonlines[0])["instances"][0]
    mask_id = json.loads(jsonlines[0])["mask"]

    # add mask
    session = session + [mask_id]
    # select N most recent
    session = session[-20:]
    # padding
    session = session + [0]*(20-len(session))

    # select most-recent for kNN model for prediction
    return json.dumps({'instances':[session]})

def output_handler(response, context):

    response_dict = response.json()
    predictions = response_dict['predictions'][0]

    response_content_type = context.accept_header
    return json.dumps({'predictions':[predictions]}), response_content_type
    # return json.dumps(response.json()), response_content_type
