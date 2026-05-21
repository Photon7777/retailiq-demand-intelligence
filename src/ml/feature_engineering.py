"""Feature engineering placeholders for future RetailIQ forecasting models."""

from __future__ import annotations

import pandas as pd


def add_calendar_features(df: pd.DataFrame, date_column: str = "date") -> pd.DataFrame:
    """Add basic calendar features used by demand forecasting models."""
    features = df.copy()
    date_values = pd.to_datetime(features[date_column])
    features["year"] = date_values.dt.year
    features["month"] = date_values.dt.month
    features["week_of_year"] = date_values.dt.isocalendar().week.astype(int)
    features["day_of_year"] = date_values.dt.dayofyear
    return features

