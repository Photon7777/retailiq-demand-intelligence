"""Train the Phase 2 baseline RetailIQ demand forecast model."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import pickle

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.ml.feature_engineering import MODEL_FEATURE_COLUMNS, TARGET_COLUMN, build_training_frame, load_retailiq_data


MODEL_NAME = "retailiq_random_forest_baseline"


def _time_based_split(frame: pd.DataFrame, test_size: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split by date order so the validation set is later than the training set."""
    frame = frame.sort_values("DATE").reset_index(drop=True)
    if len(frame) < 10:
        return frame, frame

    split_index = max(1, int(len(frame) * (1 - test_size)))
    split_index = min(split_index, len(frame) - 1)
    return frame.iloc[:split_index].copy(), frame.iloc[split_index:].copy()


def _build_pipeline(
    random_state: int,
    n_estimators: int,
    max_depth: int | None,
    min_samples_leaf: int,
    max_samples: float | None,
) -> Pipeline:
    categorical_features = ["STORE_TYPE"]
    numeric_features = [column for column in MODEL_FEATURE_COLUMNS if column not in categorical_features]

    numeric_pipeline = Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))])
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_features),
            ("categorical", categorical_pipeline, categorical_features),
        ]
    )
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        random_state=random_state,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        max_samples=max_samples,
        n_jobs=-1,
    )
    return Pipeline(steps=[("preprocess", preprocessor), ("model", model)])


def _wape(actual: pd.Series, predicted: np.ndarray) -> float:
    denominator = actual.abs().sum()
    if denominator == 0:
        return 0.0
    return float(np.abs(actual - predicted).sum() / denominator)


def train_baseline_model(
    data_dir: str | Path = "data/sample",
    model_dir: str | Path = "models",
    test_size: float = 0.2,
    random_state: int = 42,
    n_estimators: int = 50,
    max_depth: int | None = 16,
    min_samples_leaf: int = 5,
    max_samples: float | None = 0.65,
) -> dict[str, object]:
    """Train and persist a baseline Random Forest forecasting model."""
    sales, stores, features = load_retailiq_data(data_dir)
    frame = build_training_frame(sales, stores, features)
    if frame.empty:
        raise ValueError("No training rows available after feature engineering.")

    train_frame, test_frame = _time_based_split(frame, test_size)
    pipeline = _build_pipeline(
        random_state=random_state,
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        max_samples=max_samples,
    )
    pipeline.fit(train_frame[MODEL_FEATURE_COLUMNS], train_frame[TARGET_COLUMN])

    predictions = pipeline.predict(test_frame[MODEL_FEATURE_COLUMNS])
    trained_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    model_version = f"baseline_rf_{trained_at.replace(':', '').replace('+00:00', 'Z')}"

    metrics = {
        "model_name": MODEL_NAME,
        "model_version": model_version,
        "trained_at": trained_at,
        "training_rows": int(len(train_frame)),
        "validation_rows": int(len(test_frame)),
        "n_estimators": int(n_estimators),
        "max_depth": max_depth,
        "min_samples_leaf": int(min_samples_leaf),
        "max_samples": max_samples,
        "start_date": str(frame["DATE"].min().date()),
        "end_date": str(frame["DATE"].max().date()),
        "mae": float(mean_absolute_error(test_frame[TARGET_COLUMN], predictions)),
        "rmse": float(mean_squared_error(test_frame[TARGET_COLUMN], predictions) ** 0.5),
        "wape": _wape(test_frame[TARGET_COLUMN], predictions),
    }

    model_path = Path(model_dir)
    model_path.mkdir(parents=True, exist_ok=True)
    artifact = {
        "pipeline": pipeline,
        "feature_columns": MODEL_FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "model_name": MODEL_NAME,
        "model_version": model_version,
        "trained_at": trained_at,
        "metrics": metrics,
    }

    with (model_path / "retailiq_forecast_model.pkl").open("wb") as file:
        pickle.dump(artifact, file)
    (model_path / "forecast_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the RetailIQ Phase 2 baseline forecast model.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/sample"))
    parser.add_argument("--model-dir", type=Path, default=Path("models"))
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--n-estimators", type=int, default=50)
    parser.add_argument("--max-depth", type=int, default=16)
    parser.add_argument("--min-samples-leaf", type=int, default=5)
    parser.add_argument("--max-samples", type=float, default=0.65)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metrics = train_baseline_model(
        data_dir=args.data_dir,
        model_dir=args.model_dir,
        test_size=args.test_size,
        random_state=args.random_state,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        max_samples=args.max_samples,
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
