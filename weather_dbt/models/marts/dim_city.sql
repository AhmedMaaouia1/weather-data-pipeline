with stg as (
    select distinct
        city,
        country,
        region,
        lat,
        lon,
        timezone_id
    from {{ ref('stg_weather') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['city', 'country', 'region']) }} as city_id,
    city,
    country,
    region,
    lat,
    lon,
    timezone_id
from stg
