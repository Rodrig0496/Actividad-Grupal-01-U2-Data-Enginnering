select city, observed_on
from {{ ref('stg_weather_daily') }}
group by city, observed_on
having count(*) > 1
