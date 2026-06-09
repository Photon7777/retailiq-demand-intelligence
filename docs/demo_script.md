# RetailIQ Demo Script

Use this script for a 4 to 6 minute walkthrough of the deployed app and the repository.

Live demo: https://retailiq-demand-intelligence-420746557396.us-central1.run.app

## Demo Goal

Show that RetailIQ is not just a dashboard. It is an end-to-end retail intelligence product with cloud ingestion, Snowflake modeling, dbt marts, ML outputs, governed AI analysis, and production deployment.

## 1. Open With The Business Problem

Retail operators need to know where demand is moving, which products are at risk of stockout, and which sales changes need investigation. In many companies, those signals live across disconnected spreadsheets, warehouse tables, forecast files, and analyst notebooks.

RetailIQ brings those workflows into one Snowflake-backed product experience.

## 2. Start On RetailIQ Home

Point out:

- The app is deployed publicly on Google Cloud Run.
- Snowflake is the serving layer for metrics and marts.
- The architecture follows a retail operations workflow: demand sensing, inventory signal, forecast mart, and analyst layer.
- The app uses a read-only Snowflake service user with key-pair authentication in production.

Screenshot reference: `screenshots/retailiq_home.png`

## 3. Executive Overview

Open **Executive Overview** and explain the top-line business view.

Talk track:

- Total sales is calculated from the governed mart layer.
- Store and department counts confirm the Walmart dataset is loaded at full scale.
- Risk and anomaly signals are surfaced as business KPIs, not only model outputs.
- Charts are designed for executives to scan sales movement and store performance quickly.

Screenshot reference: `screenshots/executive_overview.png`

## 4. Demand Forecasting

Open **Demand Forecasting**.

Talk track:

- Forecasts are generated in Python and persisted into Snowflake `ML` tables.
- dbt promotes the model outputs into `MARTS.FACT_FORECAST`.
- The page supports store, department, horizon, and row-limit controls without loading the entire warehouse table into memory.
- WAPE gives a direct view of forecast quality.

Screenshot reference: `screenshots/demand_forecasting.png`

## 5. Stockout And Anomaly Views

Open **Stockout Risk** and **Anomaly Center**.

Talk track:

- Stockout risk compares predicted demand against available inventory.
- Synthetic inventory makes it possible to model operational risk even when the source Kaggle dataset does not include inventory.
- Anomaly detection flags unusual store-department-week sales behavior for investigation.
- These pages turn ML outputs into operational actions.

## 6. AI Retail Analyst

Open **AI Retail Analyst**.

Talk track:

- The AI analyst translates natural-language questions into governed Snowflake SQL.
- Guardrails restrict queries to approved `MARTS` tables.
- The app blocks writes, DDL, account metadata queries, and multi-statement SQL.
- It shows the generated SQL and result preview so the answer remains auditable.
- If OpenAI is unavailable, the app falls back to deterministic Snowflake-backed templates.

Suggested question:

```text
What are total sales and how many stores are represented?
```

## 7. Repository Close

Show the repository structure and call out:

- `src/ingestion`: data preparation and Snowflake loading
- `dbt_retailiq`: staging, intermediate, and mart models
- `src/ml`: forecasting, stockout risk, anomaly detection, and synthetic inventory
- `src/ai`: governed SQL and analyst orchestration
- `app`: Streamlit product experience
- `tests`: unit, integration-style, and deployment asset checks
- `cloud`: Snowflake and Cloud Run deployment setup

## Closing Line

RetailIQ demonstrates the full data product lifecycle: raw retail data to governed warehouse marts, model outputs, operational dashboards, AI-assisted analysis, automated tests, Docker packaging, and public cloud deployment.
