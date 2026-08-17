select
    s.city,
    o.station_id,
    s.station_name,
    o.observation_date,
    o.element,
    o.raw_value,

    o.raw_value * m.scale_factor as normalized_value,
    m.unit,
    m.description as element_description,

    o.measurement_flag,
    o.quality_flag,
    o.source_flag,
    o.observation_time,

    q.description as quality_issue,

    case
        when o.quality_flag is null then true
        else false
    end as is_quality_valid

from {{ ref('stg_observations') }} o

inner join {{ ref('int_target_stations') }} s
    on o.station_id = s.station_id

inner join {{ ref('int_station_elements') }} e
    on o.station_id = e.station_id
    and o.element = e.element

left join {{ source('raw', 'element_metadata') }} m
    on o.element = m.element

left join {{ source('raw', 'quality_flag_metadata') }} q
    on o.quality_flag = q.quality_flag

where e.first_year is not null
  and e.last_year is not null
  and extract(year from o.observation_date)
      between e.first_year and e.last_year