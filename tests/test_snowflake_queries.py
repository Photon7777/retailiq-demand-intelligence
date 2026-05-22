from __future__ import annotations

import pytest

from src.utils.config import AppConfig
from src.utils.snowflake_queries import _forecast_where_clause, qualified_table


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


def test_forecast_where_clause_uses_bound_parameters() -> None:
    clause, params = _forecast_where_clause(store_id=1, dept_id=7, horizon_days=0)

    assert clause == (
        "where store_id = %(store_id)s and dept_id = %(dept_id)s "
        "and horizon_days = %(horizon_days)s"
    )
    assert params == {"store_id": 1, "dept_id": 7, "horizon_days": 0}
