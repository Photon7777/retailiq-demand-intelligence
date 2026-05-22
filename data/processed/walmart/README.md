# Prepared Walmart Data

The real Walmart dataset is converted into canonical RetailIQ CSV files here when running:

```bash
python -m src.ingestion.prepare_walmart_data \
  --input-dir data/raw/walmart \
  --output-dir data/processed/walmart
```

Generated CSV files in this folder are ignored by Git because the full dataset should stay local.
