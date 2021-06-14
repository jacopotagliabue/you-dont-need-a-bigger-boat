"""

Upload local .csv dataset as .parquet in S3

"""
from dotenv import load_dotenv
load_dotenv('.env')

import os
import pandas as pd
from metaflow.metaflow_config import DATATOOLS_S3ROOT
from src.utils import get_filename



def upload_file_as_parquet(file_path, target_s3_folder, chunksize=None):
    print('Begin reading file {}'.format(file_path))

    s3_file_name = os.path.join(target_s3_folder, get_filename(file_path) + '.parquet')
    if not chunksize is None:
        df_content = next(pd.read_csv(file_path, chunksize=chunksize))
    else:
        df_content = pd.read_csv(file_path)

    print('Begin upload to S3')
    df_content.to_parquet(path=s3_file_name, engine='pyarrow')

    print('Parquet files for {} stored at : {}'.format(file_path, s3_file_name))

if __name__ == '__main__':

    SKU_TO_CONTENT_PATH = os.getenv('SKU_TO_CONTENT_PATH')
    BROWSING_TRAIN_PATH = os.getenv('BROWSING_TRAIN_PATH')
    SEARCH_TRAIN_PATH = os.getenv('SEARCH_TRAIN_PATH')
    PARQUET_S3_PATH = os.getenv('PARQUET_S3_PATH')
    TARGET_S3_PATH = os.path.join(DATATOOLS_S3ROOT,PARQUET_S3_PATH)

    # upload to S3 at some know path under the CartFlow directory
    # for now, upload some rows
    # there is no versioning whatsoever at this stage
    upload_file_as_parquet(SKU_TO_CONTENT_PATH, TARGET_S3_PATH, chunksize=300000)
    upload_file_as_parquet(BROWSING_TRAIN_PATH, TARGET_S3_PATH, chunksize=300000)
    upload_file_as_parquet(SEARCH_TRAIN_PATH, TARGET_S3_PATH, chunksize=3000)
