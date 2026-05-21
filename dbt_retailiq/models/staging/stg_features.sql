with source as (
    select * from {{ source('raw', 'features') }}
)

select
    store::number as store_id,
    date::date as feature_date,
    temperature::float as temperature,
    fuel_price::float as fuel_price,
    markdown1::float as markdown1,
    markdown2::float as markdown2,
    markdown3::float as markdown3,
    markdown4::float as markdown4,
    markdown5::float as markdown5,
    cpi::float as cpi,
    unemployment::float as unemployment,
    is_holiday::boolean as is_holiday,
    source_file,
    loaded_at
from source

