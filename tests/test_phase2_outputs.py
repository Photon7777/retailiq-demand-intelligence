from __future__ import annotations

import pandas as pd

from src.ml.anomaly_detection import build_sales_anomaly_output
from src.ml.generate_predictions import FORECAST_OUTPUT_COLUMNS, STOCKOUT_OUTPUT_COLUMNS
from src.ml.synthetic_inventory import generate_synthetic_inventory, generate_synthetic_weather


def test_synthetic_inventory_matches_sales_grain() -> None:
    sales = pd.DataFrame(
        {
            "Store": [1, 1],
            "Dept": [1, 2],
            "Date": ["2012-01-06", "2012-01-06"],
            "Weekly_Sales": [1000.0, 2000.0],
            "IsHoliday": [False, False],
        }
    )

    inventory = generate_synthetic_inventory(sales, random_seed=7)

    assert len(inventory) == len(sales)
    assert {"Available_Inventory", "Safety_Stock_Units", "Reorder_Point_Units"}.issubset(inventory.columns)
    assert (inventory["Available_Inventory"] > 0).all()


def test_synthetic_weather_uses_feature_dates() -> None:
    features = pd.DataFrame(
        {
            "Store": [1],
            "Date": ["2012-01-06"],
            "Temperature": [31.0],
        }
    )

    weather = generate_synthetic_weather(features, random_seed=7)

    assert weather.loc[0, "Store"] == 1
    assert {"Temperature", "Precipitation", "Snowfall"}.issubset(weather.columns)


def test_anomaly_output_contract(tmp_path) -> None:
    sales = pd.DataFrame(
        {
            "Store": [1, 1, 1, 1],
            "Dept": [1, 1, 1, 1],
            "Date": ["2012-01-06", "2012-01-13", "2012-01-20", "2012-01-27"],
            "Weekly_Sales": [100.0, 105.0, 98.0, 500.0],
        }
    )
    path = tmp_path / "sales.csv"
    sales.to_csv(path, index=False)

    output = build_sales_anomaly_output(path, threshold=1.5)

    assert {"Store", "Dept", "Sales_Date", "Anomaly_Score", "Is_Anomaly", "Severity", "Direction"}.issubset(output.columns)
    assert output["Is_Anomaly"].any()


def test_phase2_output_column_contracts_are_explicit() -> None:
    assert "Prediction_Interval_Lower" in FORECAST_OUTPUT_COLUMNS
    assert "Prediction_Interval_Upper" in FORECAST_OUTPUT_COLUMNS
    assert "Risk_Category" in STOCKOUT_OUTPUT_COLUMNS
