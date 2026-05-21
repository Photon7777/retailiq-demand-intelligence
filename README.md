# RetailIQ: Cloud-Native Retail Demand Intelligence Platform

RetailIQ is a portfolio-grade retail analytics platform for demand forecasting, stockout risk monitoring, anomaly detection, and AI-assisted business analysis. The project is designed as an end-to-end cloud-native data product using Google Cloud Storage, Snowflake, dbt, Python, Streamlit, Docker, GitHub, and the OpenAI API.

This repository currently contains the Phase 1 foundation: a professional project structure, setup documentation, Snowflake raw-layer DDL, configuration utilities, a first local CSV-to-Snowflake ingestion path, baseline stockout risk logic, dbt starter models, tests, and a Streamlit shell for future dashboards.

## Business Problem

Retail teams need reliable answers to recurring operational questions:

- Which stores and departments are underperforming?
- Where is demand likely to exceed inventory?
- Which sales movements are true anomalies versus normal seasonal variation?
- How accurate are forecasts by store, department, and time period?
- Can business users ask questions in plain English without waiting on ad hoc SQL?

RetailIQ is built to turn raw retail data into a Snowflake-backed intelligence layer that supports both dashboards and an AI Retail Analyst chatbot.

## Solution Architecture

The planned platform follows a layered analytics architecture:

1. **Data ingestion**: Walmart sales, stores, features, weather, and synthetic inventory files are staged locally and uploaded to Google Cloud Storage.
2. **Cloud warehouse**: Snowflake stores raw data in `RAW`, transformed tables in `STAGING` and `MARTS`, and model outputs in `ML` and `ANALYTICS`.
3. **Transformations**: dbt models clean, type, join, and document the analytics layer.
4. **Machine learning**: Python models generate demand forecasts, stockout risk scores, and anomaly flags.
5. **Application layer**: Streamlit provides executive KPIs, demand forecasts, inventory risk, anomaly investigation, data quality checks, and an AI analyst interface.
6. **AI analyst**: OpenAI-powered workflows translate business questions into governed Snowflake-backed answers.

## Tech Stack

- **Cloud storage**: Google Cloud Storage
- **Warehouse**: Snowflake
- **Transformations**: dbt with `dbt-snowflake`
- **Data and ML**: Python, pandas, NumPy, scikit-learn, XGBoost
- **Application**: Streamlit and Plotly
- **AI**: OpenAI API and LangChain
- **DevOps**: Docker Compose and GitHub
- **Testing**: pytest

## Dataset

RetailIQ uses the Walmart Store Sales Forecasting dataset as its primary dataset. The expected files include:

- `sales.csv`: weekly sales by store and department
- `stores.csv`: store metadata such as type and size
- `features.csv`: external features such as temperature, fuel price, CPI, unemployment, markdowns, and holiday flags

The project also supports planned synthetic data generation for:

- `inventory.csv`: available inventory, safety stock, and reorder points
- `weather.csv`: optional weather enrichment for store-date analysis

Place Phase 1 sample files in `data/sample/` before running the ingestion script.

## Planned Features

- Local CSV ingestion into Snowflake raw tables
- GCS upload path for raw data staging
- dbt staging, intermediate, and mart models
- Demand forecasting by store, department, and date
- Stockout risk scoring using forecasted demand and available inventory
- Sales anomaly detection
- Data quality monitoring
- Streamlit executive dashboard
- AI Retail Analyst chatbot using Snowflake-backed SQL
- Dockerized local development and deployment-ready project layout

## Quick Start

```bash
cd retailiq-demand-intelligence
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel pyproject-hooks
pip install -r requirements.txt
cp .env.example .env
```

Recommended local runtime: Python 3.11. If your Mac's default `python3` is Python 3.9, install Python 3.11 first and recreate the virtual environment.

```bash
brew install python@3.11
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
python --version
python -m pip install --upgrade pip setuptools wheel pyproject-hooks
pip install -r requirements.txt
```

Update `.env` with your Snowflake, GCP, and OpenAI configuration. Then create Snowflake objects:

If your Snowflake account requires multi-factor authentication, set:

```bash
SNOWFLAKE_AUTHENTICATOR=username_password_mfa
```

For authenticator-app codes, either type the current 6-digit code into the Streamlit sidebar before clicking **Check Snowflake Connection**, or temporarily set `SNOWFLAKE_PASSCODE` before a command-line connection test. Do not commit real passcodes or passwords.

