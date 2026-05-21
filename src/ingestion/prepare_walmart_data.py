"""Prepare Walmart Store Sales Forecasting files for the RetailIQ pipeline."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from src.ml.feature_engineering import normalize_columns
from src.ml.synthetic_inventory import generate_synthetic_inventory, generate_synthetic_weather


logger = logging.getLogger(__name__)

WALMART_FILES = {
    "sales": "train.csv",
    "stores": "stores.csv",
    "features": "features.csv",
}


def _read_walmart_file(input_dir: Path, file_name: str) -> pd.DataFrame:
    path = input_dir / file_name
    if not path.exists():
        raise FileNotFoundError(f"Missing Walmart dataset file: {path}")
    return normalize_columns(pd.read_csv(path))


def prepare_sales(train: pd.DataFrame) -> pd.DataFrame:
    """Prepare Walmart train.csv as canonical RetailIQ sales.csv."""
    required = ["STORE", "DEPT", "DATE", "WEEKLY_SALES", "IS_HOLIDAY"]
    missing = [column for column in required if column not in train.columns]
    if missing:
        raise ValueError(f"train.csv is missing required columns: {', '.join(missing)}")

    output = train[required].copy()
    output["DATE"] = pd.to_datetime(output["DATE"], errors="coerce").dt.date
    output["WEEKLY_SALES"] = pd.to_numeric(output["WEEKLY_SALES"], errors="coerce")
    return output.rename(
        columns={
            "STORE": "Store",
            "DEPT": "Dept",
            "DATE": "Date",
            "WEEKLY_SALES": "Weekly_Sales",
            "IS_HOLIDAY": "IsHoliday",
        }
    )


def prepare_stores(stores: pd.DataFrame) -> pd.DataFrame:
    """Prepare Walmart stores.csv as canonical RetailIQ stores.csv."""
    required = ["STORE", "STORE_TYPE", "SIZE"]
    missing = [column for column in required if column not in stores.columns]
    if missing:
        raise ValueError(f"stores.csv is missing required columns: {', '.join(missing)}")

    return stores[required].copy().rename(columns={"STORE": "Store", "STORE_TYPE": "Type", "SIZE": "Size"})


def prepare_features(features: pd.DataFrame) -> pd.DataFrame:
    """Prepare Walmart features.csv as canonical RetailIQ features.csv."""
    required = [
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
    ]
    for column in required:
        if column not in features.columns:
            features[column] = 0.0 if column.startswith("MARKDOWN") else pd.NA

    output = features[required].copy()
    output["DATE"] = pd.to_datetime(output["DATE"], errors="coerce").dt.date
    for column in ["MARKDOWN1", "MARKDOWN2", "MARKDOWN3", "MARKDOWN4", "MARKDOWN5"]:
        output[column] = pd.to_numeric(output[column], errors="coerce").fillna(0)

    return output.rename(
        columns={
            "STORE": "Store",
            "DATE": "Date",
            "TEMPERATURE": "Temperature",
            "FUEL_PRICE": "Fuel_Price",
            "MARKDOWN1": "MarkDown1",
            "MARKDOWN2": "MarkDown2",
            "MARKDOWN3": "MarkDown3",
            "MARKDOWN4": "MarkDown4",
            "MARKDOWN5": "MarkDown5",
            "CPI": "CPI",
            "UNEMPLOYMENT": "Unemployment",
            "IS_HOLIDAY": "IsHoliday",
        }
    )


def prepare_walmart_dataset(
    input_dir: Path,
    output_dir: Path,
    include_synthetic: bool = True,
    random_seed: int = 42,
) -> dict[str, Path]:
    """Convert raw Walmart files into RetailIQ canonical CSVs."""
    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    train = _read_walmart_file(input_dir, WALMART_FILES["sales"])
    stores_raw = _read_walmart_file(input_dir, WALMART_FILES["stores"])
    features_raw = _read_walmart_file(input_dir, WALMART_FILES["features"])

    sales = prepare_sales(train)
    stores = prepare_stores(stores_raw)
    features = prepare_features(features_raw)

    outputs: dict[str, Path] = {}
    for name, frame in {"sales": sales, "stores": stores, "features": features}.items():
        path = output_dir / f"{name}.csv"
        frame.to_csv(path, index=False)
        outputs[name] = path
        logger.info("Wrote %s rows to %s", len(frame), path)

    if include_synthetic:
        inventory = generate_synthetic_inventory(sales, random_seed=random_seed)
        weather = generate_synthetic_weather(features, random_seed=random_seed)
        for name, frame in {"inventory": inventory, "weather": weather}.items():
            path = output_dir / f"{name}.csv"
            frame.to_csv(path, index=False)
            outputs[name] = path
            logger.info("Wrote %s rows to %s", len(frame), path)

    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Walmart Store Sales Forecasting files for RetailIQ.")
    parser.add_argument("--input-dir", type=Path, default=Path("data/raw/walmart"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/sample"))
    parser.add_argument("--skip-synthetic", action="store_true", help="Only write sales, stores, and features files.")
    parser.add_argument("--random-seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    args = parse_args()
    outputs = prepare_walmart_dataset(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        include_synthetic=not args.skip_synthetic,
        random_seed=args.random_seed,
    )
    print("Prepared RetailIQ files:")
    for name, path in outputs.items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
