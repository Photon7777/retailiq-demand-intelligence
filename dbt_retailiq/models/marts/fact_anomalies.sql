select
    store::number as store_id,
    dept::number as dept_id,
    sales_date::date as sales_date,
    weekly_sales::float as weekly_sales,
    anomaly_score::float as anomaly_score,
    is_anomaly::boolean as is_anomaly,
    severity::varchar as severity,
    direction::varchar as direction,
    model_version::varchar as model_version,
    try_to_timestamp_ntz(created_at::varchar) as created_at
from {{ source('ml', 'sales_anomalies') }}
