import os
import requests
import psycopg2
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime

# Fonction d'extraction et de chargement
def extract_and_load():
    api_key = os.getenv("WEATHERSTACK_API_KEY", "fake_key")
    if not api_key:
        raise Exception("WEATHERSTACK_API_KEY is not set in environment variables!")
    else:
        print(f"Using API key: {api_key[:4]}... (masked)")
        
    city = "Paris"

    url = f"http://api.weatherstack.com/current?access_key={api_key}&query={city}"
    print(f"Calling URL: {url.replace(api_key, '***')}")
    response = requests.get(url)
    data = response.json()

    if "error" in data:
        raise Exception(f"API Error: {data['error']}")

    location = data.get("location", {})
    current = data.get("current", {})
    air_quality = current.get("air_quality", {})

    # Connexion Postgres (warehouse)
    conn = psycopg2.connect(
        host="warehouse",
        port=5432,
        dbname="weather",
        user="warehouse",
        password="warehouse",
    )
    cur = conn.cursor()

    # Création de la table si elle n'existe pas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw_weather (
            city TEXT,
            country TEXT,
            region TEXT,
            lat DOUBLE PRECISION,
            lon DOUBLE PRECISION,
            timezone_id TEXT,
            local_time TIMESTAMP,

            observation_time TEXT,
            temperature DOUBLE PRECISION,
            feelslike DOUBLE PRECISION,
            humidity DOUBLE PRECISION,
            pressure DOUBLE PRECISION,
            wind_speed DOUBLE PRECISION,
            wind_degree DOUBLE PRECISION,
            wind_dir TEXT,
            cloudcover DOUBLE PRECISION,
            uv_index DOUBLE PRECISION,
            visibility DOUBLE PRECISION,
            is_day TEXT,

            weather_description TEXT,
            weather_code INT,
            weather_icon TEXT,

            co DOUBLE PRECISION,
            no2 DOUBLE PRECISION,
            o3 DOUBLE PRECISION,
            so2 DOUBLE PRECISION,
            pm2_5 DOUBLE PRECISION,
            pm10 DOUBLE PRECISION,
            us_epa_index INT,
            gb_defra_index INT,

            inserted_at TIMESTAMP DEFAULT NOW()
        )
    """)

    # Insertion des données
    cur.execute("""
        INSERT INTO raw_weather (
            city, country, region, lat, lon, timezone_id, local_time,
            observation_time, temperature, feelslike, humidity, pressure,
            wind_speed, wind_degree, wind_dir, cloudcover, uv_index, visibility, is_day,
            weather_description, weather_code, weather_icon,
            co, no2, o3, so2, pm2_5, pm10, us_epa_index, gb_defra_index
        ) VALUES (%s, %s, %s, %s, %s, %s, %s,
                  %s, %s, %s, %s, %s,
                  %s, %s, %s, %s, %s, %s, %s,
                  %s, %s, %s,
                  %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        location.get("name"),
        location.get("country"),
        location.get("region"),
        location.get("lat"),
        location.get("lon"),
        location.get("timezone_id"),
        location.get("localtime"),

        current.get("observation_time"),
        current.get("temperature"),
        current.get("feelslike"),
        current.get("humidity"),
        current.get("pressure"),
        current.get("wind_speed"),
        current.get("wind_degree"),
        current.get("wind_dir"),
        current.get("cloudcover"),
        current.get("uv_index"),
        current.get("visibility"),
        current.get("is_day"),

        (current.get("weather_descriptions") or [None])[0],
        current.get("weather_code"),
        (current.get("weather_icons") or [None])[0],

        air_quality.get("co"),
        air_quality.get("no2"),
        air_quality.get("o3"),
        air_quality.get("so2"),
        air_quality.get("pm2_5"),
        air_quality.get("pm10"),
        air_quality.get("us-epa-index"),
        air_quality.get("gb-defra-index"),
    ))

    conn.commit()
    cur.close()
    conn.close()


# Définition du DAG
with DAG(
    dag_id="extract_weather",
    start_date=datetime(2025, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["weather"],
) as dag:

    extract_task = PythonOperator(
        task_id="extract_and_load",
        python_callable=extract_and_load,
    )
    
    trigger_dbt = TriggerDagRunOperator(
        task_id="trigger_dbt_run",
        trigger_dag_id="dbt_run",  # nom exact de mon deuxième DAG
        wait_for_completion=False  
    )

    extract_task >> trigger_dbt