from __future__ import annotations

import pytest

from src.utils.config import AppConfig
from src.utils.snowflake_queries import qualified_table


def make_config(database: str = "RETAILIQ_DB") -> AppConfig:
    return AppConfig(
        snowflake_account="example-account",
        snowflake_user="SAI",
        snowflake_password=None,
        snowflake_authenticator=None,
        snowflake_passcode=None,
        snowflake_passcode_in_password=False,
        snowflake_role="ACCOUNTADMIN",
        snowflake_warehouse="RETAILIQ_WH",
        snowflake_database=database,
        snowflake_schema="RAW",
        gcp_project_id=None,
        gcp_bucket_name=None,
        google_application_credentials=None,
        openai_api_key=None,
    )


def test_qualified_table_normalizes_identifiers() -> None:
    assert qualified_table("marts", "fact_sales", make_config()) == "RETAILIQ_DB.MARTS.FACT_SALES"


def test_qualified_table_rejects_unsafe_identifiers() -> None:
    with pytest.raises(ValueError):
        qualified_table("MARTS", "FACT_SALES;DROP TABLE RAW.SALES", make_config())

