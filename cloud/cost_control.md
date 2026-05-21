# Cost Control Guide

RetailIQ is designed to be inexpensive to run during development.

## Snowflake

- Use the `XSMALL` `RETAILIQ_WH` warehouse for development.
- Keep `AUTO_SUSPEND = 60` and `AUTO_RESUME = TRUE`.
- Avoid running exploratory queries against raw data without filters.
- Use dbt incremental models later when model outputs become larger.
- Suspend the warehouse manually after long development sessions:

```sql
ALTER WAREHOUSE RETAILIQ_WH SUSPEND;
```

## Google Cloud Storage

- Use one dedicated bucket for the project.
- Store only needed raw files and generated artifacts.
- Use lifecycle rules to delete old temporary files if experimenting heavily.

## OpenAI

- Keep AI analyst prompts scoped to needed tables and columns.
- Add query previews and user confirmations before expensive or broad analysis.
- Log token usage in later phases.

## Local Development

- Use small sample CSV files in Phase 1.
- Run full dataset loads intentionally, not on every app start.

