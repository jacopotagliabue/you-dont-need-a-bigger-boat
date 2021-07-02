
import os

import snowflake.connector
from snowflake.connector import DictCursor


class SFSelfClosingNamespaceConnection:
    """
    A class to connect to a snowflake namespace. This class wraps
    the execute command.

    Implemented to be used with the with keyword.

    Methods
    -------
    execute(command)
        Executes a command on Snowflake.

        Wrapper around cursor.execute.

    execute_many(command, seq_of_parameters)
        Executes a command on Snowflake many times, once with each set of parameters
        in the sequence.

        Wrapper around cursor.execute_many.

    upload_file(absolute_file_path, table)
        Uploads all files matching the absolute_file_path pattern to table.
    """
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
        self._d_cs = self._ctx.cursor(DictCursor)
        self._cs.execute(f"USE WAREHOUSE {self._warehouse}")
        self._cs.execute(f"USE DATABASE {self._database}")
        self._cs.execute(f"CREATE SCHEMA IF NOT EXISTS {self._schema}")
        self._cs.execute(f"USE SCHEMA {self._schema}")
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._cs.close()
        self._d_cs.close()
        self._ctx.close()

    def execute(self, command):
        """

        :param command:
        :return:
        """
        self._cs.execute(command)

    def execute_many(self, command, seq_of_parameters):
        self._cs.executemany(command, seq_of_parameters)

    def upload_file(self, absolute_file_path, table):
        self._cs.execute(f"PUT file://{absolute_file_path} @%{table}")
        self._cs.execute(f"COPY INTO {table} "
                         "FILE_FORMAT = ESCAPED_DQ")

    def dict_get_all(self):
        return self._d_cs.execute('select events from cart_sessions').fetchall()
