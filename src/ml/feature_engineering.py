"""Feature engineering utilities for RetailIQ forecasting models."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


TARGET_COLUMN = "WEEKLY_SALES"

MODEL_FEATURE_COLUMNS = [
    "STORE",
    "DEPT",
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
    "STORE_TYPE",
    "SIZE",
    "YEAR",
    "MONTH",
    "WEEK_OF_YEAR",
    "DAY_OF_YEAR",
]


def add_calendar_features(df: pd.DataFrame, date_column: str = "DATE") -> pd.DataFrame:
    """Add basic calendar features used by demand forecasting models."""
    features = df.copy()
    date_values = pd.to_datetime(features[date_column])
    features["YEAR"] = date_values.dt.year
    features["MONTH"] = date_values.dt.month
    features["WEEK_OF_YEAR"] = date_values.dt.isocalendar().week.astype(int)
    features["DAY_OF_YEAR"] = date_values.dt.dayofyear
    return features


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize common Walmart/RetailIQ CSV columns to uppercase snake-style names."""
    normalized = df.copy()
    normalized.columns = [column.strip().replace("_", "").upper() for column in normalized.columns]
    rename_map = {
        "WEEKLYSALES": "WEEKLY_SALES",
        "ISHOLIDAY": "IS_HOLIDAY",
        "FUELPRICE": "FUEL_PRICE",
        "MARKDOWN1": "MARKDOWN1",
        "MARKDOWN2": "MARKDOWN2",
        "MARKDOWN3": "MARKDOWN3",
        "MARKDOWN4": "MARKDOWN4",
        "MARKDOWN5": "MARKDOWN5",
        "TYPE": "STORE_TYPE",
        "STORETYPE": "STORE_TYPE",
    }
    normalized = normalized.rename(columns=rename_map)
    return normalized


def load_retailiq_data(data_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load canonical RetailIQ sales, store, and feature files from a local directory."""
    data_path = Path(data_dir)
    sales = normalize_columns(pd.read_csv(data_path / "sales.csv"))
    stores = normalize_columns(pd.read_csv(data_path / "stores.csv"))
    features = normalize_columns(pd.read_csv(data_path / "features.csv"))
    return sales, stores, features


def build_training_frame(
    sales: pd.DataFrame,
    stores: pd.DataFrame,
    features: pd.DataFrame,
) -> pd.DataFrame:
    """Join source files and create a model-ready training frame."""
    sales = normalize_columns(sales)
    stores = normalize_columns(stores)
    features = normalize_columns(features)

    for frame in (sales, features):
        frame["DATE"] = pd.to_datetime(frame["DATE"], errors="coerce")

    markdown_columns = ["MARKDOWN1", "MARKDOWN2", "MARKDOWN3", "MARKDOWN4", "MARKDOWN5"]
    for column in markdown_columns:
        if column not in features.columns:
            features[column] = 0.0
    for column in ["TEMPERATURE", "FUEL_PRICE", "CPI", "UNEMPLOYMENT"]:
        if column not in features.columns:
            features[column] = np.nan

    if "STORE_TYPE" not in stores.columns and "TYPE" in stores.columns:
        stores = stores.rename(columns={"TYPE": "STORE_TYPE"})

    frame = sales.merge(features, on=["STORE", "DATE"], how="left", suffixes=("", "_FEATURE"))
    frame = frame.merge(stores[["STORE", "STORE_TYPE", "SIZE"]], on="STORE", how="left")

    if "IS_HOLIDAY_FEATURE" in frame.columns:
        frame["IS_HOLIDAY"] = frame["IS_HOLIDAY"].fillna(frame["IS_HOLIDAY_FEATURE"])
    frame["IS_HOLIDAY"] = frame["IS_HOLIDAY"].astype(str).str.lower().isin(["true", "1", "yes"])

    frame = add_calendar_features(frame, "DATE")
    frame[TARGET_COLUMN] = pd.to_numeric(frame[TARGET_COLUMN], errors="coerce")
    frame = frame.dropna(subset=["STORE", "DEPT", "DATE", TARGET_COLUMN])

    for column in MODEL_FEATURE_COLUMNS:
        if column not in frame.columns:
            frame[column] = np.nan

    return frame[["DATE", TARGET_COLUMN, *MODEL_FEATURE_COLUMNS]].sort_values("DATE").reset_index(drop=True)
