with source as (
    select * from {{ source('raw', 'sales') }}
)

select
    store::number as store_id,
    dept::number as dept_id,
    date::date as sales_date,
    weekly_sales::float as weekly_sales,
    is_holiday::boolean as is_holiday,
    source_file,
    loaded_at
from source

