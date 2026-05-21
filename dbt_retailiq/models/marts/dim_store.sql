select distinct
    store_id,
    store_type,
    store_size
from {{ ref('stg_stores') }}

