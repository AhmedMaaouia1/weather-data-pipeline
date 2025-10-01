with fact as (
    select
        city_id,
        date_trunc('day', observation_time) as day,
        avg(temperature) as avg_temperature,
        max(wind_speed) as max_wind_speed,
        avg(humidity) as avg_humidity
    from {{ ref('fact_weather') }}
    group by city_id, date_trunc('day', observation_time)
),

monthly_avg as (
    select
        city_id,
        date_trunc('month', day) as month,
        avg(avg_temperature) as monthly_avg_temp
    from fact
    group by city_id, date_trunc('month', day)
),

with_anomaly as (
    select
        f.city_id,
        f.day,
        f.avg_temperature,
        f.max_wind_speed,
        f.avg_humidity,
        m.month,
        m.monthly_avg_temp,
        (f.avg_temperature - m.monthly_avg_temp) as temp_anomaly
    from fact f
    join monthly_avg m
      on f.city_id = m.city_id
     and date_trunc('month', f.day) = m.month
),

humidex as (
    select
        a.*,
        -- Formule corrigée
        (
            a.avg_temperature
            + 0.5555 * (
                6.11 * exp(
                    5417.7530 * (
                        (1/273.16) - (1/(273.15 + (a.avg_temperature - ((100 - a.avg_humidity)/5))))
                    )
                ) - 10
            )
        ) as humidex
    from with_anomaly a
)

select * from humidex
