with source as (
    select * from {{ source('raw', 'stores') }}
)

select
    store::number as store_id,
    store_type::varchar as store_type,
    size::number as store_size,
    source_file,
    loaded_at
from source

