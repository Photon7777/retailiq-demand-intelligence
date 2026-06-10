from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_airflow_orchestration_assets_exist() -> None:
    required_paths = [
        "cloud/snowflake_airflow_user.sql",
        "orchestration/airflow/Dockerfile",
        "orchestration/airflow/README.md",
        "orchestration/airflow/dags/retailiq_phase2_dag.py",
    ]

    missing = [path for path in required_paths if not (PROJECT_ROOT / path).exists()]

    assert missing == []


def test_airflow_dag_declares_expected_pipeline_tasks() -> None:
    dag_text = (PROJECT_ROOT / "orchestration/airflow/dags/retailiq_phase2_dag.py").read_text(encoding="utf-8")

    expected_task_ids = [
        "validate_walmart_source_files",
        "prepare_walmart_data",
        "optional_upload_prepared_files_to_gcs",
        "load_raw_tables_to_snowflake",
        "train_forecast_model",
        "generate_forecast_risk_and_anomaly_outputs",
        "load_ml_outputs_to_snowflake",
        "dbt_run_marts",
        "dbt_test_marts",
    ]

    for task_id in expected_task_ids:
        assert f'task_id="{task_id}"' in dag_text


def test_docker_compose_exposes_airflow_profile() -> None:
    compose_text = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "airflow-webserver:" in compose_text
    assert "airflow-scheduler:" in compose_text
    assert "airflow-init:" in compose_text
    assert "- airflow" in compose_text
    assert "8081:8080" in compose_text


def test_airflow_init_keeps_official_entrypoint() -> None:
    compose_text = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    airflow_init_block = compose_text.split("  airflow-init:", maxsplit=1)[1].split("  airflow-webserver:", maxsplit=1)[0]

    assert "entrypoint:" not in airflow_init_block
    assert "- bash" in airflow_init_block
    assert "- -c" in airflow_init_block


def test_dbt_profile_supports_snowflake_key_pair_auth() -> None:
    profile_text = (PROJECT_ROOT / "dbt_retailiq/profiles.yml.example").read_text(encoding="utf-8")

    assert "SNOWFLAKE_AUTHENTICATOR" in profile_text
    assert "snowflake_jwt" in profile_text
    assert "private_key_path" in profile_text
    assert "SNOWFLAKE_PRIVATE_KEY_FILE" in profile_text
