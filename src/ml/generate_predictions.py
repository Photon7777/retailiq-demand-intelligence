"""Generate Phase 2 forecast, stockout risk, and anomaly output files."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
import pickle

import pandas as pd

from src.ml.anomaly_detection import build_sales_anomaly_output
from src.ml.feature_engineering import MODEL_FEATURE_COLUMNS, TARGET_COLUMN, build_training_frame, load_retailiq_data
from src.ml.stockout_risk import score_stockout_risk_frame


FORECAST_OUTPUT_COLUMNS = [
    "Store",
    "Dept",
    "Forecast_Date",
    "Horizon_Days",
    "Predicted_Demand",
    "Actual_Demand",
    "Prediction_Interval_Lower",
    "Prediction_Interval_Upper",
    "Model_Name",
    "Model_Version",
    "Trained_At",
    "Created_At",
]

STOCKOUT_OUTPUT_COLUMNS = [
    "Store",
    "Dept",
    "Risk_Date",
    "Predicted_Demand",
    "Available_Inventory",
    "Stockout_Risk_Score",
    "Risk_Category",
    "Recommended_Action",
    "Model_Version",
    "Created_At",
]


def _load_model(model_path: str | Path) -> dict[str, object]:
    with Path(model_path).open("rb") as file:
        return pickle.load(file)


def _add_prediction_intervals(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    output["Prediction_Interval_Lower"] = (output["Predicted_Demand"] * 0.85).clip(lower=0).round(2)
    output["Prediction_Interval_Upper"] = (output["Predicted_Demand"] * 1.15).round(2)
    return output


def _next_week_rows(frame: pd.DataFrame) -> pd.DataFrame:
    latest = frame.sort_values("DATE").groupby(["STORE", "DEPT"], as_index=False).tail(1).copy()
    latest["DATE"] = pd.to_datetime(latest["DATE"]) + pd.Timedelta(days=7)
    latest["YEAR"] = latest["DATE"].dt.year
    latest["MONTH"] = latest["DATE"].dt.month
    latest["WEEK_OF_YEAR"] = latest["DATE"].dt.isocalendar().week.astype(int)
    latest["DAY_OF_YEAR"] = latest["DATE"].dt.dayofyear
    return latest


def build_forecast_output(data_dir: str | Path, model_path: str | Path) -> pd.DataFrame:
    """Score observed rows and one next-week row per store/department."""
    artifact = _load_model(model_path)
    pipeline = artifact["pipeline"]
    sales, stores, features = load_retailiq_data(data_dir)
    frame = build_training_frame(sales, stores, features)

    observed = frame.copy()
    observed_predictions = pipeline.predict(observed[MODEL_FEATURE_COLUMNS])
    observed_output = pd.DataFrame(
        {
            "Store": observed["STORE"].astype(int),
            "Dept": observed["DEPT"].astype(int),
            "Forecast_Date": pd.to_datetime(observed["DATE"]).dt.date,
            "Horizon_Days": 0,
            "Predicted_Demand": observed_predictions.round(2),
            "Actual_Demand": observed[TARGET_COLUMN].round(2),
        }
    )

    future = _next_week_rows(frame)
    future_predictions = pipeline.predict(future[MODEL_FEATURE_COLUMNS])
    future_output = pd.DataFrame(
        {
            "Store": future["STORE"].astype(int),
            "Dept": future["DEPT"].astype(int),
            "Forecast_Date": pd.to_datetime(future["DATE"]).dt.date,
            "Horizon_Days": 7,
            "Predicted_Demand": future_predictions.round(2),
            "Actual_Demand": [float("nan")] * len(future),
        }
    )

    created_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    forecast = pd.concat([observed_output, future_output], ignore_index=True)
    forecast = _add_prediction_intervals(forecast)
    forecast["Model_Name"] = artifact["model_name"]
    forecast["Model_Version"] = artifact["model_version"]
    forecast["Trained_At"] = artifact["trained_at"]
    forecast["Created_At"] = created_at
    return forecast[FORECAST_OUTPUT_COLUMNS]


def build_stockout_output(data_dir: str | Path, forecast: pd.DataFrame) -> pd.DataFrame:
    """Score stockout risk by joining historical forecasts to inventory snapshots."""
    inventory_path = Path(data_dir) / "inventory.csv"
    if not inventory_path.exists():
        return pd.DataFrame(columns=STOCKOUT_OUTPUT_COLUMNS)

    inventory = pd.read_csv(inventory_path)
    inventory.columns = [column.strip().replace("_", "").upper() for column in inventory.columns]
    inventory = inventory.rename(
        columns={
            "AVAILABLEINVENTORY": "AVAILABLE_INVENTORY",
            "SAFETYSTOCKUNITS": "SAFETY_STOCK_UNITS",
            "REORDERPOINTUNITS": "REORDER_POINT_UNITS",
        }
    )
    inventory["DATE"] = pd.to_datetime(inventory["DATE"], errors="coerce").dt.date

    historical_forecast = forecast[forecast["Horizon_Days"] == 0].copy()
    historical_forecast["Forecast_Date"] = pd.to_datetime(historical_forecast["Forecast_Date"], errors="coerce").dt.date
    joined = historical_forecast.merge(
        inventory[["STORE", "DEPT", "DATE", "AVAILABLE_INVENTORY"]],
        left_on=["Store", "Dept", "Forecast_Date"],
        right_on=["STORE", "DEPT", "DATE"],
        how="inner",
    )
    if joined.empty:
        return pd.DataFrame(columns=STOCKOUT_OUTPUT_COLUMNS)

    scored = joined.rename(
        columns={
            "Predicted_Demand": "predicted_demand",
            "AVAILABLE_INVENTORY": "available_inventory",
        }
    )
    scored = score_stockout_risk_frame(scored, "predicted_demand", "available_inventory")
    output = pd.DataFrame(
        {
            "Store": scored["Store"].astype(int),
            "Dept": scored["Dept"].astype(int),
            "Risk_Date": scored["Forecast_Date"],
            "Predicted_Demand": scored["predicted_demand"].round(2),
            "Available_Inventory": scored["available_inventory"].round(2),
            "Stockout_Risk_Score": scored["stockout_risk_score"].round(4),
            "Risk_Category": scored["risk_category"],
            "Recommended_Action": scored["recommended_action"],
            "Model_Version": scored["Model_Version"],
            "Created_At": scored["Created_At"],
        }
    )
    return output[STOCKOUT_OUTPUT_COLUMNS]


def generate_ml_outputs(
    data_dir: str | Path = "data/sample",
    model_path: str | Path = "models/retailiq_forecast_model.pkl",
    output_dir: str | Path = "data/ml_outputs",
) -> dict[str, Path]:
    """Generate all Phase 2 local ML output CSVs."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    forecast = build_forecast_output(data_dir, model_path)
    stockout = build_stockout_output(data_dir, forecast)
    anomalies = build_sales_anomaly_output(Path(data_dir) / "sales.csv")

    outputs = {
        "demand_forecasts": output_path / "demand_forecasts.csv",
        "stockout_risk": output_path / "stockout_risk.csv",
        "sales_anomalies": output_path / "sales_anomalies.csv",
    }
    forecast.to_csv(outputs["demand_forecasts"], index=False)
    stockout.to_csv(outputs["stockout_risk"], index=False)
    anomalies.to_csv(outputs["sales_anomalies"], index=False)
    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate RetailIQ Phase 2 ML output CSV files.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/sample"))
    parser.add_argument("--model-path", type=Path, default=Path("models/retailiq_forecast_model.pkl"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/ml_outputs"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outputs = generate_ml_outputs(args.data_dir, args.model_path, args.output_dir)
    for name, path in outputs.items():
        print(f"Wrote {name}: {path}")


if __name__ == "__main__":
    main()
