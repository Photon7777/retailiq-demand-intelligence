"""Load local RetailIQ sample CSV files into Snowflake RAW tables."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from getpass import getpass
import logging
import re
from pathlib import Path

import pandas as pd
from snowflake.connector.pandas_tools import write_pandas

from src.utils.config import get_config
from src.utils.snowflake_connection import snowflake_connection


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TableLoadConfig:
    file_name: str
    table_name: str
    expected_columns: tuple[str, ...]
    date_columns: tuple[str, ...] = ("DATE",)


TABLE_LOAD_CONFIG: dict[str, TableLoadConfig] = {
    "sales.csv": TableLoadConfig(
        file_name="sales.csv",
        table_name="SALES",
        expected_columns=("STORE", "DEPT", "DATE", "WEEKLY_SALES", "IS_HOLIDAY"),
    ),
    "stores.csv": TableLoadConfig(
        file_name="stores.csv",
        table_name="STORES",
        expected_columns=("STORE", "STORE_TYPE", "SIZE"),
        date_columns=(),
    ),
    "features.csv": TableLoadConfig(
        file_name="features.csv",
        table_name="FEATURES",
        expected_columns=(
            "STORE",
            "DATE",
            "TEMPERATURE",
            "FUEL_PRICE",
            "MARKDOWN1",
            "MARKDOWN2",
            "MARKDOWN3",
            "MARKDOWN4",
            "MARKDOWN5",
            "CPI",
            "UNEMPLOYMENT",
            "IS_HOLIDAY",
        ),
    ),
    "inventory.csv": TableLoadConfig(
        file_name="inventory.csv",
        table_name="INVENTORY",
        expected_columns=(
            "STORE",
            "DEPT",
            "DATE",
            "SKU",
            "AVAILABLE_INVENTORY",
            "SAFETY_STOCK_UNITS",
            "REORDER_POINT_UNITS",
        ),
    ),
    "weather.csv": TableLoadConfig(
        file_name="weather.csv",
        table_name="WEATHER",
        expected_columns=("STORE", "DATE", "TEMPERATURE", "PRECIPITATION", "SNOWFALL"),
    ),
}

COLUMN_ALIASES = {
    "TYPE": "STORE_TYPE",
    "FUEL_PRICE": "FUEL_PRICE",
    "WEEKLY_SALES": "WEEKLY_SALES",
    "ISHOLIDAY": "IS_HOLIDAY",
    "IS_HOLIDAY": "IS_HOLIDAY",
    "MARKDOWN_1": "MARKDOWN1",
    "MARKDOWN_2": "MARKDOWN2",
    "MARKDOWN_3": "MARKDOWN3",
    "MARKDOWN_4": "MARKDOWN4",
    "MARKDOWN_5": "MARKDOWN5",
}


def normalize_column_name(column_name: str) -> str:
    """Normalize CSV column names to Snowflake-friendly uppercase names."""
    normalized = re.sub(r"[^0-9A-Za-z]+", "_", column_name.strip()).strip("_").upper()
    return COLUMN_ALIASES.get(normalized, normalized)


def read_and_prepare_csv(file_path: Path, table_config: TableLoadConfig) -> pd.DataFrame:
    """Read a CSV file and align its columns to the target Snowflake table."""
    if not file_path.exists():
        raise FileNotFoundError(f"Missing expected file: {file_path}")

    df = pd.read_csv(file_path)
    df.columns = [normalize_column_name(column) for column in df.columns]

    missing_columns = [column for column in table_config.expected_columns if column not in df.columns]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"{file_path.name} is missing required columns for {table_config.table_name}: {missing}")

    df = df.loc[:, list(table_config.expected_columns)].copy()
    for column in table_config.date_columns:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce").dt.date

    df["SOURCE_FILE"] = file_path.name
    df["LOADED_AT"] = pd.Timestamp.utcnow().tz_localize(None)
    return df


def validate_sample_files(sample_dir: Path, files_to_load: list[str] | None = None) -> list[Path]:
    """Validate expected files exist before opening a Snowflake connection."""
    requested_files = files_to_load or list(TABLE_LOAD_CONFIG)
    paths: list[Path] = []
    for file_name in requested_files:
        if file_name not in TABLE_LOAD_CONFIG:
            supported = ", ".join(TABLE_LOAD_CONFIG)
            raise ValueError(f"Unsupported file '{file_name}'. Supported files: {supported}")

        file_path = sample_dir / file_name
        if not file_path.exists():
            raise FileNotFoundError(f"Missing expected sample file: {file_path}")
        paths.append(file_path)
    return paths


def load_dataframe_to_snowflake(connection, df: pd.DataFrame, table_config: TableLoadConfig, database: str, schema: str) -> int:
    """Append a prepared DataFrame to a Snowflake RAW table."""
    success, _num_chunks, num_rows, output = write_pandas(
        conn=connection,
        df=df,
        table_name=table_config.table_name,
        database=database,
        schema=schema,
        quote_identifiers=True,
        auto_create_table=False,
        overwrite=False,
    )
    if not success:
        raise RuntimeError(f"Snowflake load failed for {table_config.table_name}: {output}")
    return num_rows


def truncate_table(connection, database: str, schema: str, table_name: str) -> None:
    """Remove existing rows from a target table before a repeatable smoke-test load."""
    qualified_table = f"{database}.{schema}.{table_name}"
    with connection.cursor() as cursor:
        cursor.execute(f"TRUNCATE TABLE {qualified_table}")


def load_sample_files(
    sample_dir: Path,
    files_to_load: list[str] | None = None,
    snowflake_passcode: str | None = None,
    truncate_first: bool = False,
) -> None:
    """Load expected local CSV files from `data/sample/` into Snowflake RAW tables."""
    sample_dir = sample_dir.resolve()
    file_paths = validate_sample_files(sample_dir, files_to_load)
    config = get_config()
    if snowflake_passcode:
        config = replace(config, snowflake_passcode=snowflake_passcode)
    target_schema = config.snowflake_schema or "RAW"

    logger.info("Validated %s file(s) in %s", len(file_paths), sample_dir)
    with snowflake_connection(config) as connection:
        for file_path in file_paths:
            table_config = TABLE_LOAD_CONFIG[file_path.name]
            logger.info("Preparing %s for RAW.%s", file_path.name, table_config.table_name)
            df = read_and_prepare_csv(file_path, table_config)
            if truncate_first:
                logger.info("Truncating %s.%s before load", target_schema, table_config.table_name)
                truncate_table(connection, config.snowflake_database, target_schema, table_config.table_name)
            row_count = load_dataframe_to_snowflake(
                connection=connection,
                df=df,
                table_config=table_config,
                database=config.snowflake_database,
                schema=target_schema,
            )
            logger.info("Loaded %s rows into %s.%s", row_count, target_schema, table_config.table_name)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load RetailIQ sample CSV files into Snowflake RAW tables.")
    parser.add_argument("--sample-dir", type=Path, default=Path("data/sample"))
    parser.add_argument(
        "--only",
        nargs="+",
        choices=sorted(TABLE_LOAD_CONFIG),
        help="Optional subset of files to load, such as sales.csv stores.csv.",
    )
    parser.add_argument(
        "--snowflake-passcode",
        help="Current Snowflake MFA/TOTP passcode. Prefer --prompt-passcode so the code is not saved in shell history.",
    )
    parser.add_argument(
        "--prompt-passcode",
        action="store_true",
        help="Prompt securely for the current Snowflake MFA/TOTP passcode before connecting.",
    )
    parser.add_argument(
        "--truncate-first",
        action="store_true",
        help="Truncate target RAW tables before loading so smoke tests are repeatable.",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    args = parse_args()
    passcode = args.snowflake_passcode
    if args.prompt_passcode:
        passcode = getpass("Snowflake MFA code: ")
    load_sample_files(
        sample_dir=args.sample_dir,
        files_to_load=args.only,
        snowflake_passcode=passcode,
        truncate_first=args.truncate_first,
    )


if __name__ == "__main__":
    main()
