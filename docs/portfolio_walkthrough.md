# Portfolio Walkthrough

RetailIQ is a cloud-native retail demand intelligence platform built to demonstrate practical full-stack data engineering and AI engineering.

## What This Project Shows

RetailIQ connects the pieces that typically sit apart in analytics projects:

- Data ingestion from local CSV files and cloud-ready storage paths
- Snowflake database, schema, warehouse, and role setup
- dbt staging and mart models with tests
- Python ML workflows for forecasting, stockout risk, anomaly detection, and synthetic inventory
- Streamlit dashboards backed by Snowflake marts
- Governed AI analyst workflows using OpenAI and controlled SQL execution
- Docker packaging and Google Cloud Run deployment
- Optional Airflow orchestration for repeatable local pipeline runs
- Documentation, runbooks, tests, and cost controls

## Product Narrative

The app is framed as a retail operations command center. A business user can start with executive metrics, drill into forecast quality, inspect inventory risk, review pipeline freshness, investigate anomalies, and ask plain-English questions through the AI Retail Analyst.

Behind the scenes, the platform keeps the layers separate:

1. Raw Walmart files are converted into canonical RetailIQ files.
2. Snowflake stores raw source tables and ML output tables.
3. dbt turns raw and ML tables into governed marts.
4. Streamlit queries the mart layer for dashboard pages.
5. Airflow can orchestrate the local data and ML refresh path.
6. Pipeline health is surfaced from Snowflake metadata, row counts, and freshness timestamps.
7. The AI analyst generates read-only SQL against approved marts only.

## Engineering Decisions

### Snowflake As The Serving Layer

The app reads from Snowflake marts instead of local CSV files. This keeps the dashboard aligned with the same governed tables that analysts and downstream systems would use in production.

### dbt For Analytics Contracts

dbt models define typed staging views, dimensions, facts, and model-output marts. Tests validate uniqueness, non-null fields, relationships, and expected source integrity.

### Baseline ML Before Complexity

The current forecast model is intentionally a baseline. It proves the end-to-end ML path first: feature preparation, training, scoring, output contracts, Snowflake persistence, dbt promotion, and dashboard consumption.

### Guarded AI Instead Of Raw Chat

The AI Retail Analyst does not directly improvise against the full warehouse. It generates SQL through a restricted prompt, validates the SQL, limits result sizes, executes read-only queries, and displays query traceability.

### Cloud Deployment With Read-Only Credentials

The public app uses Google Cloud Run, Secret Manager, and Snowflake key-pair authentication. A dedicated Snowflake app user avoids exposing personal credentials or admin access.

## Demo Flow

1. Open the live Cloud Run URL.
2. Show the home page and architecture summary.
3. Open Executive Overview for sales, store coverage, and risk KPIs.
4. Open Demand Forecasting for WAPE, forecast totals, filters, and forecast rows.
5. Open Stockout Risk and Anomaly Center to show operational model outputs.
6. Open Pipeline Health to show orchestration readiness and Snowflake freshness.
7. Open AI Retail Analyst and ask a governed business question.
8. Close in GitHub with the repo structure, tests, and deployment guide.

For a timed version, use `docs/demo_script.md`.

## Strong Interview Talking Points

- I designed a layered retail data platform instead of a single notebook or isolated dashboard.
- I used Snowflake and dbt to create reliable analytics contracts before serving data to Streamlit.
- I built model output contracts so forecasts, stockout risk, and anomalies could be loaded and queried like production data.
- I deployed the app publicly while keeping secrets out of GitHub and the container image.
- I added AI in a governed way, with SQL validation, approved tables, row limits, and visible query traceability.

## Next Iterations

- Add CI with GitHub Actions for tests and linting.
- Add richer model monitoring and explainability.
- Add scheduled data refreshes through Cloud Run Jobs or GitHub Actions.
- Add a dedicated semantic layer for more complex analyst questions.
- Add authentication or a demo mode toggle if this becomes a public long-term portfolio asset.
