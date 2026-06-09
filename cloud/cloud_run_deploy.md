# Deploy RetailIQ To Google Cloud Run

This guide deploys the Streamlit app as a public Cloud Run service while keeping Snowflake credentials out of GitHub and out of the container image.

Primary references:

- Google Cloud Run Streamlit quickstart: https://docs.cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-streamlit-service
- Cloud Run secrets: https://cloud.google.com/run/docs/configuring/services/secrets
- Snowflake key-pair authentication: https://docs.snowflake.com/en/user-guide/key-pair-auth
- Snowflake Python connector authentication: https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-connect

## 1. Prerequisites

Install and authenticate the Google Cloud CLI:

```bash
brew install --cask google-cloud-sdk
gcloud init
gcloud auth login
```

Set your project and preferred region:

```bash
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"

gcloud config set project "$PROJECT_ID"
```

Enable the required APIs:

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com
```

## 2. Create A Snowflake App Key Pair

Generate a private key that will be stored in Secret Manager:

```bash
mkdir -p "$HOME/.retailiq"

openssl genrsa 2048 | openssl pkcs8 \
  -topk8 \
  -inform PEM \
  -out "$HOME/.retailiq/retailiq_snowflake_key.p8" \
  -nocrypt

openssl rsa \
  -in "$HOME/.retailiq/retailiq_snowflake_key.p8" \
  -pubout \
  -out "$HOME/.retailiq/retailiq_snowflake_key.pub"
```

Print the public key in Snowflake's expected one-line format:

```bash
grep -v "PUBLIC KEY" "$HOME/.retailiq/retailiq_snowflake_key.pub" | tr -d '\n'
```

Copy the output. You will paste it into `cloud/snowflake_app_user.sql`.

## 3. Create The Snowflake App User

Open Snowsight and run:

```sql
SELECT CURRENT_ROLE();
```

Switch to `ACCOUNTADMIN` if needed. Then open `cloud/snowflake_app_user.sql`, replace:

```text
<paste_public_key_here>
```

with the one-line public key from the previous step, and run the script.

The script creates:

- `RETAILIQ_APP_ROLE`
- `RETAILIQ_APP_USER`
- read-only grants on `RAW`, `STAGING`, `MARTS`, `ML`, and `ANALYTICS`
- key-pair authentication for the service user

Do not use your personal `ACCOUNTADMIN` user in Cloud Run.

## 4. Store Secrets In Google Secret Manager

Create the Snowflake private key secret:

```bash
gcloud secrets create retailiq-snowflake-private-key \
  --data-file="$HOME/.retailiq/retailiq_snowflake_key.p8"
```

If you are ready to enable the AI analyst, store your OpenAI key too:

```bash
printf "%s" "your-openai-api-key" | \
  gcloud secrets create retailiq-openai-api-key --data-file=-
```

Skip the OpenAI secret if you are only deploying the dashboard.

## 5. Create A Cloud Run Runtime Service Account

```bash
gcloud iam service-accounts create retailiq-runner \
  --display-name="RetailIQ Cloud Run runtime"

export RUNTIME_SA="retailiq-runner@${PROJECT_ID}.iam.gserviceaccount.com"
```

Allow the service account to read the Snowflake private key:

```bash
gcloud secrets add-iam-policy-binding retailiq-snowflake-private-key \
  --member="serviceAccount:${RUNTIME_SA}" \
  --role="roles/secretmanager.secretAccessor"
```

If you created the OpenAI secret:

```bash
gcloud secrets add-iam-policy-binding retailiq-openai-api-key \
  --member="serviceAccount:${RUNTIME_SA}" \
  --role="roles/secretmanager.secretAccessor"
```

## 6. Deploy RetailIQ

Run this from the repository root:

```bash
cd /Users/saipraneethkmg/Documents/Retail/retailiq-demand-intelligence
```

Deploy the dashboard without OpenAI first:

```bash
gcloud run deploy retailiq-demand-intelligence \
  --source . \
  --region "$REGION" \
  --service-account "$RUNTIME_SA" \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 2 \
  --set-env-vars "SNOWFLAKE_ACCOUNT=your-snowflake-account,SNOWFLAKE_USER=RETAILIQ_APP_USER,SNOWFLAKE_AUTHENTICATOR=SNOWFLAKE_JWT,SNOWFLAKE_ROLE=RETAILIQ_APP_ROLE,SNOWFLAKE_WAREHOUSE=RETAILIQ_WH,SNOWFLAKE_DATABASE=RETAILIQ_DB,SNOWFLAKE_SCHEMA=MARTS,SNOWFLAKE_PRIVATE_KEY_FILE=/secrets/snowflake_private_key.p8,OPENAI_MODEL=gpt-5-mini" \
  --set-secrets "/secrets/snowflake_private_key.p8=retailiq-snowflake-private-key:latest"
```

If you also created `retailiq-openai-api-key`, replace the `--set-secrets` line with:

```bash
--set-secrets "/secrets/snowflake_private_key.p8=retailiq-snowflake-private-key:latest,OPENAI_API_KEY=retailiq-openai-api-key:latest"
```

Important: replace `your-snowflake-account` with the same account value that works locally, such as `hktqqza-vk12996` if that is your active locator.

If the OpenAI secret is not attached, the AI Retail Analyst page still runs with deterministic governed SQL templates. Attach `OPENAI_API_KEY` to enable full LLM SQL generation and answer synthesis.

## 7. Open The Public URL

```bash
gcloud run services describe retailiq-demand-intelligence \
  --region "$REGION" \
  --format="value(status.url)"
```

Open the returned URL in your browser.

The app should load without asking for a Snowflake MFA code because Cloud Run uses `RETAILIQ_APP_USER` with key-pair authentication.

## 8. Validate The Deployment

Check service logs:

```bash
gcloud run services logs read retailiq-demand-intelligence \
  --region "$REGION" \
  --limit 100
```

In the app:

- Open **Executive Overview** and confirm metrics render.
- Open **Demand Forecasting** and confirm the store/department filters respond.
- Open **Stockout Risk** and confirm the risk table loads.
- Open **Data Quality** and confirm table health renders.

## 9. Update Or Redeploy

After pushing code changes to GitHub, redeploy from the repo root:

```bash
gcloud run deploy retailiq-demand-intelligence \
  --source . \
  --region "$REGION"
```

Cloud Run keeps the existing environment variables and secrets unless you replace them.

## 10. Cost Controls

Cloud Run is configured with `--min-instances 0`, so it can scale to zero when idle.

Snowflake is already configured with `AUTO_SUSPEND = 60`. To manually suspend the warehouse:

```sql
ALTER WAREHOUSE RETAILIQ_WH SUSPEND;
```

If Snowflake says the warehouse cannot be suspended, it is usually already suspended or currently running a query.

## Troubleshooting

If Cloud Run starts but the app cannot connect to Snowflake:

- Confirm `SNOWFLAKE_ACCOUNT` exactly matches the working local account value.
- Confirm `SNOWFLAKE_AUTHENTICATOR=SNOWFLAKE_JWT`.
- Confirm `SNOWFLAKE_PRIVATE_KEY_FILE=/secrets/snowflake_private_key.p8`.
- Confirm `RETAILIQ_APP_USER` has the public key from your generated private key.
- Confirm the Cloud Run service account has `roles/secretmanager.secretAccessor`.
- Check logs with `gcloud run services logs read`.

If the app loads slowly on first visit, that is normal for a scale-to-zero service. The first request has to start the container.
