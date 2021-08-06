"""

Perform data validation over transformed data using Great Expectations including custom expectations

"""

import sys
from typing import Dict
from datetime import datetime

import pandas as pd
import great_expectations as ge


# add great_expectations/plugins to path
sys.path.append('great_expectations')
# import of custom expectation required even if not explictly called
from plugins.custom_expectation import ExpectAverageSessionLengthToBeBetween


def validate_data(run_id: str,
                  flow_name: str,
                  data_paths: Dict[str, str]) -> None:
    """
    Entry point for data validation step

    :param run_id: current Metaflow run id
    :param flow_name: current Metaflow flow name
    :param data_paths: dict of data to paths for validaiton
    :return:
    """

    # initialize data great expectations context object
    context = ge.data_context.DataContext()
    # run data validation for each data input
    for data_name, data_path in data_paths.items():
        # read data from S3
        data = pd.read_parquet(data_path, engine='pyarrow')
        # run ge checkpoint
        context.run_checkpoint(checkpoint_name='intent_checkpoint',
                               # runtime batch request
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
                               run_name='-'.join([flow_name,
                                                 str(run_id), data_name]),
                               run_time=datetime.utcnow(),
                               # use name of data to select expectation suite
                               expectation_suite_name=data_name)
    context.build_data_docs()
    context.open_data_docs()
