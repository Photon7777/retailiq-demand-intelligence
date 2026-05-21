# ML Output Files

Phase 2 model scripts write generated CSV outputs here:

- `demand_forecasts.csv`
- `stockout_risk.csv`
- `sales_anomalies.csv`

The generated CSV files are intentionally ignored by Git. Load them into Snowflake with `python -m src.ingestion.load_ml_outputs_to_snowflake --output-dir data/ml_outputs --truncate-first --prompt-passcode`.
