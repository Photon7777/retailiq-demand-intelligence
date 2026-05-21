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

## Planned ML Output: ML.DEMAND_FORECASTS

| Column | Description |
| --- | --- |
| `STORE_ID` | Store identifier |
| `DEPT_ID` | Department identifier |
| `FORECAST_DATE` | Forecasted week |
| `PREDICTED_DEMAND` | Predicted demand or sales proxy |
| `PREDICTION_INTERVAL_LOWER` | Lower uncertainty bound |
| `PREDICTION_INTERVAL_UPPER` | Upper uncertainty bound |
| `MODEL_VERSION` | Model version identifier |

