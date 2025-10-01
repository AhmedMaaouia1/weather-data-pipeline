with stg as (
    select * from {{ ref('stg_weather') }}
),

dim as (
    select * from {{ ref('dim_city') }}
),

fact as (
    select
        d.city_id,
        s.local_time::timestamp as observation_time,

        -- Mesures météo
        s.temperature,
        s.feelslike,
        s.humidity,
        s.pressure,
        s.wind_speed,
        s.wind_degree,
        s.wind_dir,
        s.cloudcover,
        s.uv_index,
        s.visibility,
        s.is_day,

        -- Conditions météo
        s.weather_description,
        s.weather_code,
        s.weather_icon,

        -- Qualité de l’air
        s.co,
        s.no2,
        s.o3,
        s.so2,
        s.pm2_5,
        s.pm10,
        s.us_epa_index,
        s.gb_defra_index,

        -- Audit
        s.loaded_at
    from stg s
    left join dim d using (city, country, region, lat, lon, timezone_id)
)

select * from fact
