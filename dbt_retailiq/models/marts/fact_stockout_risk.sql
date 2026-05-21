select
    store::number as store_id,
    dept::number as dept_id,
    risk_date::date as risk_date,
    predicted_demand::float as predicted_demand,
    available_inventory::float as available_inventory,
    stockout_risk_score::float as stockout_risk_score,
    risk_category::varchar as risk_category,
    recommended_action::varchar as recommended_action,
    model_version::varchar as model_version,
    created_at::timestamp_ntz as created_at
from {{ source('ml', 'stockout_risk') }}
