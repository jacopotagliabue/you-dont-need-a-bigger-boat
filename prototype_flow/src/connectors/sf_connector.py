
import os

import snowflake.connector

from data_loaders.sigir_data_loader import SigirBatchedGenerator


class SFSelfClosingNamespaceConnection:
    def __init__(self, warehouse, database, schema):
        self._ctx = None
        self._cs = None
        self._warehouse = warehouse
        self._database = database
        self._schema = schema

    def __enter__(self):
        if not self._warehouse:
            raise ValueError("Warehouse is either None or empty please specify name.")
        if not self._database:
            raise ValueError("Database is either None or empty please specify name.")
        if not self._schema:
            raise ValueError("Schema is either None or empty please specify name.")

        self._ctx = snowflake.connector.connect(
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PWD'),
            account=os.getenv('SNOWFLAKE_ACCOUNT')
        )
        self._cs = self._ctx.cursor()
        self._cs.execute(f"USE WAREHOUSE {self._warehouse}")
        self._cs.execute(f"USE DATABASE {self._database}")
        self._cs.execute(f"CREATE SCHEMA IF NOT EXISTS {self._schema}")
        self._cs.execute(f"USE SCHEMA {self._schema}")
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._cs.close()
        self._ctx.close()

    def execute(self, command):
        self._cs.execute(command)

    def execute_many(self, command, seq_of_parameters):
        self._cs.executemany(command, seq_of_parameters)

    def upload_file(self, absolute_file_path, table):
        self._cs.execute(f"PUT file://{absolute_file_path} @%{table}")
        self._cs.execute(f"COPY INTO {table} "
                         "FILE_FORMAT = ESCAPED_DQ")
