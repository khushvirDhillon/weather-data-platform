select
    station_id,
    try_cast(nullif(latitude, '') as double) as latitude,
    try_cast(nullif(longitude, '') as double) as longitude,
    element,
    try_cast(nullif(first_year, '') as integer) as first_year,
    try_cast(nullif(last_year, '') as integer) as last_year
from {{ source('raw', 'raw_inventory') }}