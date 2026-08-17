select
    c.city,
    c.station_id,
    s.station_name,
    s.latitude,
    s.longitude,
    s.elevation,
    s.province,
    s.wmo_id
from {{ ref('stg_configured_stations') }} c
inner join {{ ref('stg_stations') }} s
    on c.station_id = s.station_id