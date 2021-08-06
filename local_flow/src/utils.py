import os
import json
from typing import Any


def get_filename(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def return_json_file_content(file_name: str) -> Any:
    """
    Load data from a json file

    :param file_name: name of the file
    :return: the data content extracted from the file
    """
    with open(file_name) as json_file:
        data = json.load(json_file)

    return data
