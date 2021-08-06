"""

Upload local .csv dataset as .parquet in S3

"""
# Load env variables
try:
    from dotenv import load_dotenv
    load_dotenv('.env')
except Exception as e:
    print(e)

import os
from typing import Optional, List

import pandas as pd
from metaflow.metaflow_config import DATATOOLS_S3ROOT

from src.utils import get_filename


def upload_file_as_parquet(file_path: str,
                           target_s3_folder: str,
                           chunksize: Optional[int] = None,
                           partition_cols: Optional[List[str]] = None) -> None:
    print('Begin reading file {}'.format(file_path))

    s3_file_name = os.path.join(
        target_s3_folder, get_filename(file_path) + '.parquet')
    if not chunksize is None:
        df_content = next(pd.read_csv(file_path, chunksize=chunksize))
    else:
        df_content = pd.read_csv(file_path)

    print('Begin upload to S3')
    df_content.to_parquet(path=s3_file_name,
                          engine='pyarrow',
                          partition_cols=partition_cols)

    print('Parquet files for {} stored at : {}'.format(file_path, s3_file_name))


if __name__ == '__main__':
    PARQUET_S3_PATH = os.environ['PARQUET_S3_PATH']
    LOCAL_DATA_PATH = os.environ['LOCAL_DATA_PATH']
    SKU_TO_CONTENT_PATH = os.path.join(LOCAL_DATA_PATH, 'sku_to_content.csv')
    BROWSING_TRAIN_PATH = os.path.join(LOCAL_DATA_PATH, 'browsing_train.csv')
    SEARCH_TRAIN_PATH = os.path.join(LOCAL_DATA_PATH, 'search_train.csv')
    TARGET_S3_PATH = os.path.join(DATATOOLS_S3ROOT, PARQUET_S3_PATH)

    # upload to S3 at some know path under the CartFlow directory
    # for now, upload some rows
    # there is no versioning whatsoever at this stage
    upload_file_as_parquet(SKU_TO_CONTENT_PATH, TARGET_S3_PATH)
    upload_file_as_parquet(BROWSING_TRAIN_PATH, TARGET_S3_PATH)
    upload_file_as_parquet(SEARCH_TRAIN_PATH, TARGET_S3_PATH)
