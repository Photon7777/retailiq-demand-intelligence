"""Governed SQL generation and validation for the RetailIQ analyst."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any

import pandas as pd
from openai import OpenAI
from openai import OpenAIError

from src.ai.prompt_templates import SQL_AGENT_GUARDRAILS, SQL_GENERATION_PROMPT
from src.utils.config import AppConfig, get_config
from src.utils.snowflake_queries import run_query


APPROVED_MART_TABLES: dict[str, tuple[str, ...]] = {
    "DIM_STORE": ("store_id", "store_type", "store_size"),
    "DIM_DATE": ("date_day", "year", "month", "week_of_year", "is_holiday_week"),
    "FACT_SALES": ("store_id", "dept_id", "sales_date", "weekly_sales", "is_holiday"),
    "FACT_INVENTORY": ("store_id", "dept_id", "inventory_date", "available_inventory"),
    "FACT_DEMAND": (
        "store_id",
        "dept_id",
        "demand_date",
        "observed_demand",
        "available_inventory",
        "safety_stock_units",
        "reorder_point_units",
    ),
    "FACT_FORECAST": (
        "store_id",
        "dept_id",
        "forecast_date",
        "horizon_days",
        "predicted_demand",
        "actual_demand",
        "prediction_interval_lower",
        "prediction_interval_upper",
        "model_name",
        "model_version",
    ),
    "FACT_STOCKOUT_RISK": (
        "store_id",
        "dept_id",
        "risk_date",
        "predicted_demand",
        "available_inventory",
        "stockout_risk_score",
        "risk_category",
        "recommended_action",
        "model_version",
    ),
    "FACT_ANOMALIES": (
        "store_id",
        "dept_id",
        "sales_date",
        "weekly_sales",
        "anomaly_score",
        "is_anomaly",
        "severity",
        "direction",
        "model_version",
    ),
}

FORBIDDEN_SQL_PATTERN = re.compile(
    r"\b("
    r"alter|call|copy|create|delete|describe|drop|execute|explain|grant|insert|merge|"
    r"put|remove|revoke|show|truncate|undrop|update|use"
    r")\b",
    re.IGNORECASE,
)
TABLE_REFERENCE_PATTERN = re.compile(r"\b(?:from|join)\s+([A-Za-z0-9_.$\"]+)", re.IGNORECASE)
CTE_NAME_PATTERN = re.compile(r"(?:with|,)\s+([A-Za-z_][A-Za-z0-9_]*)\s+as\s*\(", re.IGNORECASE)
LIMIT_PATTERN = re.compile(r"\blimit\s+\d+\b", re.IGNORECASE)


@dataclass(frozen=True)
class SqlGenerationResult:
    """A governed SQL plan returned by the analyst SQL layer."""

    sql: str
    rationale: str
    used_openai: bool
    model: str | None = None
    warning: str | None = None


class SqlValidationError(ValueError):
    """Raised when generated SQL violates RetailIQ guardrails."""


def _database(config: AppConfig | None = None) -> str:
    config = config or get_config()
    return (config.snowflake_database or "RETAILIQ_DB").upper()


def _qualified(table: str, config: AppConfig | None = None) -> str:
    return f"{_database(config)}.MARTS.{table.upper()}"


def catalog_for_prompt(config: AppConfig | None = None) -> str:
    """Return a compact table catalog for LLM SQL generation."""
    lines = []
    for table, columns in APPROVED_MART_TABLES.items():
        lines.append(f"- {_qualified(table, config)}({', '.join(columns)})")
    return "\n".join(lines)


def strip_sql_fences(sql: str) -> str:
    """Remove Markdown SQL fences and trailing statement delimiters."""
    cleaned = sql.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:sql)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    cleaned = re.sub(r"--.*?$", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
    return cleaned.strip().rstrip(";").strip()


def _normalize_table_reference(reference: str) -> str:
    return reference.replace('"', "").split(".")[-1].upper()


def validate_read_only_sql(sql: str, config: AppConfig | None = None) -> str:
    """Validate SQL against read-only and mart-only guardrails."""
    cleaned = strip_sql_fences(sql)
    lowered = cleaned.lower()

    if not cleaned:
        raise SqlValidationError("Generated SQL is empty.")
    if ";" in cleaned:
        raise SqlValidationError("Only one SQL statement is allowed.")
    if not (lowered.startswith("select") or lowered.startswith("with")):
        raise SqlValidationError("Only SELECT or WITH queries are allowed.")
    if FORBIDDEN_SQL_PATTERN.search(cleaned):
        raise SqlValidationError("Generated SQL contains a forbidden command.")
    if re.search(r"\b(raw|ml|staging|analytics|information_schema|account_usage|snowflake)\b", cleaned, re.IGNORECASE):
        raise SqlValidationError("Generated SQL can only reference approved MARTS tables.")

    approved_tables = set(APPROVED_MART_TABLES)
    cte_names = {match.group(1).upper() for match in CTE_NAME_PATTERN.finditer(cleaned)}
    referenced_tables = [_normalize_table_reference(match.group(1)) for match in TABLE_REFERENCE_PATTERN.finditer(cleaned)]
    if not referenced_tables:
        raise SqlValidationError("Generated SQL must reference at least one approved mart table.")

    invalid_tables = [table for table in referenced_tables if table not in approved_tables and table not in cte_names]
    if invalid_tables:
        readable = ", ".join(sorted(set(invalid_tables)))
        raise SqlValidationError(f"Generated SQL references unsupported tables: {readable}.")

    return cleaned


def enforce_limit(sql: str, row_limit: int = 100) -> str:
    """Append a Snowflake LIMIT clause when one is not already present."""
    cleaned = strip_sql_fences(sql)
    if LIMIT_PATTERN.search(cleaned):
        return cleaned
    return f"{cleaned}\nlimit {int(row_limit)}"


def fallback_sql_for_question(question: str, config: AppConfig | None = None) -> SqlGenerationResult:
    """Return deterministic governed SQL when OpenAI is not configured."""
    normalized = question.lower()

    if "stockout" in normalized or "risk" in normalized:
        if "highest" in normalized or "top" in normalized or "critical" in normalized:
            sql = f"""
            select
                store_id,
                dept_id,
                risk_date,
                predicted_demand,
                available_inventory,
                stockout_risk_score,
                risk_category,
                recommended_action
            from {_qualified("FACT_STOCKOUT_RISK", config)}
            order by stockout_risk_score desc
            limit 10
            """
            rationale = "Return the highest stockout risk rows by score."
        else:
            sql = f"""
            select
                risk_category,
                count(*) as risk_rows,
                avg(stockout_risk_score) as avg_risk_score,
                max(stockout_risk_score) as max_risk_score
            from {_qualified("FACT_STOCKOUT_RISK", config)}
            group by risk_category
            order by
                case risk_category
                    when 'Critical' then 1
                    when 'High' then 2
                    when 'Medium' then 3
                    else 4
                end
            """
            rationale = "Summarize stockout risk by category."
    elif "anomal" in normalized:
        sql = f"""
        select
            severity,
            direction,
            count(*) as anomaly_rows,
            avg(abs(anomaly_score)) as avg_abs_anomaly_score
        from {_qualified("FACT_ANOMALIES", config)}
        where is_anomaly
        group by severity, direction
        order by anomaly_rows desc
        """
        rationale = "Summarize flagged sales anomalies by severity and direction."
    elif "forecast" in normalized or "wape" in normalized or "error" in normalized:
        sql = f"""
        select
            model_version,
            count(*) as forecast_rows,
            sum(predicted_demand) as predicted_demand,
            sum(actual_demand) as actual_demand,
            sum(abs(actual_demand - predicted_demand)) / nullif(sum(abs(actual_demand)), 0) as wape
        from {_qualified("FACT_FORECAST", config)}
        group by model_version
        order by forecast_rows desc
        """
        rationale = "Summarize forecast accuracy and demand volume by model version."
    elif "store" in normalized and ("highest" in normalized or "top" in normalized or "best" in normalized):
        sql = f"""
        select
            s.store_id,
            ds.store_type,
            ds.store_size,
            sum(s.weekly_sales) as total_sales,
            avg(s.weekly_sales) as avg_weekly_sales,
            count(*) as sales_records
        from {_qualified("FACT_SALES", config)} as s
        left join {_qualified("DIM_STORE", config)} as ds
            on s.store_id = ds.store_id
        group by s.store_id, ds.store_type, ds.store_size
        order by total_sales desc
        limit 10
        """
        rationale = "Rank stores by total sales."
    elif "department" in normalized or "dept" in normalized:
        sql = f"""
        select
            dept_id,
            sum(weekly_sales) as total_sales,
            avg(weekly_sales) as avg_weekly_sales,
            count(*) as sales_records
        from {_qualified("FACT_SALES", config)}
        group by dept_id
        order by total_sales desc
        limit 10
        """
        rationale = "Rank departments by total sales."
    elif "trend" in normalized or "weekly" in normalized or "over time" in normalized:
        sql = f"""
        select
            sales_date,
            sum(weekly_sales) as weekly_sales,
            count(distinct store_id) as store_count,
            count(distinct dept_id) as dept_count
        from {_qualified("FACT_SALES", config)}
        group by sales_date
        order by sales_date desc
        limit 20
        """
        rationale = "Return recent weekly sales trend."
    else:
        sql = f"""
        select
            sum(weekly_sales) as total_sales,
            count(*) as sales_records,
            count(distinct store_id) as store_count,
            count(distinct dept_id) as dept_count,
            min(sales_date) as start_date,
            max(sales_date) as end_date
        from {_qualified("FACT_SALES", config)}
        """
        rationale = "Return executive sales totals from the governed sales fact."

    governed_sql = validate_read_only_sql(sql, config)
    return SqlGenerationResult(
        sql=enforce_limit(governed_sql),
        rationale=rationale,
        used_openai=False,
        warning="OpenAI API key is not configured, so RetailIQ used a deterministic governed query template.",
    )


def _fallback_after_openai_error(
    question: str,
    config: AppConfig | None = None,
    warning: str = "OpenAI SQL generation failed, so RetailIQ used a deterministic governed query template.",
) -> SqlGenerationResult:
    result = fallback_sql_for_question(question, config)
    return SqlGenerationResult(
        sql=result.sql,
        rationale=result.rationale,
        used_openai=False,
        model=result.model,
        warning=warning,
    )


def _parse_openai_sql_response(raw_content: str) -> tuple[str, str]:
    try:
        payload = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise SqlValidationError("OpenAI did not return valid JSON for the SQL plan.") from exc

    sql = str(payload.get("sql", "")).strip()
    rationale = str(payload.get("rationale", "")).strip() or "Generated a governed Snowflake SQL query."
    return sql, rationale


def generate_sql_from_question(
    question: str,
    config: AppConfig | None = None,
    row_limit: int = 100,
) -> SqlGenerationResult:
    """Generate safe Snowflake SQL from a business question."""
    config = config or get_config()
    question = question.strip()
    if not question:
        raise ValueError("Question cannot be blank.")

    if not config.openai_api_key:
        return fallback_sql_for_question(question, config)

    client = OpenAI(api_key=config.openai_api_key)
    model = config.openai_model or "gpt-5-mini"
    try:
        response = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": SQL_GENERATION_PROMPT.format(
                        guardrails=SQL_AGENT_GUARDRAILS,
                        table_catalog=catalog_for_prompt(config),
                        row_limit=row_limit,
                    ),
                },
                {"role": "user", "content": question},
            ],
        )
        content = response.choices[0].message.content or "{}"
        sql, rationale = _parse_openai_sql_response(content)
        governed_sql = enforce_limit(validate_read_only_sql(sql, config), row_limit=row_limit)
        return SqlGenerationResult(sql=governed_sql, rationale=rationale, used_openai=True, model=model)
    except (OpenAIError, SqlValidationError, ValueError, json.JSONDecodeError):
        return _fallback_after_openai_error(question, config)


def execute_governed_sql(
    sql: str,
    config: AppConfig | None = None,
    row_limit: int = 100,
) -> pd.DataFrame:
    """Validate and execute a governed read-only SQL query."""
    governed_sql = enforce_limit(validate_read_only_sql(sql, config), row_limit=row_limit)
    return run_query(governed_sql, config=config)
