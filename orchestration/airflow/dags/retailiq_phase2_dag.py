"""Airflow orchestration for the RetailIQ data and ML buildout."""

from __future__ import annotations

from datetime import datetime, timedelta
import os
import shlex

try:
    from airflow import DAG
except ModuleNotFoundError:  # pragma: no cover - Airflow 3 compatibility path.
    from airflow.sdk import DAG

try:
    from airflow.providers.standard.operators.bash import BashOperator
except ModuleNotFoundError:  # pragma: no cover - Airflow 2 compatibility path.
    from airflow.operators.bash import BashOperator


PROJECT_DIR = os.getenv("RETAILIQ_PROJECT_DIR", "/opt/airflow/retailiq")
PYTHON_BIN = os.getenv("RETAILIQ_PYTHON_BIN", "python")
DBT_BIN = os.getenv("RETAILIQ_DBT_BIN", "dbt")

RAW_INPUT_DIR = os.getenv("RETAILIQ_AIRFLOW_INPUT_DIR", "data/raw/walmart")
PROCESSED_DIR = os.getenv("RETAILIQ_AIRFLOW_PROCESSED_DIR", "data/processed/walmart")
MODEL_DIR = os.getenv("RETAILIQ_AIRFLOW_MODEL_DIR", "models")
OUTPUT_DIR = os.getenv("RETAILIQ_AIRFLOW_OUTPUT_DIR", "data/ml_outputs")
DBT_DIR = os.getenv("RETAILIQ_AIRFLOW_DBT_DIR", f"{PROJECT_DIR}/dbt_retailiq")

RANDOM_SEED = os.getenv("RETAILIQ_AIRFLOW_RANDOM_SEED", "42")
N_ESTIMATORS = os.getenv("RETAILIQ_AIRFLOW_N_ESTIMATORS", "50")
MAX_DEPTH = os.getenv("RETAILIQ_AIRFLOW_MAX_DEPTH", "16")
MIN_SAMPLES_LEAF = os.getenv("RETAILIQ_AIRFLOW_MIN_SAMPLES_LEAF", "5")
MAX_SAMPLES = os.getenv("RETAILIQ_AIRFLOW_MAX_SAMPLES", "0.65")
GCS_PREFIX = os.getenv("RETAILIQ_AIRFLOW_GCS_PREFIX", "retailiq/raw")


def truthy_env(name: str, default: str = "false") -> bool:
    """Interpret a container environment value as a boolean flag."""
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "y"}


def project_command(command: str, cwd: str = PROJECT_DIR) -> str:
    """Wrap a command with strict shell settings and the project working directory."""
    return "\n".join(
        [
            "set -euo pipefail",
            f"cd {shlex.quote(cwd)}",
            command,
        ]
    )


def maybe_truncate_flag() -> str:
    """Return the loader truncate flag when configured for repeatable refreshes."""
    return " --truncate-first" if truthy_env("RETAILIQ_AIRFLOW_TRUNCATE_FIRST", "true") else ""


default_args = {
    "owner": "retailiq",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="retailiq_phase2_pipeline",
    description="Prepare Walmart data, load Snowflake, train ML outputs, and build dbt marts.",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    default_args=default_args,
    tags=["retailiq", "snowflake", "dbt", "ml"],
) as dag:
    validate_inputs = BashOperator(
        task_id="validate_walmart_source_files",
        bash_command=project_command(
            "\n".join(
                [
                    f"test -f {shlex.quote(RAW_INPUT_DIR)}/train.csv",
                    f"test -f {shlex.quote(RAW_INPUT_DIR)}/stores.csv",
                    f"test -f {shlex.quote(RAW_INPUT_DIR)}/features.csv",
                ]
            )
        ),
    )

    prepare_walmart_data = BashOperator(
        task_id="prepare_walmart_data",
        bash_command=project_command(
            " ".join(
                [
                    PYTHON_BIN,
                    "-m src.ingestion.prepare_walmart_data",
                    "--input-dir",
                    shlex.quote(RAW_INPUT_DIR),
                    "--output-dir",
                    shlex.quote(PROCESSED_DIR),
                    "--random-seed",
                    shlex.quote(RANDOM_SEED),
                ]
            )
        ),
    )

    optional_gcs_upload = BashOperator(
        task_id="optional_upload_prepared_files_to_gcs",
        bash_command=project_command(
            "\n".join(
                [
                    'if [ "${RETAILIQ_AIRFLOW_UPLOAD_GCS:-false}" = "true" ]; then',
                    " ".join(
                        [
                            f"  {PYTHON_BIN}",
                            "-m src.ingestion.upload_to_gcs",
                            "--sample-dir",
                            shlex.quote(PROCESSED_DIR),
                            "--prefix",
                            shlex.quote(GCS_PREFIX),
                        ]
                    ),
                    "else",
                    '  echo "Skipping GCS upload because RETAILIQ_AIRFLOW_UPLOAD_GCS is false."',
                    "fi",
                ]
            )
        ),
    )

    load_raw_tables = BashOperator(
        task_id="load_raw_tables_to_snowflake",
        bash_command=project_command(
            f"{PYTHON_BIN} -m src.ingestion.load_to_snowflake "
            f"--sample-dir {shlex.quote(PROCESSED_DIR)}{maybe_truncate_flag()}"
        ),
    )

    train_forecast_model = BashOperator(
        task_id="train_forecast_model",
        bash_command=project_command(
            " ".join(
                [
                    PYTHON_BIN,
                    "-m src.ml.train_forecast_model",
                    "--data-dir",
                    shlex.quote(PROCESSED_DIR),
                    "--model-dir",
                    shlex.quote(MODEL_DIR),
                    "--n-estimators",
                    shlex.quote(N_ESTIMATORS),
                    "--max-depth",
                    shlex.quote(MAX_DEPTH),
                    "--min-samples-leaf",
                    shlex.quote(MIN_SAMPLES_LEAF),
                    "--max-samples",
                    shlex.quote(MAX_SAMPLES),
                    "--random-state",
                    shlex.quote(RANDOM_SEED),
                ]
            )
        ),
    )

    generate_ml_outputs = BashOperator(
        task_id="generate_forecast_risk_and_anomaly_outputs",
        bash_command=project_command(
            f"{PYTHON_BIN} -m src.ml.generate_predictions "
            f"--data-dir {shlex.quote(PROCESSED_DIR)} "
            f"--model-path {shlex.quote(MODEL_DIR)}/retailiq_forecast_model.pkl "
            f"--output-dir {shlex.quote(OUTPUT_DIR)}"
        ),
    )

    load_ml_tables = BashOperator(
        task_id="load_ml_outputs_to_snowflake",
        bash_command=project_command(
            f"{PYTHON_BIN} -m src.ingestion.load_ml_outputs_to_snowflake "
            f"--output-dir {shlex.quote(OUTPUT_DIR)}{maybe_truncate_flag()}"
        ),
    )

    dbt_run = BashOperator(
        task_id="dbt_run_marts",
        bash_command=project_command(f"{DBT_BIN} run", cwd=DBT_DIR),
    )

    dbt_test = BashOperator(
        task_id="dbt_test_marts",
        bash_command=project_command(f"{DBT_BIN} test", cwd=DBT_DIR),
    )

    (
        validate_inputs
        >> prepare_walmart_data
        >> optional_gcs_upload
        >> load_raw_tables
        >> train_forecast_model
        >> generate_ml_outputs
        >> load_ml_tables
        >> dbt_run
        >> dbt_test
    )
