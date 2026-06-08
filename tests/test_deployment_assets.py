from __future__ import annotations

from pathlib import Path

import pytest

from src.utils.config import AppConfig
from src.utils.snowflake_connection import SnowflakeConfigurationError, get_snowflake_connection


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def make_config(**overrides) -> AppConfig:
    values = {
        "snowflake_account": "example-account",
        "snowflake_user": "RETAILIQ_APP_USER",
        "snowflake_password": None,
        "snowflake_authenticator": "SNOWFLAKE_JWT",
        "snowflake_private_key_file": "/secrets/snowflake_private_key.p8",
        "snowflake_private_key_file_pwd": None,
        "snowflake_passcode": None,
        "snowflake_passcode_in_password": False,
        "snowflake_role": "RETAILIQ_APP_ROLE",
        "snowflake_warehouse": "RETAILIQ_WH",
        "snowflake_database": "RETAILIQ_DB",
        "snowflake_schema": "MARTS",
        "gcp_project_id": None,
        "gcp_bucket_name": None,
        "google_application_credentials": None,
        "openai_api_key": None,
    }
    values.update(overrides)
    return AppConfig(**values)


def test_cloud_run_deployment_assets_exist() -> None:
    required_paths = [
        "Dockerfile",
        ".dockerignore",
        "cloud/cloud_run_deploy.md",
        "cloud/snowflake_app_user.sql",
    ]

    missing = [path for path in required_paths if not (PROJECT_ROOT / path).exists()]

    assert missing == []


def test_dockerignore_excludes_local_data_and_secrets() -> None:
    dockerignore = (PROJECT_ROOT / ".dockerignore").read_text(encoding="utf-8")

    assert ".env" in dockerignore
    assert "data/raw/walmart/*" in dockerignore
    assert "data/processed/walmart/*" in dockerignore
    assert "data/ml_outputs/*" in dockerignore
    assert "models/*" in dockerignore


def test_snowflake_jwt_requires_private_key_file() -> None:
    config = make_config(snowflake_private_key_file=None)

    with pytest.raises(SnowflakeConfigurationError, match="snowflake_private_key_file"):
        get_snowflake_connection(config)


def test_snowflake_jwt_connection_kwargs(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_kwargs: dict[str, object] = {}

    def fake_connect(**kwargs):
        captured_kwargs.update(kwargs)
        return object()

    monkeypatch.setattr("snowflake.connector.connect", fake_connect)

    connection = get_snowflake_connection(make_config())

    assert connection is not None
    assert captured_kwargs["authenticator"] == "SNOWFLAKE_JWT"
    assert captured_kwargs["private_key_file"] == "/secrets/snowflake_private_key.p8"
    assert "password" not in captured_kwargs
    assert captured_kwargs["role"] == "RETAILIQ_APP_ROLE"
