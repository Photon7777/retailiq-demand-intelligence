select
    store::number as store_id,
    dept::number as dept_id,
    forecast_date::date as forecast_date,
    horizon_days::number as horizon_days,
    predicted_demand::float as predicted_demand,
    actual_demand::float as actual_demand,
    prediction_interval_lower::float as prediction_interval_lower,
    prediction_interval_upper::float as prediction_interval_upper,
    model_name::varchar as model_name,
    model_version::varchar as model_version,
    try_to_timestamp_ntz(trained_at::varchar) as trained_at,
    try_to_timestamp_ntz(created_at::varchar) as created_at
from {{ source('ml', 'demand_forecasts') }}
