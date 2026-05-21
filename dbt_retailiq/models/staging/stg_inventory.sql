with source as (
    select * from {{ source('raw', 'inventory') }}
)

select
    store::number as store_id,
    dept::number as dept_id,
    date::date as inventory_date,
    sku::varchar as sku,
    available_inventory::float as available_inventory,
    safety_stock_units::float as safety_stock_units,
    reorder_point_units::float as reorder_point_units,
    source_file,
    loaded_at
from source

