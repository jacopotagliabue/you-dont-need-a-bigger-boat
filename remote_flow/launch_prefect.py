import os

from dotenv import load_dotenv

# load envs
load_dotenv(verbose=True, dotenv_path='.env')
from prefect.tasks.dbt import DbtShellTask
from prefect.tasks.shell import ShellTask
from datetime import timedelta
from prefect.schedules import IntervalSchedule
import pathlib

from prefect import task, Flow
from prefect.tasks.great_expectations import RunGreatExpectationsValidation

# make sure we have prefect token in the env
assert os.getenv('PREFECT__CLOUD__AUTH_TOKEN') is not None

# Define GE Task
validation_task = RunGreatExpectationsValidation(task_run_name="DataValidationTask")

# Define the dbt task
dbt_task = DbtShellTask(
       log_stderr=True,
       return_all=True,
       profiles_dir='~/.dbt/',
       dbt_kwargs={
           'type': 'snowflake',
           'threads': 1,
           'account': os.getenv('SNOWFLAKE_ACCOUNT')
       },
       helper_script="cd sigir_dbt",
       task_run_name="DataPreparationTask"
    )

# Define the metflow task
dir_path = os.path.dirname(os.path.realpath(__file__))
metaflow_task = ShellTask(helper_script=f"cd {dir_path}", task_run_name="TrainingTask")


serverless_task = ShellTask(helper_script=f"cd {dir_path}/serverless", task_run_name="DeploymentTask")

# instantiate schedule
# schedule = IntervalSchedule(interval=timedelta(minutes=60))
with Flow("AndrewTestFlow") as flow:
    # Prepare data with dbt
    dbt_output = dbt_task(command='dbt run')
    # Run GE validation tasks
    validation_output_content_flattened = validation_task(
       batch_kwargs={'data_asset_name': 'public.content_flattened', 'datasource': 'sigir_2021', 'schema': 'public', 'table': 'content_flattened'},
       expectation_suite_name="public.content_flattened.warning",
       context_root_dir=f"{pathlib.Path(__file__).parent.absolute()}/great_expectations"
    ).set_dependencies(upstream_tasks=[dbt_output])

    validation_output_sessions_stats = validation_task(
        batch_kwargs={'table': 'session_stats', 'schema': 'public', 'data_asset_name': 'public.session_stats', 'datasource': 'sigir_2021'},
        expectation_suite_name="public.session_stats",
        context_root_dir=f"{pathlib.Path(__file__).parent.absolute()}/great_expectations"
    ).set_dependencies(upstream_tasks=[dbt_output])

    # Launch metaflow
    metaflow_output = metaflow_task(
        command='METAFLOW_PROFILE=metaflow AWS_PROFILE=metaflow python metaflow/cart_baseline_flow.py --no-pylint run').set_dependencies(
        upstream_tasks=[validation_output_content_flattened, validation_output_sessions_stats])

    # Deploy Trained Model
    serverless_task(command="serverless deploy --aws-profile serverless").set_dependencies(upstream_tasks=[metaflow_output])

flow.register(project_name=os.getenv('PREFECT_PROJECT_NAME'))
flow.run_agent() #token=os.getenv('PREFECT_AGENT_KEY'))

