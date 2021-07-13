"""
Perform
"""

import sys
import pandas as pd
import great_expectations as ge
from datetime import datetime

# add great_expectations/plugins to path
sys.path.append('great_expectations')
from plugins.custom_expectation import ExpectAverageSessionLengthToBeBetween


def validate_data(run_id: int, flow_name: str, data_paths: dict):
    # initialize data great expectations context object
    context = ge.data_context.DataContext()
    # run data validation for each data input
    for data_name, data_path in data_paths.items():
        # read data from S3
        data = pd.read_parquet(data_path, engine='pyarrow')
        # run ge checkpoint
        context.run_checkpoint(checkpoint_name='intent_checkpoint',
                               batch_request={
                                    'datasource_name': 's3_parquet',
                                    'data_connector_name': 'runtime_data_connector',
                                    'data_asset_name': data_name,
                                    'runtime_parameters': {
                                       'batch_data': data  # bug in ge/arrow prevents it from reading parquet directly
                                    },
                                    'batch_identifiers': {
                                        "run_id": run_id,
                                        "data_name": data_name
                                    }
                               },
                               run_name= '-'.join([flow_name, run_id, data_name]),
                               run_time=datetime.utcnow(),
                               expectation_suite_name=data_name)
    context.build_data_docs()
    context.open_data_docs()
