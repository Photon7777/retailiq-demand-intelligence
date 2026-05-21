select
    sales.store_id,
    sales.dept_id,
    sales.sales_date,
    sales.weekly_sales,
    sales.is_holiday,
    stores.store_type,
    stores.store_size,
    features.temperature,
    features.fuel_price,
    features.markdown1,
    features.markdown2,
    features.markdown3,
    features.markdown4,
    features.markdown5,
    features.cpi,
    features.unemployment
from {{ ref('stg_sales') }} as sales
left join {{ ref('stg_stores') }} as stores
    on sales.store_id = stores.store_id
left join {{ ref('stg_features') }} as features
    on sales.store_id = features.store_id
    and sales.sales_date = features.feature_date
