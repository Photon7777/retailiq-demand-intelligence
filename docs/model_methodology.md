# Model Methodology

RetailIQ will use an iterative modeling approach that starts with interpretable baselines and moves toward stronger machine learning models.

## Forecasting

Planned forecasting workflow:

1. Aggregate weekly sales by store, department, and date.
2. Join external features such as holidays, temperature, fuel price, CPI, unemployment, and markdowns.
3. Add calendar features such as year, month, week of year, and holiday flags.
4. Train baseline models using historical averages and lag features.
5. Train machine learning models with scikit-learn and XGBoost.
6. Evaluate with WAPE, MAE, RMSE, and bias.
7. Persist forecast outputs to Snowflake.

Expected forecast output contract:

| Column | Description |
| --- | --- |
| `store_id` | Store identifier |
| `dept_id` | Department identifier |
| `forecast_date` | Forecasted week |
| `predicted_demand` | Predicted demand value |
| `prediction_interval_lower` | Lower prediction interval |
| `prediction_interval_upper` | Upper prediction interval |
| `model_version` | Model version or training run identifier |

## Stockout Risk

Stockout risk will use forecasted demand and available inventory:

```text
stockout_risk_score = predicted_demand / available_inventory
```

The first implementation classifies scores into Low, Medium, High, and Critical categories. Later phases can add lead time, reorder points, safety stock, service-level targets, and vendor constraints.

## Anomaly Detection

The first anomaly workflow will compare weekly sales against historical behavior by store and department. Candidate methods include:

- z-score thresholds
- rolling mean and standard deviation bands
- isolation forest
- forecast residual anomaly detection

Anomaly outputs will include severity, direction, score, and investigation status.

## Explainability

Later phases will add feature importance, segment-level error analysis, and model monitoring views for portfolio storytelling.

