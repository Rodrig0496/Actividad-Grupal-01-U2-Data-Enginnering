{{ config(materialized='table') }}

select
    city || '-' || strftime(observed_on, '%Y-%m') as city_month,
    city,
    cast(date_trunc('month', observed_on) as date) as month,
    count(*) as observed_days,
    round(avg(temperature_max_c), 2) as avg_max_c,
    round(avg(temperature_min_c), 2) as avg_min_c,
    round(sum(precipitation_mm), 2) as total_precipitation_mm,
    count(*) filter (where precipitation_mm >= 1) as wet_days
from {{ ref('stg_weather_daily') }}
group by city, month, city_month
