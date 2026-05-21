"""Load RetailIQ ML output CSV files into Snowflake ML tables."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from getpass import getpass
import logging
from pathlib import Path

import pandas as pd
from snowflake.connector.pandas_tools import write_pandas

from src.ingestion.load_to_snowflake import normalize_column_name
from src.utils.config import get_config
from src.utils.snowflake_connection import snowflake_connection


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MLOutputConfig:
    file_name: str
    table_name: str
    expected_columns: tuple[str, ...]
    date_columns: tuple[str, ...] = ()
    timestamp_columns: tuple[str, ...] = ("CREATED_AT",)


ML_OUTPUT_CONFIG: dict[str, MLOutputConfig] = {
    "demand_forecasts.csv": MLOutputConfig(
        file_name="demand_forecasts.csv",
        table_name="DEMAND_FORECASTS",
        expected_columns=(
            "STORE",
            "DEPT",
            "FORECAST_DATE",
            "HORIZON_DAYS",
            "PREDICTED_DEMAND",
            "ACTUAL_DEMAND",
            "PREDICTION_INTERVAL_LOWER",
            "PREDICTION_INTERVAL_UPPER",
            "MODEL_NAME",
            "MODEL_VERSION",
            "TRAINED_AT",
            "CREATED_AT",
        ),
        date_columns=("FORECAST_DATE",),
        timestamp_columns=("TRAINED_AT", "CREATED_AT"),
    ),
    "stockout_risk.csv": MLOutputConfig(
        file_name="stockout_risk.csv",
        table_name="STOCKOUT_RISK",
        expected_columns=(
            "STORE",
            "DEPT",
            "RISK_DATE",
            "PREDICTED_DEMAND",
            "AVAILABLE_INVENTORY",
            "STOCKOUT_RISK_SCORE",
            "RISK_CATEGORY",
            "RECOMMENDED_ACTION",
            "MODEL_VERSION",
            "CREATED_AT",
        ),
        date_columns=("RISK_DATE",),
    ),
    "sales_anomalies.csv": MLOutputConfig(
        file_name="sales_anomalies.csv",
        table_name="SALES_ANOMALIES",
        expected_columns=(
            "STORE",
            "DEPT",
            "SALES_DATE",
            "WEEKLY_SALES",
            "ANOMALY_SCORE",
            "IS_ANOMALY",
            "SEVERITY",
            "DIRECTION",
            "MODEL_VERSION",
            "CREATED_AT",
        ),
        date_columns=("SALES_DATE",),
    ),
}


ML_TABLE_DDL = {
    "DEMAND_FORECASTS": """
        CREATE TABLE IF NOT EXISTS {database}.ML.DEMAND_FORECASTS (
          STORE NUMBER,
          DEPT NUMBER,
          FORECAST_DATE DATE,
          HORIZON_DAYS NUMBER,
          PREDICTED_DEMAND FLOAT,
          ACTUAL_DEMAND FLOAT,
          PREDICTION_INTERVAL_LOWER FLOAT,
          PREDICTION_INTERVAL_UPPER FLOAT,
          MODEL_NAME VARCHAR,
          MODEL_VERSION VARCHAR,
          TRAINED_AT TIMESTAMP_NTZ,
          CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        )
    """,
    "STOCKOUT_RISK": """
        CREATE TABLE IF NOT EXISTS {database}.ML.STOCKOUT_RISK (
          STORE NUMBER,
          DEPT NUMBER,
          RISK_DATE DATE,
          PREDICTED_DEMAND FLOAT,
          AVAILABLE_INVENTORY FLOAT,
          STOCKOUT_RISK_SCORE FLOAT,
          RISK_CATEGORY VARCHAR,
          RECOMMENDED_ACTION VARCHAR,
          MODEL_VERSION VARCHAR,
          CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        )
    """,
    "SALES_ANOMALIES": """
        CREATE TABLE IF NOT EXISTS {database}.ML.SALES_ANOMALIES (
          STORE NUMBER,
          DEPT NUMBER,
          SALES_DATE DATE,
          WEEKLY_SALES FLOAT,
          ANOMALY_SCORE FLOAT,
          IS_ANOMALY BOOLEAN,
          SEVERITY VARCHAR,
          DIRECTION VARCHAR,
          MODEL_VERSION VARCHAR,
          CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        )
    """,
}


def read_ml_output(file_path: Path, output_config: MLOutputConfig) -> pd.DataFrame:
    """Read and type an ML output CSV for Snowflake loading."""
    if not file_path.exists():
        raise FileNotFoundError(f"Missing expected ML output file: {file_path}")

    df = pd.read_csv(file_path)
    df.columns = [normalize_column_name(column) for column in df.columns]
    missing_columns = [column for column in output_config.expected_columns if column not in df.columns]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"{file_path.name} is missing required columns for {output_config.table_name}: {missing}")

    df = df.loc[:, list(output_config.expected_columns)].copy()
    for column in output_config.date_columns:
        df[column] = pd.to_datetime(df[column], errors="coerce").dt.date
    for column in output_config.timestamp_columns:
        df[column] = pd.to_datetime(df[column], errors="coerce").dt.tz_localize(None)
    for column in df.columns:
        if column in {*output_config.date_columns, *output_config.timestamp_columns}:
            continue
        if column in {"MODEL_NAME", "MODEL_VERSION", "RISK_CATEGORY", "RECOMMENDED_ACTION", "SEVERITY", "DIRECTION"}:
            continue
        if column == "IS_ANOMALY":
            df[column] = df[column].astype(str).str.lower().isin(["true", "1", "yes"])
            continue
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def ensure_ml_tables(connection, database: str) -> None:
    """Create the Snowflake ML schema and output tables if they do not exist."""
    with connection.cursor() as cursor:
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {database}.ML")
        for table_name, ddl in ML_TABLE_DDL.items():
            logger.info("Ensuring ML.%s exists", table_name)
            cursor.execute(ddl.format(database=database))


def truncate_table(connection, database: str, schema: str, table_name: str) -> None:
    """Remove existing rows from a Snowflake ML output table."""
    with connection.cursor() as cursor:
        cursor.execute(f"TRUNCATE TABLE {database}.{schema}.{table_name}")


def load_ml_outputs(
    output_dir: Path,
    files_to_load: list[str] | None = None,
    snowflake_passcode: str | None = None,
    truncate_first: bool = False,
) -> None:
    """Load local ML output CSV files into Snowflake's ML schema."""
    requested_files = files_to_load or list(ML_OUTPUT_CONFIG)
    config = get_config()
    if snowflake_passcode:
        config = replace(config, snowflake_passcode=snowflake_passcode)

    with snowflake_connection(config) as connection:
        ensure_ml_tables(connection, config.snowflake_database)
        for file_name in requested_files:
            if file_name not in ML_OUTPUT_CONFIG:
                supported = ", ".join(ML_OUTPUT_CONFIG)
                raise ValueError(f"Unsupported ML output '{file_name}'. Supported files: {supported}")

            output_config = ML_OUTPUT_CONFIG[file_name]
            file_path = output_dir / file_name
            logger.info("Preparing %s for ML.%s", file_name, output_config.table_name)
            df = read_ml_output(file_path, output_config)
            if truncate_first:
                logger.info("Truncating ML.%s before load", output_config.table_name)
                truncate_table(connection, config.snowflake_database, "ML", output_config.table_name)
            success, _chunks, row_count, output = write_pandas(
                conn=connection,
                df=df,
                table_name=output_config.table_name,
                database=config.snowflake_database,
                schema="ML",
                quote_identifiers=True,
                auto_create_table=False,
                overwrite=False,
            )
            if not success:
                raise RuntimeError(f"Snowflake load failed for ML.{output_config.table_name}: {output}")
            logger.info("Loaded %s rows into ML.%s", row_count, output_config.table_name)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load RetailIQ ML output CSV files into Snowflake.")
    parser.add_argument("--output-dir", type=Path, default=Path("data/ml_outputs"))
    parser.add_argument("--only", nargs="+", choices=sorted(ML_OUTPUT_CONFIG))
    parser.add_argument("--snowflake-passcode")
    parser.add_argument("--prompt-passcode", action="store_true")
    parser.add_argument("--truncate-first", action="store_true")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    args = parse_args()
    passcode = args.snowflake_passcode
    if args.prompt_passcode:
        passcode = getpass("Snowflake MFA code: ")
    load_ml_outputs(
        output_dir=args.output_dir,
        files_to_load=args.only,
        snowflake_passcode=passcode,
        truncate_first=args.truncate_first,
    )


if __name__ == "__main__":
    main()
