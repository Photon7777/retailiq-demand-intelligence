select
    store_id,
    dept_id,
    sales_date,
    weekly_sales,
    is_holiday,
    source_file,
    loaded_at
from {{ ref('stg_sales') }}

