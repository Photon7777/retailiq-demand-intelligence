# Walmart Dataset Drop Zone

Place the downloaded Walmart Store Sales Forecasting CSV files here:

- `train.csv`
- `stores.csv`
- `features.csv`

The CSV files are intentionally ignored by Git because the real dataset can be large. Run `python -m src.ingestion.prepare_walmart_data --input-dir data/raw/walmart --output-dir data/sample` to convert them into the canonical RetailIQ files used by the ingestion pipeline.
