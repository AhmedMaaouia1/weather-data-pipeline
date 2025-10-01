with source as (
    select * from {{ source('raw', 'raw_weather') }}
),

renamed as (
    select
        city,
        country,
        region,
        lat,
        lon,
        timezone_id,
        local_time,
        observation_time,
        temperature,
        feelslike,
        humidity,
        pressure,
        wind_speed,
        wind_degree,
        wind_dir,
        cloudcover,
        uv_index,
        visibility,
        is_day,
        weather_description,
        weather_code,
        weather_icon,
        co,
        no2,
        o3,
        so2,
        pm2_5,
        pm10,
        us_epa_index,
        gb_defra_index,
        inserted_at as loaded_at
    from source
)

select * from renamed
