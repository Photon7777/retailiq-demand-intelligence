# Model Methodology

RetailIQ uses an iterative modeling approach that starts with interpretable baselines and moves toward stronger machine learning models.

## Forecasting

Phase 2 forecasting workflow:

1. Aggregate weekly sales by store, department, and date.
2. Join external features such as holidays, temperature, fuel price, CPI, unemployment, and markdowns.
3. Add calendar features such as year, month, week of year, and holiday flags.
4. Train a scikit-learn Random Forest baseline.
5. Score historical rows and create a one-week-ahead forecast for each store and department.
6. Evaluate with WAPE, MAE, and RMSE.
7. Persist forecast outputs to Snowflake `ML.DEMAND_FORECASTS`.

Expected forecast output contract:

| Column | Description |
| --- | --- |
| `store_id` | Store identifier |
| `dept_id` | Department identifier |
| `forecast_date` | Forecasted week |
| `horizon_days` | Forecast horizon in days |
| `predicted_demand` | Predicted demand value |
| `actual_demand` | Actual demand when available |
| `prediction_interval_lower` | Lower prediction interval |
| `prediction_interval_upper` | Upper prediction interval |
| `model_version` | Model version or training run identifier |

## Stockout Risk

Stockout risk will use forecasted demand and available inventory:

```text
stockout_risk_score = predicted_demand / available_inventory
```

The Phase 2 implementation classifies scores into Low, Medium, High, and Critical categories and writes results to `ML.STOCKOUT_RISK`. Later phases can add lead time, reorder points, safety stock, service-level targets, and vendor constraints.

## Anomaly Detection

The Phase 2 anomaly workflow compares weekly sales against historical behavior by store and department with z-score thresholds. Candidate future methods include:

- z-score thresholds
- rolling mean and standard deviation bands
- isolation forest
- forecast residual anomaly detection

Anomaly outputs will include severity, direction, score, and investigation status.

## Explainability

Later phases will add feature importance, segment-level error analysis, and model monitoring views for portfolio storytelling.
