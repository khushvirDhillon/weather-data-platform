select
    station_id,
    cast(latitude as double) as latitude,
    cast(longitude as double) as longitude,
    element,
    cast(first_year as integer) as first_year,
    cast(last_year as integer) as last_year
from {{ source('raw', 'raw_inventory') }}