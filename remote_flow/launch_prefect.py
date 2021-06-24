import os

from dotenv import load_dotenv

# load envs
load_dotenv(verbose=True, dotenv_path='.env')
import prefect
from prefect.tasks.dbt import DbtShellTask
from datetime import timedelta
from prefect.schedules import IntervalSchedule
import pathlib


from prefect import task, Flow
from prefect.tasks.great_expectations import RunGreatExpectationsValidation


# Define checkpoint task
validation_task = RunGreatExpectationsValidation()


# make sure we have the variables...
# assert os.getenv('PREFECT_AGENT_KEY') is not None
# since here we are just notifying the HC endpoint, make sure we complete this by retrying


@task
def get_batch_kwargs(prev_task):
    return {'data_asset_name': 'public.content_flattened', 'datasource': 'sigir_2021', 'schema': 'public', 'table': 'content_flattened'}

# instantiate schedule
schedule = IntervalSchedule(interval=timedelta(minutes=60))
with Flow("AndrewTestFlow", schedule) as flow:
    task = DbtShellTask(
       log_stderr=True,
       return_all=True,
       profiles_dir='~/.dbt/',
       dbt_kwargs={
           'type': 'snowflake',
           'threads': 1,
           'account': os.getenv('SNOWFLAKE_ACCOUNT')
       },
       helper_script="cd sigir_dbt"
    )(command='dbt run')
    # add ge validation here
    batch_kwargs = get_batch_kwargs(task)

    expectation_suite_name = "public.content_flattened.warning"

    validation_task(
       batch_kwargs=batch_kwargs,
       expectation_suite_name=expectation_suite_name,
       context_root_dir=f"{pathlib.Path(__file__).parent.absolute()}/great_expectations"
    )
    # add trigger to metaflow
# remember, project needs to be created FIRST
flow.register(project_name=os.getenv('PREFECT_PROJECT_NAME'))
flow.run_agent() #token=os.getenv('PREFECT_AGENT_KEY'))

