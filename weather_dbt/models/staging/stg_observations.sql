select
    station_id,
    cast(date as date) as observation_date,
    element,
    cast(value as integer) as raw_value,
    nullif(mflag, '') as measurement_flag,
    nullif(qflag, '') as quality_flag,
    nullif(sflag, '') as source_flag,
    nullif(obs_time, '') as observation_time
from {{ source('raw', 'raw_observations') }}