with dates as (
    select sales_date as date_day from {{ ref('stg_sales') }}
    union
    select feature_date as date_day from {{ ref('stg_features') }}
    union
    select inventory_date as date_day from {{ ref('stg_inventory') }}
)

select
    date_day,
    year(date_day) as year,
    quarter(date_day) as quarter,
    month(date_day) as month,
    weekofyear(date_day) as week_of_year,
    dayofweek(date_day) as day_of_week
from dates
where date_day is not null

