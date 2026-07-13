"""Example Airflow DAG using ForgeFlow operators.

This DAG demonstrates how to use ForgeFlow operators, hooks, and sensors
in an Airflow workflow for orchestrating ETL pipelines.
"""

from datetime import datetime, timedelta

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ImportError:
    raise ImportError('Apache Airflow is required. Install with: pip install -e ".[airflow]"')

from forgeflow.airflow import ForgeFlowOperator, ForgeFlowSensor, ForgeFlowValidateOperator

# Default arguments for the DAG
default_args = {
    "owner": "forgeflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# Create the DAG
with DAG(
    "forgeflow_example_pipeline",
    default_args=default_args,
    description="Example ForgeFlow ETL pipeline",
    schedule_interval=timedelta(days=1),
    catchup=False,
    tags=["forgeflow", "etl", "example"],
) as dag:

    # Task 1: Wait for configuration to be ready
    wait_for_config = ForgeFlowSensor(
        task_id="wait_for_config",
        pipeline_name="example_pipeline",
        config_path="config/pipelines.yaml",
        poke_interval=30,
        timeout=300,
    )

    # Task 2: Validate pipeline configuration
    validate_pipeline = ForgeFlowValidateOperator(
        task_id="validate_pipeline",
        pipeline_name="example_pipeline",
        config_path="config/pipelines.yaml",
    )

    # Task 3: Run the ForgeFlow pipeline
    run_pipeline = ForgeFlowOperator(
        task_id="run_example_pipeline",
        pipeline_name="example_pipeline",
        config_path="config/pipelines.yaml",
        push_to_xcom=True,
        validate_before_run=True,
    )

    # Task 4: Process results (custom Python function)
    def process_results(**context):
        """Process pipeline execution results from XCom."""
        ti = context["ti"]
        result = ti.xcom_pull(task_ids="run_example_pipeline")

        if result and result.get("status") == "success":
            print(f"✅ Pipeline completed: {result['message']}")
        else:
            print("⚠️ No result received from pipeline")

    process_task = PythonOperator(
        task_id="process_results",
        python_callable=process_results,
        provide_context=True,
    )

    # Define task dependencies
    wait_for_config >> validate_pipeline >> run_pipeline >> process_task


# Example 2: Multiple pipelines in parallel
with DAG(
    "forgeflow_parallel_pipelines",
    default_args=default_args,
    description="Run multiple ForgeFlow pipelines in parallel",
    schedule_interval="0 2 * * *",  # Run at 2 AM daily
    catchup=False,
    tags=["forgeflow", "etl", "parallel"],
) as parallel_dag:

    # Validate all pipelines first
    validate_all = ForgeFlowValidateOperator(
        task_id="validate_all_pipelines",
        pipeline_name=None,  # Validates all pipelines
        config_path="config/pipelines.yaml",
    )

    # Run multiple pipelines in parallel
    pipeline_tasks = []
    for pipeline_name in ["pipeline_1", "pipeline_2", "pipeline_3"]:
        task = ForgeFlowOperator(
            task_id=f"run_{pipeline_name}",
            pipeline_name=pipeline_name,
            config_path="config/pipelines.yaml",
            push_to_xcom=False,
        )
        pipeline_tasks.append(task)

    # Set dependencies: validate first, then run all in parallel
    validate_all >> pipeline_tasks
