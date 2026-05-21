from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FORECAST_OUTPUT_COLUMNS = {
    "store_id",
    "dept_id",
    "forecast_date",
    "predicted_demand",
    "prediction_interval_lower",
    "prediction_interval_upper",
    "model_version",
}


def test_expected_forecast_output_contract_is_documented() -> None:
    methodology = (PROJECT_ROOT / "docs/model_methodology.md").read_text(encoding="utf-8").lower()

    for column_name in EXPECTED_FORECAST_OUTPUT_COLUMNS:
        assert column_name in methodology


def test_forecasting_notebook_placeholder_exists() -> None:
    assert (PROJECT_ROOT / "notebooks/02_forecasting_baseline.ipynb").exists()

