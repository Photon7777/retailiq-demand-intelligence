# Architecture

RetailIQ is designed as a layered data and AI platform for retail demand intelligence.

## Pipeline

```text
Local CSV / GCS
    -> Snowflake RAW
    -> dbt STAGING
    -> dbt MARTS
    -> Python ML outputs
    -> Streamlit dashboards
    -> AI Retail Analyst
```

## Layers

### Ingestion

Raw source files are stored locally in `data/sample/` during Phase 1. The ingestion script validates expected files, normalizes column names, and appends data into Snowflake `RAW` tables.

### Warehouse

Snowflake stores each major stage in a dedicated schema:

- `RAW`: source-aligned tables
- `STAGING`: typed and cleaned dbt models
- `MARTS`: analytics-ready facts and dimensions
- `ML`: forecasts, anomaly scores, features, and model outputs
- `ANALYTICS`: dashboard and AI analyst serving layer

### Transformation

dbt provides modular SQL transformations, lineage, tests, and documentation. Phase 1 includes starter staging and mart models.

### Machine Learning

Python workflows will train demand forecasting models, generate prediction outputs, score stockout risk, and detect anomalies.

### Application

Streamlit is the primary presentation layer. It will show executive KPIs, forecasting trends, inventory risk, anomalies, data quality checks, and AI analyst answers.

### AI

The AI Retail Analyst will use OpenAI to interpret business questions, generate governed read-only SQL, execute against Snowflake, and summarize results in business language.

