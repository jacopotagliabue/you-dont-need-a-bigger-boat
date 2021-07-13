import pandas as pd
import cudf



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
    df = pd.read_parquet(search_train_path, engine='pyarrow')
    print(df.shape)
    df = cudf.DataFrame.from_pandas(df)
    # peek at raw data
    print(df.dtypes)
    print(df.head(2))
    print('\n')
    return df.to_pandas()

def process_browsing_train(browsing_train_path):
    print('Processing {}'.format(browsing_train_path))

    # 30M seems to exceed some memory limit; take 1M rows for now
    df = pd.read_parquet(browsing_train_path, engine='pyarrow').head(1000000)

    # select important columns only
    df = df[['session_id_hash', 'event_type', 'product_action', 'server_timestamp_epoch_ms']]
    df['product_action'].fillna(value='',inplace=True)
    print(df.shape)
    df = cudf.DataFrame.from_pandas(df)

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

    return df.to_pandas()

def process_sku_to_content(sku_to_content_path):
    print('Processing {}'.format(sku_to_content_path))
    df = pd.read_parquet(sku_to_content_path, engine='pyarrow')
    df = cudf.DataFrame.from_pandas(df)

    # peek at raw data
    print(df.dtypes)
    print(df.head(2))
    print('\n')

    return df.to_pandas()