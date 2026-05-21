select
    store_id,
    dept_id,
    inventory_date,
    sku,
    available_inventory,
    safety_stock_units,
    reorder_point_units,
    source_file,
    loaded_at
from {{ ref('stg_inventory') }}

