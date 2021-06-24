import json

def return_json_file_content(file_name: str):
    """
    Load data from a json file

    :param file_name: name of the file
    :return: the data content extracted from the file
    """
    with open(file_name) as json_file:
        data = json.load(json_file)

    return data