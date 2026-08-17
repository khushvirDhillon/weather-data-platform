select
    city,
    station_id,
    station_name,
    observation_date,

    max(case when element = 'TMAX' then normalized_value end) as tmax_c,
    max(case when element = 'TMIN' then normalized_value end) as tmin_c,
    max(case when element = 'TAVG' then normalized_value end) as tavg_c,

    max(case when element = 'PRCP' then normalized_value end) as precipitation_mm,
    max(case when element = 'SNOW' then normalized_value end) as snowfall_mm,
    max(case when element = 'SNWD' then normalized_value end) as snow_depth_mm,

    max(case when element = 'AWND' then normalized_value end) as avg_wind_speed_ms

from {{ ref('int_weather_observations') }}

where is_quality_valid = true

group by
    city,
    station_id,
    station_name,
    observation_date