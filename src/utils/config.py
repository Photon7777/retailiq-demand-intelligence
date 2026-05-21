"""Application configuration loaded from environment variables."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    """Typed access to RetailIQ runtime configuration."""

    snowflake_account: str | None
    snowflake_user: str | None
    snowflake_password: str | None
    snowflake_role: str | None
    snowflake_warehouse: str | None
    snowflake_database: str | None
    snowflake_schema: str | None
    gcp_project_id: str | None
    gcp_bucket_name: str | None
    google_application_credentials: str | None
    openai_api_key: str | None

    def missing(self, keys: Iterable[str]) -> list[str]:
        """Return required keys that are not configured."""
        missing_keys: list[str] = []
        for key in keys:
            value = getattr(self, key)
            if value is None or str(value).strip() == "":
                missing_keys.append(key)
        return missing_keys


def _read_env(name: str) -> str | None:
    value = os.getenv(name)
    return value.strip() if value and value.strip() else None


def get_config(env_file: str | Path | None = None) -> AppConfig:
    """Load `.env` and return an immutable application config object."""
    if env_file:
        load_dotenv(dotenv_path=env_file)
    else:
        load_dotenv()

    return AppConfig(
        snowflake_account=_read_env("SNOWFLAKE_ACCOUNT"),
        snowflake_user=_read_env("SNOWFLAKE_USER"),
        snowflake_password=_read_env("SNOWFLAKE_PASSWORD"),
        snowflake_role=_read_env("SNOWFLAKE_ROLE"),
        snowflake_warehouse=_read_env("SNOWFLAKE_WAREHOUSE"),
        snowflake_database=_read_env("SNOWFLAKE_DATABASE"),
        snowflake_schema=_read_env("SNOWFLAKE_SCHEMA"),
        gcp_project_id=_read_env("GCP_PROJECT_ID"),
        gcp_bucket_name=_read_env("GCP_BUCKET_NAME"),
        google_application_credentials=_read_env("GOOGLE_APPLICATION_CREDENTIALS"),
        openai_api_key=_read_env("OPENAI_API_KEY"),
    )


SNOWFLAKE_REQUIRED_CONFIG = (
    "snowflake_account",
    "snowflake_user",
    "snowflake_password",
    "snowflake_warehouse",
    "snowflake_database",
    "snowflake_schema",
)

