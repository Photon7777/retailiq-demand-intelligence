# Phase 2 Runbook

This runbook moves RetailIQ from a working foundation into the full Walmart data and analytics buildout.

## Goal

Phase 2 produces a Snowflake-backed analytics layer with:

- Canonical Walmart `sales`, `stores`, and `features` files
- Synthetic `inventory` and `weather` files for operational analytics
- A baseline Random Forest demand forecast model
- Forecast, stockout risk, and anomaly output CSVs
- Snowflake `RAW`, `ML`, and dbt `MARTS` tables
- Streamlit pages backed by real Snowflake data

## Prerequisites

1. Create and activate the Python environment.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Place Kaggle Walmart files here:

```text
data/raw/walmart/train.csv
data/raw/walmart/stores.csv
data/raw/walmart/features.csv
```

3. Fill in `.env` with your Snowflake values.

4. Run `cloud/snowflake_setup.sql` in Snowsight.

5. If your account requires MFA, warm the Snowflake MFA cache before dbt or command-line loads.

```bash
export SNOWFLAKE_PASSCODE=123456
python -c "from src.utils.snowflake_connection import test_snowflake_connection; print(test_snowflake_connection())"
unset SNOWFLAKE_PASSCODE
```

Replace `123456` with your current authenticator code.

## Recommended Workflow

Preview the complete command plan:

```bash
python -m src.pipelines.run_phase2 --truncate-first --dry-run
```

Run local preparation, model training, and ML output generation only:

```bash
python -m src.pipelines.run_phase2 --local-only
```

Run the full pipeline after Snowflake connectivity is working:

```bash
python -m src.pipelines.run_phase2 --truncate-first
```

If MFA is not cached, use:

```bash
python -m src.pipelines.run_phase2 --truncate-first --prompt-passcode
```

The runner uses the passcode through the child process environment rather than placing it in each child command.

## What The Runner Does

1. Converts Kaggle source files into canonical RetailIQ CSVs.
2. Optionally uploads prepared CSVs to GCS with `--upload-gcs`.
3. Loads prepared CSVs into Snowflake `RAW` tables.
4. Trains the baseline forecast model into `models/`.
5. Generates local ML outputs into `data/ml_outputs/`.
6. Loads ML outputs into Snowflake `ML` tables.
7. Runs `dbt run` and `dbt test`.

## Validation Queries

Run these in Snowsight after the full workflow:

```sql
USE WAREHOUSE RETAILIQ_WH;
USE DATABASE RETAILIQ_DB;

SELECT 'RAW.SALES' AS object_name, COUNT(*) AS row_count FROM RAW.SALES
UNION ALL
SELECT 'RAW.INVENTORY', COUNT(*) FROM RAW.INVENTORY
UNION ALL
SELECT 'ML.DEMAND_FORECASTS', COUNT(*) FROM ML.DEMAND_FORECASTS
UNION ALL
SELECT 'ML.STOCKOUT_RISK', COUNT(*) FROM ML.STOCKOUT_RISK
UNION ALL
SELECT 'ML.SALES_ANOMALIES', COUNT(*) FROM ML.SALES_ANOMALIES
UNION ALL
SELECT 'MARTS.FACT_FORECAST', COUNT(*) FROM MARTS.FACT_FORECAST;
```

Expected full Walmart scale is roughly:

- `RAW.SALES`: 421,570 rows
- `RAW.INVENTORY`: 421,570 rows
- `ML.DEMAND_FORECASTS`: 424,901 rows
- `ML.STOCKOUT_RISK`: 421,570 rows
- `ML.SALES_ANOMALIES`: 421,570 rows

## App Check

Start Streamlit:

```bash
streamlit run app/streamlit_app.py
```

Then check:

- Executive Overview shows total sales and store counts.
- Demand Forecasting shows WAPE, forecast rows, trend chart, and detail rows.
- Stockout Risk shows Critical, High, Medium, and Low counts.
- Anomaly Center shows candidate rows and flagged anomalies.
- Data Quality shows raw, mart, and ML object health.

## Troubleshooting

If Snowflake authentication fails, verify:

- `SNOWFLAKE_ACCOUNT` matches the account locator or organization-account value shown in Snowsight.
- `SNOWFLAKE_AUTHENTICATOR=username_password_mfa` for username/password plus authenticator-app MFA.
- `SNOWFLAKE_ROLE`, `SNOWFLAKE_WAREHOUSE`, and `SNOWFLAKE_DATABASE` are populated.
- MFA caching has been enabled if you want repeated dbt connections.

If dbt cannot find tables, verify the raw and ML loads completed before `dbt run`.

If Streamlit feels slow, confirm the Demand Forecasting page is using `MARTS.FACT_FORECAST` and not loading the full CSV directly.
