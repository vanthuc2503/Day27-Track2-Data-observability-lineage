from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ImportError:  # pragma: no cover
    DAG = None

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))


def validate_orders_task() -> dict:
    """
    TODO:
    1. Import config values.
    2. Read the input CSV.
    3. Validate the rows.
    4. Write the JSON summary.
    5. Send the Discord alert.
    6. Raise an error on failed validation.
    """
    from src.config import AIRFLOW_INPUT_FILE, SUMMARY_FILE
    from src.validation import run_lab_check

    return run_lab_check(
        input_path=AIRFLOW_INPUT_FILE,
        output_path=SUMMARY_FILE,
        allow_failure=False,
        skip_discord=False,
    )


if DAG is not None:
    with DAG(
        dag_id="sales_data_quality_pipeline",
        start_date=datetime(2024, 1, 1),
        schedule=None,
        catchup=False,
        tags=["lab", "data-quality", "discord"],
    ) as dag:
        validate_orders = PythonOperator(
            task_id="validate_orders",
            python_callable=validate_orders_task,
        )
else:  # pragma: no cover
    dag = None
