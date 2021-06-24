import csv
import os


from connectors.sf_connector import SFSelfClosingNamespaceConnection
from data_loaders.sigir_data_loader import SigirBatchedGenerator
from data_models.tables import browsing_train_table, sku_to_content_table, search_train_table
from wrangle.wranglers import sku_wrangler, browsing_wrangler, search_wrangler

#load env
try:
    from dotenv import load_dotenv
    load_dotenv('.env')
except Exception as e:
    print(e)


def write_chunks(table, filepath, conn, batch_size, max_batches=float('inf'), value_parser=lambda x: x):
    """
    Main function to read in csv files in batch and upload the content to snowflake after
    "unprocessing" the data. This method will create a temporary folder and store the "unprocessed"
    documents in csv format in order to then use SNowflakes csv upload capability.

    :param table: name of the table to upload to
    :param filepath: path to the source csv files
    :param conn: configured SFSelfClosingNamespaceConnection
    :param batch_size: number of lines per read batch (this is to manage memory usage)
    :param max_batches: max number of batches to process in a file (defaults to processing all)
    :param value_parser: Logic (wrangler) to "unprocess" data. (default: identity transformation)
    :return: None
    """

    import tempfile
    fieldnames = [name for name, _ in table['columns']]
    columns = ", ".join([f"{name} {datatype}" for name, datatype in table['columns']])
    table_name = table['name']
    with tempfile.TemporaryDirectory() as tmpdirname:
        output_prefix = f"{tmpdirname}/batch"
        with SigirBatchedGenerator(filepath) as data:
            for i, batch in enumerate(data.get_batches(batch_size)):
                if i >= max_batches:
                    break
                output_file = f"{output_prefix}{i}.csv"
                with open(output_file, 'w') as file:
                    print("writing", output_file)
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    values = []
                    for b in batch:
                        v = value_parser(b)
                        if isinstance(v, list):
                            values.extend(v)
                        elif isinstance(v, dict):
                            values.append(v)
                    writer.writerows(values)
        create_string = (
            f"CREATE OR REPLACE TABLE {table_name}("
            f"{columns})"
        )
        conn.execute(create_string)
        conn.upload_file(f"{output_prefix}*", table_name)


if __name__ == "__main__":
    # load env vars
    data_path = os.getenv("LOCAL_DATA_PATH")
    config_batch_size = int(os.getenv("BATCH_SIZE"))
    config_max_batches = float(os.getenv("MAX_BATCHES", 'inf'))
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
    database = os.getenv("SNOWFLAKE_DB")
    schema = os.getenv("SNOWFLAKE_SCHEMA")

    browsing_train = f"{data_path}/browsing_train.csv"
    search_train = f"{data_path}/search_train.csv"
    sku_to_content = f"{data_path}/sku_to_content.csv"

    # upload all files
    with SFSelfClosingNamespaceConnection(warehouse, database, schema) as sf_con:
        print(sku_to_content)  # print filepath for sanity check
        write_chunks(table=sku_to_content_table,
                     filepath=sku_to_content,
                     conn=sf_con,
                     batch_size=config_batch_size,
                     max_batches=config_max_batches,
                     value_parser=sku_wrangler)
        print(search_train)
        write_chunks(table=search_train_table,
                     filepath=search_train,
                     conn=sf_con,
                     batch_size=config_batch_size,
                     max_batches=config_max_batches,
                     value_parser=search_wrangler)
        print(browsing_train)
        write_chunks(table=browsing_train_table,
                     filepath=browsing_train,
                     conn=sf_con,
                     batch_size=config_batch_size,
                     max_batches=config_max_batches,
                     value_parser=browsing_wrangler)
