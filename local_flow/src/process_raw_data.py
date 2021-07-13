"""

Utilize RAPIDS/cudf to transform and clean raw data

"""
import pandas as pd
import cudf


def process_raw_data(search_train_path: str, browsing_train_path: str, sku_to_content_path: str):
    """
    Entry point for data transformation with rapids/pandas

    :param search_train_path: path to search_train data
    :param browsing_train_path: path to browsing_train data
    :param sku_to_content_path: path to sku_to_content data
    :return: processed data as dict of Dataframes
    """
    # process raw_data
    df_search_train = process_search_train(search_train_path)
    df_browsing_train = process_browsing_train(browsing_train_path)
    df_sku_to_content = process_sku_to_content(sku_to_content_path)

    # reutrn dict of processed data with name, only browsing_train for now
    return {'browsing_train': df_browsing_train}

def process_search_train(search_train_path: str):
    """
    Processing of search_train data

    :param search_train_path: path to search_train data
    :return:
    """
    print('Processing {}'.format(search_train_path))
    df = pd.read_parquet(search_train_path, engine='pyarrow')
    print(df.shape)
    df = cudf.DataFrame.from_pandas(df)
    # peek at raw data
    print(df.dtypes)
    print(df.head(2))
    print('\n')

    # convert back to pandas
    return df.to_pandas()


def process_browsing_train(browsing_train_path: str):
    """
    Processing of browsing_train data

    :param browsing_train_path: path to browsing_train data
    :return:
    """
    print('Processing {}'.format(browsing_train_path))

    # 30M seems to exceed some memory limit; take 1M rows for now
    df = pd.read_parquet(browsing_train_path, engine='pyarrow').head(1000000)

    # select important columns only
    df = df[['session_id_hash', 'event_type', 'product_action', 'server_timestamp_epoch_ms']]
    df['product_action'].fillna(value='', inplace=True)
    print(df.shape)
    df = cudf.DataFrame.from_pandas(df)

    # peek at raw data
    print(df.dtypes)
    print(df.head(2))
    print('\n')

    # sort according to session_id_hash and timestamp
    df = df.sort_values(by=['session_id_hash', 'server_timestamp_epoch_ms'])
    df = df.reset_index(drop=True)

    # print first 15 events to debug sorting
    print(df[['session_id_hash', 'server_timestamp_epoch_ms']].head(15))
    print('\n')

    # convert back to pandas
    return df.to_pandas()


def process_sku_to_content(sku_to_content_path: str):
    """
    Processing of sku_to_content data

    :param sku_to_content_path: path to sku_to_content data
    :return:
    """
    print('Processing {}'.format(sku_to_content_path))
    df = pd.read_parquet(sku_to_content_path, engine='pyarrow')
    df = cudf.DataFrame.from_pandas(df)

    # peek at raw data
    print(df.dtypes)
    print(df.head(2))
    print('\n')

    # convert back to pandas
    return df.to_pandas()
