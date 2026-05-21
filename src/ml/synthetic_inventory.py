"""Synthetic inventory and weather generation for Phase 2 local data prep."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.ml.feature_engineering import normalize_columns


INVENTORY_COLUMNS = [
    "Store",
    "Dept",
    "Date",
    "SKU",
    "Available_Inventory",
    "Safety_Stock_Units",
    "Reorder_Point_Units",
]

WEATHER_COLUMNS = ["Store", "Date", "Temperature", "Precipitation", "Snowfall"]


def generate_synthetic_inventory(
    sales: pd.DataFrame,
    random_seed: int = 42,
    low_inventory_share: float = 0.18,
) -> pd.DataFrame:
    """Create deterministic synthetic inventory from sales rows.

    Walmart's public dataset does not include inventory. This generator uses weekly sales
    as a demand proxy and creates enough low-coverage rows to exercise stockout logic.
    """
    rng = np.random.default_rng(random_seed)
    sales = normalize_columns(sales)
    required = {"STORE", "DEPT", "DATE", "WEEKLY_SALES"}
    missing = sorted(required - set(sales.columns))
    if missing:
        raise ValueError(f"Sales data is missing required columns for inventory generation: {', '.join(missing)}")

    output = sales[["STORE", "DEPT", "DATE", "WEEKLY_SALES"]].copy()
    output["DATE"] = pd.to_datetime(output["DATE"], errors="coerce").dt.date
    demand_proxy = pd.to_numeric(output["WEEKLY_SALES"], errors="coerce").fillna(0).clip(lower=0)

    base_coverage = rng.normal(loc=1.25, scale=0.28, size=len(output)).clip(0.65, 2.05)
    low_inventory_mask = rng.random(len(output)) < low_inventory_share
    base_coverage[low_inventory_mask] = rng.uniform(0.35, 0.95, size=low_inventory_mask.sum())

    available_inventory = (demand_proxy * base_coverage).round(2)
    safety_stock = (demand_proxy * rng.uniform(0.18, 0.32, size=len(output))).round(2)
    reorder_point = (safety_stock + demand_proxy * rng.uniform(0.25, 0.45, size=len(output))).round(2)

    result = pd.DataFrame(
        {
            "Store": output["STORE"].astype(int),
            "Dept": output["DEPT"].astype(int),
            "Date": output["DATE"],
            "SKU": output.apply(lambda row: f"SKU-{int(row['STORE'])}-{int(row['DEPT'])}", axis=1),
            "Available_Inventory": available_inventory,
            "Safety_Stock_Units": safety_stock,
            "Reorder_Point_Units": reorder_point,
        }
    )
    return result[INVENTORY_COLUMNS]


def generate_synthetic_weather(features: pd.DataFrame, random_seed: int = 42) -> pd.DataFrame:
    """Create a simple weather file from Walmart feature rows."""
    rng = np.random.default_rng(random_seed)
    features = normalize_columns(features)
    required = {"STORE", "DATE", "TEMPERATURE"}
    missing = sorted(required - set(features.columns))
    if missing:
        raise ValueError(f"Feature data is missing required columns for weather generation: {', '.join(missing)}")

    output = features[["STORE", "DATE", "TEMPERATURE"]].copy()
    output["DATE"] = pd.to_datetime(output["DATE"], errors="coerce").dt.date
    temperature = pd.to_numeric(output["TEMPERATURE"], errors="coerce").fillna(output["TEMPERATURE"].median())
    precipitation = rng.gamma(shape=1.2, scale=0.08, size=len(output)).clip(0, 1.5).round(2)
    snow_mask = temperature < 35
    snowfall = np.where(snow_mask, precipitation * rng.uniform(0.2, 1.1, size=len(output)), 0.0).round(2)

    result = pd.DataFrame(
        {
            "Store": output["STORE"].astype(int),
            "Date": output["DATE"],
            "Temperature": temperature.round(2),
            "Precipitation": precipitation,
            "Snowfall": snowfall,
        }
    )
    return result[WEATHER_COLUMNS]


def write_synthetic_files(data_dir: Path, output_dir: Path, random_seed: int = 42) -> dict[str, Path]:
    """Generate inventory and weather CSVs from canonical sales/features files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    sales = pd.read_csv(data_dir / "sales.csv")
    features = pd.read_csv(data_dir / "features.csv")

    inventory = generate_synthetic_inventory(sales, random_seed=random_seed)
    weather = generate_synthetic_weather(features, random_seed=random_seed)

    inventory_path = output_dir / "inventory.csv"
    weather_path = output_dir / "weather.csv"
    inventory.to_csv(inventory_path, index=False)
    weather.to_csv(weather_path, index=False)
    return {"inventory": inventory_path, "weather": weather_path}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic RetailIQ inventory and weather CSV files.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/sample"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/sample"))
    parser.add_argument("--random-seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = write_synthetic_files(args.data_dir, args.output_dir, args.random_seed)
    for name, path in paths.items():
        print(f"Wrote {name}: {path}")


if __name__ == "__main__":
    main()
