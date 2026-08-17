select
    s.city,
    s.station_id,
    s.station_name,
    i.element,
    i.first_year,
    i.last_year
from {{ ref('int_target_stations') }} s
inner join {{ ref('stg_inventory') }} i
    on s.station_id = i.station_id