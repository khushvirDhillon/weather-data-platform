select
    trim(cast(station_id as varchar)) as station_id,

    try_cast(date as date) as observation_date,

    nullif(trim(cast(element as varchar)), '') as element,

    try_cast(
        nullif(trim(cast(value as varchar)), '')
        as integer
    ) as raw_value,

    nullif(trim(cast(mflag as varchar)), '') as measurement_flag,
    nullif(trim(cast(qflag as varchar)), '') as quality_flag,
    nullif(trim(cast(sflag as varchar)), '') as source_flag,
    nullif(trim(cast(obs_time as varchar)), '') as observation_time

from {{ source('raw', 'raw_observations') }}