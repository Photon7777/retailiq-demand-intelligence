# RetailIQ Airflow Orchestration

This folder adds Apache Airflow as an optional orchestration layer for the RetailIQ Phase 2 data and ML workflow.

Airflow runs the same pipeline pieces that are already available as local commands:

1. Validate the Walmart source files.
2. Prepare canonical RetailIQ CSVs.
3. Optionally upload prepared files to GCS.
4. Load Snowflake `RAW` tables.
5. Train the forecast model.
6. Generate forecast, stockout risk, and anomaly outputs.
7. Load Snowflake `ML` tables.
8. Run `dbt run`.
9. Run `dbt test`.

## Why Airflow Is Optional

The Streamlit app and Cloud Run deployment do not need Airflow at runtime. Airflow is kept behind a Docker Compose profile so local development and public deployment stay lightweight.

The Airflow image installs RetailIQ's Python, ML, Snowflake, and dbt dependencies into an isolated virtual environment at `/opt/airflow/retailiq_venv`. Airflow itself keeps its own package environment.

## Prerequisites

- Docker Desktop
- A populated `.env` file
- Walmart files in `data/raw/walmart/`
- Snowflake objects created with `cloud/snowflake_setup.sql`
- Snowflake authentication that works without an interactive prompt

For local Airflow, key-pair authentication with the read-only app user is the cleanest Snowflake path. Username/password MFA can work only if the account and client configuration support non-interactive token caching.

## Start Airflow

From the repository root:

```bash
export AIRFLOW_UID=$(id -u)
mkdir -p orchestration/airflow/logs orchestration/airflow/plugins
docker compose --profile airflow up --build airflow-init
docker compose --profile airflow up airflow-webserver airflow-scheduler
```

Open Airflow:

```text
http://localhost:8081
```

Default local credentials:

```text
username: admin
password: admin
```

You can override them before `airflow-init`:

```bash
export AIRFLOW_ADMIN_USERNAME=retailiq
export AIRFLOW_ADMIN_PASSWORD="choose-a-local-password"
docker compose --profile airflow up --build airflow-init
```

## Trigger The DAG

In the Airflow UI:

1. Open `retailiq_phase2_pipeline`.
2. Unpause the DAG if needed.
3. Click **Trigger DAG**.
4. Watch the task graph from source validation through `dbt_test_marts`.

## Configuration

The DAG reads these optional environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `RETAILIQ_AIRFLOW_INPUT_DIR` | `data/raw/walmart` | Walmart source files |
| `RETAILIQ_AIRFLOW_PROCESSED_DIR` | `data/processed/walmart` | Canonical output files |
| `RETAILIQ_AIRFLOW_MODEL_DIR` | `models` | Model artifact directory |
| `RETAILIQ_AIRFLOW_OUTPUT_DIR` | `data/ml_outputs` | ML output CSV directory |
| `RETAILIQ_AIRFLOW_DBT_DIR` | `/opt/airflow/retailiq/dbt_retailiq` | dbt project directory |
| `RETAILIQ_AIRFLOW_TRUNCATE_FIRST` | `true` | Recreate Snowflake load tables before loading |
| `RETAILIQ_AIRFLOW_UPLOAD_GCS` | `false` | Enable optional GCS upload task |
| `RETAILIQ_AIRFLOW_GCS_PREFIX` | `retailiq/raw` | GCS object prefix |

## Shut Down

```bash
docker compose --profile airflow down
```

To remove the local Airflow metadata database:

```bash
docker compose --profile airflow down --volumes
```
