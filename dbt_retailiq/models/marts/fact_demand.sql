select
    sales.store_id,
    sales.dept_id,
    sales.sales_date as demand_date,
    sales.weekly_sales as observed_demand,
    inventory.available_inventory,
    inventory.safety_stock_units,
    inventory.reorder_point_units
from {{ ref('stg_sales') }} as sales
left join {{ ref('stg_inventory') }} as inventory
    on sales.store_id = inventory.store_id
    and sales.dept_id = inventory.dept_id
    and sales.sales_date = inventory.inventory_date

