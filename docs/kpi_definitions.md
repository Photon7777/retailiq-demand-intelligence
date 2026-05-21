# KPI Definitions

## Total Sales

Total sales is the sum of weekly sales over the selected period.

```text
total_sales = sum(weekly_sales)
```

## WAPE

Weighted Absolute Percentage Error measures forecast error relative to total actual demand.

```text
WAPE = sum(abs(actual - forecast)) / sum(abs(actual))
```

Lower WAPE indicates better forecast accuracy.

## Forecast Error

Forecast error is the signed difference between actual and predicted demand.

```text
forecast_error = actual_demand - predicted_demand
```

Positive error means the model under-forecasted demand. Negative error means it over-forecasted demand.

## Stockout Risk

Stockout risk measures whether predicted demand may exceed available inventory.

```text
stockout_risk_score = predicted_demand / available_inventory
```

Risk categories:

| Score | Category |
| --- | --- |
| `< 0.60` | Low |
| `0.60 to 0.90` | Medium |
| `0.90 to 1.10` | High |
| `> 1.10` | Critical |

## Anomaly Count

Anomaly count is the number of store-department-week records flagged as unusual by the anomaly detection workflow.

```text
anomaly_count = count(records where is_anomaly = true)
```

