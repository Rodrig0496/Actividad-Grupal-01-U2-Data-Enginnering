select *
from {{ ref('stg_weather_daily') }}
where city is null
    or observed_on is null
    or temperature_max_c is null
    or temperature_min_c is null
    or precipitation_mm is null
    or not isfinite(temperature_max_c)
    or not isfinite(temperature_min_c)
    or not isfinite(precipitation_mm)
    or temperature_min_c > temperature_max_c
    or precipitation_mm < 0
