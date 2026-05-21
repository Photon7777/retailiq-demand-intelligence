# Data Dictionary

This dictionary describes planned source, mart, and ML output tables.

## RAW.SALES

| Column | Description |
| --- | --- |
| `STORE` | Walmart store identifier |
| `DEPT` | Department identifier |
| `DATE` | Weekly sales date |
| `WEEKLY_SALES` | Weekly sales value |
| `IS_HOLIDAY` | Holiday week flag |
| `SOURCE_FILE` | Source file name |
| `LOADED_AT` | Ingestion timestamp |

## RAW.STORES

| Column | Description |
| --- | --- |
| `STORE` | Walmart store identifier |
| `STORE_TYPE` | Store type |
| `SIZE` | Store size |
| `SOURCE_FILE` | Source file name |
| `LOADED_AT` | Ingestion timestamp |

## RAW.FEATURES

| Column | Description |
| --- | --- |
| `STORE` | Walmart store identifier |
| `DATE` | Feature date |
| `TEMPERATURE` | Store-area temperature |
| `FUEL_PRICE` | Fuel price |
| `MARKDOWN1` to `MARKDOWN5` | Promotional markdown indicators |
| `CPI` | Consumer price index |
| `UNEMPLOYMENT` | Unemployment rate |
| `IS_HOLIDAY` | Holiday week flag |

## RAW.INVENTORY

| Column | Description |
| --- | --- |
| `STORE` | Store identifier |
| `DEPT` | Department identifier |
| `DATE` | Inventory snapshot date |
| `SKU` | Synthetic SKU identifier |
| `AVAILABLE_INVENTORY` | Available units |
| `SAFETY_STOCK_UNITS` | Safety stock threshold |
| `REORDER_POINT_UNITS` | Reorder point threshold |

## RAW.WEATHER

| Column | Description |
| --- | --- |
| `STORE` | Store identifier |
| `DATE` | Weather date |
| `TEMPERATURE` | Temperature |
| `PRECIPITATION` | Precipitation amount |
| `SNOWFALL` | Snowfall amount |

## ML.DEMAND_FORECASTS

| Column | Description |
| --- | --- |
| `STORE` | Store identifier |
| `DEPT` | Department identifier |
| `FORECAST_DATE` | Forecasted week |
| `HORIZON_DAYS` | Forecast horizon, where 0 is historical scoring and 7 is next-week forecast |
| `PREDICTED_DEMAND` | Predicted demand or sales proxy |
| `ACTUAL_DEMAND` | Actual weekly sales when available |
| `PREDICTION_INTERVAL_LOWER` | Lower uncertainty bound |
| `PREDICTION_INTERVAL_UPPER` | Upper uncertainty bound |
| `MODEL_NAME` | Model family used for the forecast |
| `MODEL_VERSION` | Model version identifier |
| `TRAINED_AT` | Model training timestamp |
| `CREATED_AT` | Output generation timestamp |

## ML.STOCKOUT_RISK

| Column | Description |
| --- | --- |
| `STORE` | Store identifier |
| `DEPT` | Department identifier |
| `RISK_DATE` | Risk scoring date |
| `PREDICTED_DEMAND` | Forecasted demand used in the risk score |
| `AVAILABLE_INVENTORY` | Inventory available for the store and department |
| `STOCKOUT_RISK_SCORE` | Predicted demand divided by available inventory |
| `RISK_CATEGORY` | Low, Medium, High, or Critical |
| `RECOMMENDED_ACTION` | Business action recommendation |
| `MODEL_VERSION` | Forecast model version used for scoring |
| `CREATED_AT` | Output generation timestamp |

## ML.SALES_ANOMALIES

| Column | Description |
| --- | --- |
| `STORE` | Store identifier |
| `DEPT` | Department identifier |
| `SALES_DATE` | Weekly sales date |
| `WEEKLY_SALES` | Observed weekly sales |
| `ANOMALY_SCORE` | Z-score anomaly score |
| `IS_ANOMALY` | Boolean anomaly flag |
| `SEVERITY` | Low, Medium, or High |
| `DIRECTION` | Sales spike or sales drop |
| `MODEL_VERSION` | Anomaly detection method version |
| `CREATED_AT` | Output generation timestamp |
