select *
from {{ ref('int_weather_observations') }}
where element in ('PRCP', 'SNOW', 'SNWD')
  and normalized_value < 0