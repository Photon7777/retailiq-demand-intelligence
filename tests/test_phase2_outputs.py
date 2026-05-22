from __future__ import annotations

import pandas as pd

from src.ml.anomaly_detection import build_sales_anomaly_output
from src.ingestion.load_ml_outputs_to_snowflake import ML_OUTPUT_CONFIG, ML_TABLE_DDL, read_ml_output
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


def test_ml_loader_can_create_required_output_tables() -> None:
    assert {"DEMAND_FORECASTS", "STOCKOUT_RISK", "SALES_ANOMALIES"} == set(ML_TABLE_DDL)
    assert "CREATE TABLE IF NOT EXISTS {database}.ML.DEMAND_FORECASTS" in ML_TABLE_DDL["DEMAND_FORECASTS"]


def test_ml_loader_formats_timestamps_for_snowflake_copy(tmp_path) -> None:
    path = tmp_path / "demand_forecasts.csv"
    pd.DataFrame(
        {
            "Store": [1],
            "Dept": [1],
            "Forecast_Date": ["2012-01-13"],
            "Horizon_Days": [7],
            "Predicted_Demand": [123.45],
            "Actual_Demand": [None],
            "Prediction_Interval_Lower": [100.0],
            "Prediction_Interval_Upper": [150.0],
            "Model_Name": ["baseline"],
            "Model_Version": ["v1"],
            "Trained_At": ["2026-05-21T23:18:11+00:00"],
            "Created_At": ["2026-05-21T23:20:00+00:00"],
        }
    ).to_csv(path, index=False)

    output = read_ml_output(path, ML_OUTPUT_CONFIG["demand_forecasts.csv"])

    assert output.loc[0, "TRAINED_AT"] == "2026-05-21 23:18:11"
    assert output.loc[0, "CREATED_AT"] == "2026-05-21 23:20:00"
