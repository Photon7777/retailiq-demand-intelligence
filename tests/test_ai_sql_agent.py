from __future__ import annotations

import pytest

from src.ai.sql_agent import (
    SqlValidationError,
    enforce_limit,
    fallback_sql_for_question,
    strip_sql_fences,
    validate_read_only_sql,
)
from src.utils.config import AppConfig


def make_config() -> AppConfig:
    return AppConfig(
        snowflake_account="example-account",
        snowflake_user="RETAILIQ_APP_USER",
        snowflake_password=None,
        snowflake_authenticator="SNOWFLAKE_JWT",
        snowflake_private_key_file="/secrets/snowflake_private_key.p8",
        snowflake_private_key_file_pwd=None,
        snowflake_passcode=None,
        snowflake_passcode_in_password=False,
        snowflake_role="RETAILIQ_APP_ROLE",
        snowflake_warehouse="RETAILIQ_WH",
        snowflake_database="RETAILIQ_DB",
        snowflake_schema="MARTS",
        gcp_project_id=None,
        gcp_bucket_name=None,
        google_application_credentials=None,
        openai_api_key=None,
    )


def test_strip_sql_fences_removes_markdown_and_semicolon() -> None:
    assert strip_sql_fences("```sql\nselect * from RETAILIQ_DB.MARTS.FACT_SALES;\n```") == (
        "select * from RETAILIQ_DB.MARTS.FACT_SALES"
    )


def test_validate_read_only_sql_accepts_approved_mart_table() -> None:
    sql = "select store_id, sum(weekly_sales) from RETAILIQ_DB.MARTS.FACT_SALES group by store_id"

    assert validate_read_only_sql(sql, make_config()) == sql


def test_validate_read_only_sql_rejects_writes() -> None:
    with pytest.raises(SqlValidationError):
        validate_read_only_sql("delete from RETAILIQ_DB.MARTS.FACT_SALES", make_config())


def test_validate_read_only_sql_rejects_unsupported_schema() -> None:
    with pytest.raises(SqlValidationError, match="MARTS"):
        validate_read_only_sql("select * from RETAILIQ_DB.RAW.SALES", make_config())


def test_validate_read_only_sql_rejects_multiple_statements() -> None:
    with pytest.raises(SqlValidationError, match="one SQL statement"):
        validate_read_only_sql("select * from RETAILIQ_DB.MARTS.FACT_SALES; select current_user()", make_config())


def test_enforce_limit_appends_limit_when_missing() -> None:
    limited = enforce_limit("select * from RETAILIQ_DB.MARTS.FACT_SALES", row_limit=25)

    assert limited.endswith("limit 25")


def test_fallback_sql_for_sales_question_uses_governed_mart() -> None:
    result = fallback_sql_for_question("Which stores have the highest sales?", make_config())

    assert result.used_openai is False
    assert "RETAILIQ_DB.MARTS.FACT_SALES" in result.sql
    assert "RETAILIQ_DB.MARTS.DIM_STORE" in result.sql
    assert "limit 10" in result.sql.lower()
