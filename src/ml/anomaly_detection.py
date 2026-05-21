"""Baseline anomaly detection utilities for sales monitoring."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from src.ml.feature_engineering import normalize_columns


def flag_zscore_anomalies(df: pd.DataFrame, value_column: str, threshold: float = 3.0) -> pd.DataFrame:
    """Flag simple z-score anomalies as a Phase 1 utility."""
    output = df.copy()
    mean_value = output[value_column].mean()
    std_value = output[value_column].std(ddof=0)
    if std_value == 0 or pd.isna(std_value):
        output["anomaly_score"] = 0.0
        output["is_anomaly"] = False
        return output

    output["anomaly_score"] = (output[value_column] - mean_value) / std_value
    output["is_anomaly"] = output["anomaly_score"].abs() >= threshold
    return output


def detect_sales_anomalies(sales: pd.DataFrame, threshold: float = 2.0) -> pd.DataFrame:
    """Detect z-score sales anomalies within each store and department."""
    sales = normalize_columns(sales)
    required = {"STORE", "DEPT", "DATE", "WEEKLY_SALES"}
    missing = sorted(required - set(sales.columns))
    if missing:
        raise ValueError(f"Sales data is missing required columns for anomaly detection: {', '.join(missing)}")

    sales = sales[["STORE", "DEPT", "DATE", "WEEKLY_SALES"]].copy()
    sales["DATE"] = pd.to_datetime(sales["DATE"], errors="coerce").dt.date
    sales["WEEKLY_SALES"] = pd.to_numeric(sales["WEEKLY_SALES"], errors="coerce")

    scored_frames: list[pd.DataFrame] = []
    for _, group in sales.groupby(["STORE", "DEPT"], dropna=False):
        scored_frames.append(flag_zscore_anomalies(group, "WEEKLY_SALES", threshold=threshold))

    scored = pd.concat(scored_frames, ignore_index=True)
    scored["severity"] = scored["anomaly_score"].abs().map(
        lambda score: "High" if score >= 3 else "Medium" if score >= threshold else "Low"
    )
    scored["direction"] = scored["anomaly_score"].map(lambda score: "Sales spike" if score > 0 else "Sales drop")
    return scored


def build_sales_anomaly_output(sales_path: str | Path, threshold: float = 2.0) -> pd.DataFrame:
    """Build the canonical ML.SALES_ANOMALIES CSV output."""
    sales = pd.read_csv(sales_path)
    scored = detect_sales_anomalies(sales, threshold=threshold)
    created_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    output = pd.DataFrame(
        {
            "Store": scored["STORE"].astype(int),
            "Dept": scored["DEPT"].astype(int),
            "Sales_Date": scored["DATE"],
            "Weekly_Sales": scored["WEEKLY_SALES"].round(2),
            "Anomaly_Score": scored["anomaly_score"].round(4),
            "Is_Anomaly": scored["is_anomaly"],
            "Severity": scored["severity"],
            "Direction": scored["direction"],
            "Model_Version": "zscore_baseline_v1",
            "Created_At": created_at,
        }
    )
    return output[
        [
            "Store",
            "Dept",
            "Sales_Date",
            "Weekly_Sales",
            "Anomaly_Score",
            "Is_Anomaly",
            "Severity",
            "Direction",
            "Model_Version",
            "Created_At",
        ]
    ]
