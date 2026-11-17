select *
from {{ ref('mart_weather_monthly') }}
where observed_days <> day(last_day(month))
