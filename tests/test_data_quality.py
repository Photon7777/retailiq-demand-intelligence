from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_phase_1_required_files_exist() -> None:
    required_paths = [
        "README.md",
        ".env.example",
        "cloud/snowflake_setup.sql",
        "src/ingestion/load_to_snowflake.py",
        "src/utils/config.py",
        "src/utils/snowflake_connection.py",
        "dbt_retailiq/dbt_project.yml",
        "dbt_retailiq/models/schema.yml",
    ]

    missing = [path for path in required_paths if not (PROJECT_ROOT / path).exists()]

    assert missing == []


def test_snowflake_setup_includes_expected_raw_tables() -> None:
    setup_sql = (PROJECT_ROOT / "cloud/snowflake_setup.sql").read_text(encoding="utf-8").upper()
    expected_tables = ["SALES", "STORES", "FEATURES", "INVENTORY", "WEATHER"]

    for table_name in expected_tables:
        assert f"RAW.{table_name}" in setup_sql


def test_env_example_does_not_contain_fake_secret_values() -> None:
    env_text = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")

    assert "password123" not in env_text.lower()
    assert "sk-" not in env_text

