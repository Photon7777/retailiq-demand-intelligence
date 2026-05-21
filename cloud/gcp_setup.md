# Google Cloud Storage Setup

RetailIQ uses Google Cloud Storage as the cloud landing zone for raw retail files before they are loaded into Snowflake.

## Recommended Setup

1. Create a dedicated GCP project for the portfolio project.
2. Create a storage bucket with a globally unique name.
3. Use a regional bucket close to your Snowflake account region where possible.
4. Enable uniform bucket-level access.
5. Create a service account with least-privilege access to the bucket.
6. Download the service account key only for local development, and store the path in `GOOGLE_APPLICATION_CREDENTIALS`.

## Suggested Bucket Layout

```text
gs://<bucket-name>/retailiq/raw/sales/
gs://<bucket-name>/retailiq/raw/stores/
gs://<bucket-name>/retailiq/raw/features/
gs://<bucket-name>/retailiq/raw/inventory/
gs://<bucket-name>/retailiq/raw/weather/
```

## Local Environment Variables

```bash
GCP_PROJECT_ID=
GCP_BUCKET_NAME=
GOOGLE_APPLICATION_CREDENTIALS=
```

Keep service account credentials out of GitHub. Use `.env` locally and secret managers for deployed environments.

