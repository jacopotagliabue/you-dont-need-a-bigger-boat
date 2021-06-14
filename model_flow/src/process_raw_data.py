import pandas as pd



def process_raw_data(search_train_path, browsing_train_path, sku_to_content_path):

    # process raw_data
    df_search_train = process_search_train(search_train_path)
    df_browsing_train = process_browsing_train(browsing_train_path)
    df_sku_to_content = process_sku_to_content(sku_to_content_path)

    # further processing steps


    # reutrn dict of processed data with name

    return {'browsing_train' : df_browsing_train}

def process_search_train(search_train_path):
    df = pd.read_parquet(search_train_path, engine='pyarrow')
    # peek at raw data
    print(df.dtypes)
    print(df.head(2))
    print('\n')
    return df

def process_browsing_train(search_train_path):
    df = pd.read_parquet(search_train_path, engine='pyarrow')
    # peek at raw data
    print(df.dtypes)
    print(df.head(2))
    print('\n')
    return df

def process_sku_to_content(search_train_path):
    df = pd.read_parquet(search_train_path, engine='pyarrow')
    # peek at raw data
    print(df.dtypes)
    print(df.head(2))
    print('\n')

    return df