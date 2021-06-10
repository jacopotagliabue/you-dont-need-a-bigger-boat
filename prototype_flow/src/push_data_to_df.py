import csv
import os


from connectors.sf_connector import SFSelfClosingNamespaceConnection
from data_loaders.sigir_data_loader import SigirBatchedGenerator
from data_models.tables import browsing_train_table, sku_to_content_table, search_train_table
from wrangle.wranglers import sku_wrangler, browsing_wrangler, search_wrangler

try:
    from dotenv import load_dotenv
    load_dotenv('.env')
except Exception as e:
    print(e)


def write_chunks(table, filepath, conn, value_parser=lambda x: x):
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
    data_path = os.getenv("LOCAL_DATA_PATH")
    batch_size = int(os.getenv("BATCH_SIZE"))
    max_batches = float(os.getenv("MAX_BATCHES", 'inf'))
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
    database = os.getenv("SNOWFLAKE_DB")
    schema = os.getenv("SNOWFLAKE_SCHEMA")

    browsing_train = f"{data_path}/browsing_train.csv"
    search_train = f"{data_path}/search_train.csv"
    sku_to_content = f"{data_path}/sku_to_content.csv"

    with SFSelfClosingNamespaceConnection(warehouse, database, schema) as sf_con:
        print(sku_to_content)
        write_chunks(table=sku_to_content_table, filepath=sku_to_content, conn=sf_con, value_parser=sku_wrangler)
        print(search_train)
        write_chunks(table=search_train_table, filepath=search_train, conn=sf_con, value_parser=search_wrangler)
        # print(browsing_train)
        # write_chunks(table=browsing_train_table, filepath=browsing_train, conn=sf_con, value_parser=browsing_wrangler)



