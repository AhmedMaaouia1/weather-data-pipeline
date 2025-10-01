from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    "owner": "airflow",
    "retries": 1,
}

DBT_PROJECT_DIR = "/usr/app/weather_dbt"

with DAG(
    dag_id="analytics_weather",
    default_args=default_args,
    description="DAG pour transformations métier (weather metrics)",
    schedule_interval="@daily",
    start_date=datetime(2025, 9, 1),
    catchup=False,
    tags=["analytics", "weather"],
) as dag:

    run_metrics = BashOperator(
        task_id="run_weather_metrics",
        bash_command=(
            "dbt run --project-dir {{ params.project_dir }} "
            "--profiles-dir /usr/app --no-write-json --log-format text "
            "--log-path /tmp --target-path /tmp/target "
            "--select weather_metrics"
        ),
        params={"project_dir": DBT_PROJECT_DIR},
    )

    test_metrics = BashOperator(
        task_id="test_weather_metrics",
        bash_command=(
            "dbt test --project-dir {{ params.project_dir }} "
            "--profiles-dir /usr/app --no-write-json --log-format text "
            "--log-path /tmp --target-path /tmp/target "
            "--select weather_metrics"
        ),
        params={"project_dir": DBT_PROJECT_DIR},
    )

    run_metrics >> test_metrics
