# Transformation avec dbt dans Airflow
import os
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

DBT_PROJECT_DIR = "/usr/app/weather_dbt"

with DAG(
    dag_id="dbt_run",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["dbt", "transform"],
) as dag:

    run_dbt = BashOperator(
        task_id="run_dbt_models",
        bash_command=(
            "dbt run --project-dir {{ params.project_dir }} "
            "--profiles-dir /usr/app --no-write-json --log-format text "
            "--log-path /tmp --target-path /tmp/target"
        ),
        params={"project_dir": DBT_PROJECT_DIR},
    )

    test_dbt = BashOperator(
        task_id="test_dbt_models",
        bash_command=(
            "dbt test --project-dir {{ params.project_dir }} "
            "--profiles-dir /usr/app --no-write-json --log-format text "
            "--log-path /tmp --target-path /tmp/target"
        ),
        params={"project_dir": DBT_PROJECT_DIR},
    )



    run_dbt >> test_dbt
