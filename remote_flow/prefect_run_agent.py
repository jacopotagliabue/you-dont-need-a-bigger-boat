import os

from prefect import Flow
from prefect.tasks.dbt import DbtShellTask
from prefect.tasks.shell import ShellTask
from prefect.tasks.great_expectations import RunGreatExpectationsValidation


# Make sure we have Prefect Token in the env
assert os.getenv('PREFECT__CLOUD__AUTH_TOKEN') is not None


# Define the Great Expectations task
ge_validation_task_content_flattened = RunGreatExpectationsValidation(
    context_root_dir="./great_expectations",
    name="GE content_flattened",
)
ge_validation_task_session_stats = RunGreatExpectationsValidation(
    context_root_dir="./great_expectations",
    name="GE session_stats",
)

# Define the DBT task
dbt_task = DbtShellTask(
    log_stderr=True,
    return_all=True,
    profiles_dir=os.environ['DBT_PROFILES_DIR'],
    helper_script="cd ./dbt",
    name="DBT",
)

# Define the MetaFlow task
metaflow_task = ShellTask(
    log_stderr=True,
    return_all=True,
    name="MetaFlow",
)

# Define the Serverless Task
serverless_task = ShellTask(
    log_stderr=True,
    return_all=True,
    helper_script=f"cd ./serverless",
    name="Serverless",
)


flow_name = os.getenv('PREFECT_FLOW_NAME')

with Flow(flow_name) as flow:
    # Prepare data with dbt
    dbt_output = dbt_task(command='dbt run')

    # Run GE validation tasks
    database = os.getenv('SNOWFLAKE_DB').lower()
    schema = os.getenv('SNOWFLAKE_SCHEMA_TARGET').lower()

    ge_validation_output_content_flattened = ge_validation_task_content_flattened(
        expectation_suite_name="public.content_flattened.warning",
        batch_kwargs={
            'data_asset_name': 'public.content_flattened',
            'table': 'content_flattened',
            'datasource': database,
            'schema': schema,
        },
    ).set_dependencies(
        upstream_tasks=[dbt_output],
    )

    ge_validation_output_sessions_stats = ge_validation_task_session_stats(
        expectation_suite_name="public.session_stats",
        batch_kwargs={
            'data_asset_name': 'public.session_stats',
            'table': 'session_stats',
            'datasource': database,
            'schema': schema,
        },
    ).set_dependencies(
        upstream_tasks=[dbt_output],
    )

    # Launch MetaFlow
    metaflow_output = metaflow_task(
        command='python metaflow/cart_baseline_flow.py --no-pylint run'
    ).set_dependencies(
        upstream_tasks=[
            ge_validation_output_content_flattened,
            ge_validation_output_sessions_stats,
        ],
    )

    # Deploy Trained Model
    serverless_output = serverless_task(
        command="npm run deploy"
    ).set_dependencies(
        upstream_tasks=[metaflow_output]
    )

flow.register(project_name=os.getenv('PREFECT_PROJECT_NAME'))
flow.run_agent()
