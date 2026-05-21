"""Stockout risk scoring utilities."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite

import numpy as np
import pandas as pd


RISK_ACTIONS = {
    "Low": "Maintain current replenishment plan.",
    "Medium": "Monitor sell-through and review upcoming replenishment timing.",
    "High": "Prioritize replenishment review and consider shifting inventory from lower-risk locations.",
    "Critical": "Escalate immediately, expedite replenishment, and evaluate demand substitution options.",
}


@dataclass(frozen=True)
class StockoutRiskResult:
    predicted_demand: float
    available_inventory: float
    stockout_risk_score: float
    risk_category: str
    recommended_action: str


def classify_stockout_risk(stockout_risk_score: float) -> str:
    """Classify a stockout risk score into Low, Medium, High, or Critical."""
    if not isfinite(stockout_risk_score):
        return "Critical"
    if stockout_risk_score < 0.60:
        return "Low"
    if stockout_risk_score <= 0.90:
        return "Medium"
    if stockout_risk_score <= 1.10:
        return "High"
    return "Critical"


def calculate_stockout_risk(predicted_demand: float, available_inventory: float) -> StockoutRiskResult:
    """Calculate stockout risk as predicted demand divided by available inventory."""
    predicted = float(predicted_demand)
    inventory = float(available_inventory)

    if inventory <= 0:
        score = float("inf")
    else:
        score = predicted / inventory

    category = classify_stockout_risk(score)
    return StockoutRiskResult(
        predicted_demand=predicted,
        available_inventory=inventory,
        stockout_risk_score=score,
        risk_category=category,
        recommended_action=RISK_ACTIONS[category],
    )


def score_stockout_risk_frame(
    df: pd.DataFrame,
    predicted_demand_column: str = "predicted_demand",
    available_inventory_column: str = "available_inventory",
) -> pd.DataFrame:
    """Score stockout risk for every row in a DataFrame."""
    scored = df.copy()
    inventory = scored[available_inventory_column].astype(float)
    predicted = scored[predicted_demand_column].astype(float)
    scored["stockout_risk_score"] = np.where(inventory <= 0, np.inf, predicted / inventory)
    scored["risk_category"] = scored["stockout_risk_score"].apply(classify_stockout_risk)
    scored["recommended_action"] = scored["risk_category"].map(RISK_ACTIONS)
    return scored


def stockout_risk_as_dict(predicted_demand: float, available_inventory: float) -> dict[str, float | str]:
    """Convenience wrapper for APIs and Streamlit displays."""
    return asdict(calculate_stockout_risk(predicted_demand, available_inventory))

