from __future__ import annotations

from math import isinf

import pandas as pd

from src.ml.stockout_risk import calculate_stockout_risk, classify_stockout_risk, score_stockout_risk_frame


def test_stockout_risk_category_boundaries() -> None:
    assert classify_stockout_risk(0.59) == "Low"
    assert classify_stockout_risk(0.60) == "Medium"
    assert classify_stockout_risk(0.90) == "Medium"
    assert classify_stockout_risk(0.91) == "High"
    assert classify_stockout_risk(1.10) == "High"
    assert classify_stockout_risk(1.11) == "Critical"


def test_stockout_risk_score_and_action() -> None:
    result = calculate_stockout_risk(predicted_demand=110, available_inventory=100)

    assert result.stockout_risk_score == 1.10
    assert result.risk_category == "High"
    assert "replenishment" in result.recommended_action.lower()


def test_zero_inventory_is_critical() -> None:
    result = calculate_stockout_risk(predicted_demand=10, available_inventory=0)

    assert isinf(result.stockout_risk_score)
    assert result.risk_category == "Critical"


def test_dataframe_scoring_adds_expected_columns() -> None:
    df = pd.DataFrame(
        {
            "predicted_demand": [50, 75, 105, 140],
            "available_inventory": [100, 100, 100, 100],
        }
    )

    scored = score_stockout_risk_frame(df)

    assert scored["risk_category"].tolist() == ["Low", "Medium", "High", "Critical"]
    assert {"stockout_risk_score", "risk_category", "recommended_action"}.issubset(scored.columns)

