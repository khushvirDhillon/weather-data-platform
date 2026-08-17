select
    station_id,
    try_cast(nullif(latitude, '') as double) as latitude,
    try_cast(nullif(longitude, '') as double) as longitude,
    try_cast(nullif(elevation, '') as double) as elevation,
    nullif(state, '') as province,
    station_name,
    nullif(gsn_flag, '') as gsn_flag,
    nullif(hcn_crn_flag, '') as hcn_crn_flag,
    nullif(wmo_id, '') as wmo_id
from {{ source('raw', 'raw_stations') }}