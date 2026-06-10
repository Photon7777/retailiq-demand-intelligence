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

For local Airflow, use key-pair authentication with `RETAILIQ_AIRFLOW_USER`. Username/password MFA is fine for manual local commands, but Airflow tasks run unattended and cannot stop to ask for a fresh 6-digit TOTP code.

## Configure Snowflake For Airflow

If `load_raw_tables_to_snowflake` fails with `MFA with TOTP is required`, switch Airflow to a service user.

Create a local private key:

```bash
mkdir -p secrets/snowflake
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM \
  -out secrets/snowflake/retailiq_airflow_key.p8 \
  -nocrypt
openssl rsa \
  -in secrets/snowflake/retailiq_airflow_key.p8 \
  -pubout \
  -out secrets/snowflake/retailiq_airflow_key.pub
```

Print the one-line public key:

```bash
awk 'NF && !/-----/{printf "%s",$0}' secrets/snowflake/retailiq_airflow_key.pub
echo
```

In Snowflake, open `cloud/snowflake_airflow_user.sql`, replace `<paste_public_key_here>` with that one-line public key, and run the worksheet as `ACCOUNTADMIN`.

Then update `.env` for Airflow:

```bash
SNOWFLAKE_USER=RETAILIQ_AIRFLOW_USER
SNOWFLAKE_PASSWORD=
SNOWFLAKE_AUTHENTICATOR=SNOWFLAKE_JWT
SNOWFLAKE_PRIVATE_KEY_FILE=/opt/airflow/retailiq/secrets/snowflake/retailiq_airflow_key.p8
SNOWFLAKE_PRIVATE_KEY_FILE_PWD=
SNOWFLAKE_ROLE=RETAILIQ_PIPELINE_ROLE
SNOWFLAKE_WAREHOUSE=RETAILIQ_WH
SNOWFLAKE_DATABASE=RETAILIQ_DB
SNOWFLAKE_SCHEMA=RAW
```

The `secrets/` directory is gitignored. Do not commit private keys.

## Start Airflow

From the repository root:

```bash
export AIRFLOW_UID=$(id -u)
mkdir -p orchestration/airflow/logs orchestration/airflow/plugins
docker compose --profile airflow up --build airflow-init
docker compose --profile airflow up airflow-webserver airflow-scheduler
```

If you changed `.env`, recreate the containers so Airflow receives the new variables:

```bash
docker compose --profile airflow down --remove-orphans
export AIRFLOW_UID=$(id -u)
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

## Troubleshooting

If `airflow-init` says the Airflow user has no username, pull the latest repo changes and recreate the Airflow containers:

```bash
docker compose --profile airflow down --remove-orphans
export AIRFLOW_UID=$(id -u)
docker compose --profile airflow up --build airflow-init
```

The init service must use Airflow's official container entrypoint so the runtime user is registered correctly before Airflow commands run.

If `load_raw_tables_to_snowflake` fails with a Snowflake MFA/TOTP error, Airflow is still using personal username/password authentication. Complete the `RETAILIQ_AIRFLOW_USER` key-pair setup above, restart the Airflow containers, and trigger a new DAG run.
