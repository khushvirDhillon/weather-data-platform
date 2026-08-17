select
    station_id,
    cast(latitude as double) as latitude,
    cast(longitude as double) as longitude,
    cast(elevation as double) as elevation,
    nullif(state, '') as province,
    station_name,
    nullif(gsn_flag, '') as gsn_flag,
    nullif(hcn_crn_flag, '') as hcn_crn_flag,
    nullif(wmo_id, '') as wmo_id
from {{ source('raw', 'raw_stations') }}