import os
import json
from typing import Any, Optional


def get_filename(path: str, ext: Optional[str] = None) -> str:
    file_name = os.path.splitext(os.path.basename(path))[0]
    return f"{file_name}.{ext}" if ext else file_name


def return_json_file_content(file_name: str) -> Any:
    """
    Load data from a json file

    :param file_name: name of the file
    :return: the data content extracted from the file
    """
    with open(file_name) as json_file:
        data = json.load(json_file)

    return data
