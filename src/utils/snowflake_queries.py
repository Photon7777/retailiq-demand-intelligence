"""Reusable Snowflake query helpers for Streamlit pages."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

from src.ml.anomaly_detection import flag_zscore_anomalies
from src.ml.stockout_risk import score_stockout_risk_frame
from src.utils.config import AppConfig, get_config
from src.utils.snowflake_connection import snowflake_connection


IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


def _identifier(value: str) -> str:
    """Validate and normalize a Snowflake identifier from config/code."""
    if not IDENTIFIER_PATTERN.match(value):
        raise ValueError(f"Unsafe Snowflake identifier: {value}")
    return value.upper()


def _database(config: AppConfig | None = None) -> str:
    config = config or get_config()
    return _identifier(config.snowflake_database or "RETAILIQ_DB")


def qualified_table(schema: str, table: str, config: AppConfig | None = None) -> str:
    """Return a fully qualified Snowflake table name."""
    return f"{_database(config)}.{_identifier(schema)}.{_identifier(table)}"


def object_exists(schema: str, table: str, config: AppConfig | None = None) -> bool:
    """Return whether a table or view exists in the configured Snowflake database."""
    database = _database(config)
    df = run_query(
        f"""
        select count(*) as object_count
        from {database}.information_schema.tables
        where table_schema = %(schema)s
          and table_name = %(table)s
        """,
        config=config,
        params={"schema": _identifier(schema), "table": _identifier(table)},
    )
    return bool(df.iloc[0]["object_count"]) if not df.empty else False


def run_query(sql: str, config: AppConfig | None = None, params: dict[str, Any] | None = None) -> pd.DataFrame:
    """Run a Snowflake query and return a DataFrame with lower-case columns."""
    with snowflake_connection(config) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params=params)
            df = cursor.fetch_pandas_all()
    df.columns = [column.lower() for column in df.columns]
    return df


def fetch_platform_summary(config: AppConfig | None = None) -> pd.DataFrame:
    """Fetch high-level source and mart table health."""
    database = _database(config)
    return run_query(
        f"""
        select
            table_schema,
            table_name,
            table_type,
            coalesce(row_count, 0) as row_count,
            created,
            last_altered
        from {database}.information_schema.tables
        where table_schema in ('RAW', 'STAGING', 'MARTS', 'ML')
        order by table_schema, table_name
        """,
        config=config,
    )


def fetch_executive_metrics(config: AppConfig | None = None) -> pd.DataFrame:
    """Fetch core executive KPI metrics from mart tables."""
    fact_sales = qualified_table("MARTS", "FACT_SALES", config)
    fact_demand = qualified_table("MARTS", "FACT_DEMAND", config)
    return run_query(
        f"""
        select
            coalesce(sum(s.weekly_sales), 0) as total_sales,
            count(*) as sales_records,
            count(distinct s.store_id) as store_count,
            count(distinct s.dept_id) as dept_count,
            min(s.sales_date) as start_date,
            max(s.sales_date) as end_date,
            count_if(d.available_inventory is not null and d.observed_demand / nullif(d.available_inventory, 0) > 0.90)
                as high_or_critical_risk_count
        from {fact_sales} as s
        left join {fact_demand} as d
            on s.store_id = d.store_id
            and s.dept_id = d.dept_id
            and s.sales_date = d.demand_date
        """,
        config=config,
    )


def fetch_sales_trend(config: AppConfig | None = None) -> pd.DataFrame:
    """Fetch weekly sales trend by date."""
    fact_sales = qualified_table("MARTS", "FACT_SALES", config)
    return run_query(
        f"""
        select
            sales_date,
            sum(weekly_sales) as weekly_sales,
            count(distinct store_id) as store_count,
            count(distinct dept_id) as dept_count
        from {fact_sales}
        group by sales_date
        order by sales_date
        """,
        config=config,
    )


def fetch_store_sales(config: AppConfig | None = None) -> pd.DataFrame:
    """Fetch sales by store with store attributes."""
    fact_sales = qualified_table("MARTS", "FACT_SALES", config)
    dim_store = qualified_table("MARTS", "DIM_STORE", config)
    return run_query(
        f"""
        select
            s.store_id,
            ds.store_type,
            ds.store_size,
            sum(s.weekly_sales) as total_sales,
            avg(s.weekly_sales) as avg_weekly_sales,
            count(*) as sales_records
        from {fact_sales} as s
        left join {dim_store} as ds
            on s.store_id = ds.store_id
        group by s.store_id, ds.store_type, ds.store_size
        order by total_sales desc
        """,
        config=config,
    )


def fetch_department_sales(config: AppConfig | None = None) -> pd.DataFrame:
    """Fetch sales by department."""
    fact_sales = qualified_table("MARTS", "FACT_SALES", config)
    return run_query(
        f"""
        select
            dept_id,
            sum(weekly_sales) as total_sales,
            avg(weekly_sales) as avg_weekly_sales,
            count(*) as sales_records
        from {fact_sales}
        group by dept_id
        order by total_sales desc
        """,
        config=config,
    )


def fetch_demand_detail(config: AppConfig | None = None) -> pd.DataFrame:
    """Fetch demand and inventory detail, then score stockout risk."""
    fact_demand = qualified_table("MARTS", "FACT_DEMAND", config)
    df = run_query(
        f"""
        select
            store_id,
            dept_id,
            demand_date,
            observed_demand,
            available_inventory,
            safety_stock_units,
            reorder_point_units
        from {fact_demand}
        order by demand_date, store_id, dept_id
        """,
        config=config,
    )
    if df.empty:
        return df

    scored = df.rename(
        columns={
            "observed_demand": "predicted_demand",
            "available_inventory": "available_inventory",
        }
    )
    scored = score_stockout_risk_frame(scored, "predicted_demand", "available_inventory")
    return scored.rename(columns={"predicted_demand": "observed_demand"})


def fetch_baseline_forecast(config: AppConfig | None = None) -> pd.DataFrame:
    """Create a simple naive forecast view from observed sales for Phase 1.5."""
    fact_sales = qualified_table("MARTS", "FACT_SALES", config)
    df = run_query(
        f"""
        select
            store_id,
            dept_id,
            sales_date,
            weekly_sales
        from {fact_sales}
        order by store_id, dept_id, sales_date
        """,
        config=config,
    )
    if df.empty:
        return df

    df["baseline_forecast"] = df.groupby(["store_id", "dept_id"])["weekly_sales"].shift(1)
    group_average = df.groupby(["store_id", "dept_id"])["weekly_sales"].transform("mean")
    df["baseline_forecast"] = df["baseline_forecast"].fillna(group_average)
    df["forecast_error"] = df["weekly_sales"] - df["baseline_forecast"]
    df["absolute_error"] = df["forecast_error"].abs()
    return df


def fetch_forecast_results(config: AppConfig | None = None) -> pd.DataFrame:
    """Fetch Phase 2 forecast results, falling back to the Phase 1.5 baseline."""
    if object_exists("MARTS", "FACT_FORECAST", config):
        fact_forecast = qualified_table("MARTS", "FACT_FORECAST", config)
        return run_query(
            f"""
            select
                store_id,
                dept_id,
                forecast_date,
                horizon_days,
                predicted_demand,
                actual_demand,
                prediction_interval_lower,
                prediction_interval_upper,
                model_name,
                model_version,
                case
                    when actual_demand is null then null
                    else actual_demand - predicted_demand
                end as forecast_error,
                case
                    when actual_demand is null then null
                    else abs(actual_demand - predicted_demand)
                end as absolute_error
            from {fact_forecast}
            order by forecast_date, store_id, dept_id
            """,
            config=config,
        )

    baseline = fetch_baseline_forecast(config)
    if baseline.empty:
        return baseline

    return baseline.rename(
        columns={
            "sales_date": "forecast_date",
            "weekly_sales": "actual_demand",
            "baseline_forecast": "predicted_demand",
        }
    ).assign(
        horizon_days=0,
        prediction_interval_lower=lambda df: (df["predicted_demand"] * 0.85).clip(lower=0),
        prediction_interval_upper=lambda df: df["predicted_demand"] * 1.15,
        model_name="phase_1_5_naive_baseline",
        model_version="phase_1_5",
    )


def fetch_anomaly_candidates(config: AppConfig | None = None) -> pd.DataFrame:
    """Fetch sales rows and apply a simple z-score anomaly screen."""
    fact_sales = qualified_table("MARTS", "FACT_SALES", config)
    df = run_query(
        f"""
        select
            store_id,
            dept_id,
            sales_date,
            weekly_sales
        from {fact_sales}
        order by sales_date, store_id, dept_id
        """,
        config=config,
    )
    if df.empty:
        return df
    flagged = flag_zscore_anomalies(df, "weekly_sales", threshold=2.0)
    flagged["severity"] = flagged["anomaly_score"].abs().map(
        lambda score: "High" if score >= 3 else "Medium" if score >= 2 else "Low"
    )
    flagged["direction"] = flagged["anomaly_score"].map(lambda score: "Sales spike" if score > 0 else "Sales drop")
    return flagged.sort_values(["is_anomaly", "anomaly_score"], ascending=[False, False])


def fetch_stockout_risk_results(config: AppConfig | None = None) -> pd.DataFrame:
    """Fetch Phase 2 stockout risk output, falling back to observed-demand scoring."""
    if object_exists("MARTS", "FACT_STOCKOUT_RISK", config):
        fact_stockout = qualified_table("MARTS", "FACT_STOCKOUT_RISK", config)
        return run_query(
            f"""
            select
                store_id,
                dept_id,
                risk_date,
                predicted_demand,
                available_inventory,
                stockout_risk_score,
                risk_category,
                recommended_action,
                model_version
            from {fact_stockout}
            order by
                case risk_category
                    when 'Critical' then 1
                    when 'High' then 2
                    when 'Medium' then 3
                    else 4
                end,
                stockout_risk_score desc
            """,
            config=config,
        )

    demand = fetch_demand_detail(config)
    if demand.empty:
        return demand
    return demand.rename(
        columns={
            "demand_date": "risk_date",
            "observed_demand": "predicted_demand",
        }
    ).assign(model_version="observed_demand_proxy")


def fetch_anomaly_results(config: AppConfig | None = None) -> pd.DataFrame:
    """Fetch Phase 2 anomaly output, falling back to the Phase 1.5 z-score screen."""
    if object_exists("MARTS", "FACT_ANOMALIES", config):
        fact_anomalies = qualified_table("MARTS", "FACT_ANOMALIES", config)
        return run_query(
            f"""
            select
                store_id,
                dept_id,
                sales_date,
                weekly_sales,
                anomaly_score,
                is_anomaly,
                severity,
                direction,
                model_version
            from {fact_anomalies}
            order by is_anomaly desc, abs(anomaly_score) desc, sales_date
            """,
            config=config,
        )

    return fetch_anomaly_candidates(config)


def fetch_quality_checks(config: AppConfig | None = None) -> pd.DataFrame:
    """Create a lightweight data quality status table from Snowflake metadata."""
    database = _database(config)
    return run_query(
        f"""
        with object_health as (
            select
                table_schema,
                table_name,
                table_type,
                coalesce(row_count, 0) as row_count,
                last_altered
            from {database}.information_schema.tables
            where table_schema in ('RAW', 'MARTS', 'ML')
        )
        select
            table_schema || '.' || table_name as object_name,
            table_type,
            row_count,
            case
                when table_type = 'BASE TABLE' and row_count > 0 then 'Pass'
                when table_type = 'VIEW' then 'Pass'
                else 'Review'
            end as status,
            last_altered
        from object_health
        order by table_schema, table_name
        """,
        config=config,
    )