```bash
snowsql -f cloud/snowflake_setup.sql
```

The repository includes a tiny sample dataset in `data/sample/` for smoke testing the pipeline:

```text
data/sample/sales.csv
data/sample/stores.csv
data/sample/features.csv
data/sample/inventory.csv
data/sample/weather.csv
```

For the full Walmart dataset, download the Walmart Store Sales Forecasting files and place them in `data/raw/walmart/`:

```text
data/raw/walmart/train.csv
data/raw/walmart/stores.csv
data/raw/walmart/features.csv
```

Then prepare canonical RetailIQ files, including synthetic inventory and weather:

```bash
python -m src.ingestion.prepare_walmart_data \
  --input-dir data/raw/walmart \
  --output-dir data/sample
```

Run the local-to-Snowflake ingestion:

```bash
python -m src.ingestion.load_to_snowflake --sample-dir data/sample --truncate-first
```

If your Snowflake account requires MFA/TOTP:

```bash
python -m src.ingestion.load_to_snowflake --sample-dir data/sample --truncate-first --prompt-passcode
```

For dbt with Snowflake MFA, keep `SNOWFLAKE_AUTHENTICATOR=username_password_mfa`. If you are using a personal development Snowflake account, you can enable short-lived MFA token caching from a Snowsight worksheet:

```sql
ALTER ACCOUNT SET ALLOW_CLIENT_MFA_CACHING = TRUE;
```

Then run one Python connection check with a current passcode before running dbt:

```bash
export SNOWFLAKE_PASSCODE=123456
python -c "from src.utils.snowflake_connection import test_snowflake_connection; print(test_snowflake_connection())"
unset SNOWFLAKE_PASSCODE
```

Replace `123456` with the current 6-digit authenticator code.

Launch the Streamlit app:

```bash
streamlit run app/streamlit_app.py
```

Run tests:

```bash
pytest
```

## Phase 2 Workflow

After the raw files and dbt marts are working, generate and publish ML outputs:

```bash
python -m src.ml.train_forecast_model --data-dir data/sample --model-dir models
python -m src.ml.generate_predictions \
  --data-dir data/sample \
  --model-path models/retailiq_forecast_model.pkl \
  --output-dir data/ml_outputs
```

Load the generated outputs into Snowflake. The loader creates the `ML` schema and output tables if they do not exist:

```bash
python -m src.ingestion.load_ml_outputs_to_snowflake \
  --output-dir data/ml_outputs \
  --truncate-first \
  --prompt-passcode
```

Finally run dbt so `MARTS.FACT_FORECAST`, `MARTS.FACT_STOCKOUT_RISK`, and `MARTS.FACT_ANOMALIES` are available to Streamlit:

```bash
cd dbt_retailiq
dbt run
dbt test
cd ..
```

## Docker Compose

For a simple containerized Streamlit run:

```bash
cp .env.example .env
docker compose up --build
```

The app will be available at `http://localhost:8501`.

## Project Roadmap

### Phase 1: Foundation

- Repository structure and setup files
- Snowflake raw-layer DDL
- Environment and connection utilities
- Local CSV ingestion into Snowflake
- Baseline stockout risk scoring
- dbt project scaffold and starter tests
- Streamlit app shell and placeholder pages
- Architecture, data dictionary, KPI, methodology, and business docs

### Phase 1.5: Live Dashboard Bridge

- Query Snowflake marts from Streamlit
- Show live executive KPIs and table health
- Display a baseline demand forecast view
- Score stockout risk from observed demand and available inventory
- Surface simple anomaly and data quality views
- Add a rule-based AI analyst preview before OpenAI integration

### Phase 2: Data and Analytics Buildout

- Prepare the full Walmart dataset into canonical RetailIQ CSVs
- Generate synthetic inventory and weather records
- Train a baseline Random Forest forecasting model
- Generate forecast, stockout risk, and sales anomaly output files
- Persist model outputs to Snowflake `ML` tables
- Transform ML outputs into dbt marts for Streamlit dashboards

### Phase 3: Intelligence Layer

- Add anomaly detection workflows
- Build full Streamlit dashboards
- Add model evaluation and explainability
- Implement AI Retail Analyst chatbot with governed SQL generation
- Add Docker hardening and deployment documentation

### Phase 4: Portfolio Polish

- Add screenshots and architecture diagrams
- Add sample business scenarios
- Add CI checks with GitHub Actions
- Publish a polished project walkthrough
