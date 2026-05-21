"""Baseline anomaly detection utilities for future sales monitoring."""

from __future__ import annotations

import pandas as pd


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

