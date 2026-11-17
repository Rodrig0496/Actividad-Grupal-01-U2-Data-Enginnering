select
    city,
    observed_on,
    temperature_max_c,
    temperature_min_c,
    precipitation_mm
from {{ source('raw', 'daily_weather') }}
