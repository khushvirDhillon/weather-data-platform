select *
from {{ ref('int_weather_observations') }}
where element in ('TMAX', 'TMIN', 'TAVG')
  and normalized_value not between -80 and 60