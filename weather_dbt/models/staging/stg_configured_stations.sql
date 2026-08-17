select
    city,
    station_id
from {{ source('raw', 'configured_stations') }}