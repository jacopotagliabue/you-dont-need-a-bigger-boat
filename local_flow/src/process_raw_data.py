# Try import cudf for GPU enabled (Batch) processing
try:
    import cudf
    CUDF_AVAIL = True
except Exception as e:
    print(e)
    CUDF_AVAIL = False

import pandas as pd


def read_from_parquet(path, limit=None):
    df = pd.read_parquet(path, engine='pyarrow')
    print(df.shape)
    if CUDF_AVAIL:
        if limit:
            df = df.head(limit)
        df = cudf.DataFrame.from_pandas(df)
    return df

def return_df(df):
    if CUDF_AVAIL:
        df = df.to_pandas()
    return df


def process_raw_data(search_train_path, browsing_train_path, sku_to_content_path):
    """
    Entry point for data transformation with rapids/pandas

    :param search_train_path:
    :param browsing_train_path:
    :param sku_to_content_path:
    :return:
    """
    # process raw_data
    df_search_train = process_search_train(search_train_path)
    df_browsing_train = process_browsing_train(browsing_train_path)
    df_sku_to_content = process_sku_to_content(sku_to_content_path)

    # reutrn dict of processed data with name, only browsing_train for now
    return {'browsing_train' : df_browsing_train}

def process_search_train(search_train_path):
    print('Processing {}'.format(search_train_path))
    df = read_from_parquet(search_train_path)
    # peek at raw data
    print(df.dtypes)
    print(df.head(2))
    print('\n')
    return return_df(df)

def process_browsing_train(browsing_train_path):
    print('Processing {}'.format(browsing_train_path))

    # 30M seems to exceed some memory limit; take 1M rows for now
    df = read_from_parquet(browsing_train_path, limit=1000000)
    # select important columns only
    df = df[['session_id_hash', 'event_type', 'product_action', 'server_timestamp_epoch_ms']]
    df['product_action'].fillna(value='',inplace=True)
    print(df.shape)

    # peek at raw data
    print(df.dtypes)
    print(df.head(2))
    print('\n')

    # sort according to session_id_hash and timestamp
    df = df.sort_values(by=['session_id_hash', 'server_timestamp_epoch_ms'])
    df = df.reset_index(drop=True)

    # check sorting
    print(df[['session_id_hash','server_timestamp_epoch_ms']].head(10))
    print('\n')

    return return_df(df)

def process_sku_to_content(sku_to_content_path):
    print('Processing {}'.format(sku_to_content_path))
    df = read_from_parquet(sku_to_content_path)

    # peek at raw data
    print(df.dtypes)
    print(df.head(2))
    print('\n')

    return return_df(df)
