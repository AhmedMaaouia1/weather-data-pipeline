# End-to-End Weather Data Pipeline (Airflow + Postgres + dbt + Docker)

J’ai construit un pipeline **ETL/ELT** conteneurisé qui :
- extrait des observations météo depuis l’API *Weatherstack* (Python),
- charge les données brutes dans un **PostgreSQL** utilisé comme *warehouse*,
- transforme les données avec **dbt** (staging → dimension/fact → métriques),
- est orchestré par **Apache Airflow** via **Astro CLI**,
- et s’exécute dans des conteneurs **Docker** grâce à `docker-compose.override.yml`.

![Architecture](weather_data_pipeline.jpeg)

---

## Stack
- **Docker / docker-compose** pour la conteneurisation et le réseau local
- **Astro CLI** pour avoir Airflow prêt à l’emploi en local
- **Airflow** pour l’orchestration des DAGs
- **PostgreSQL (warehouse)** pour le stockage des données
- **dbt (core + postgres adapter)** pour les transformations SQL

---

## Structure du repo
```
.
├─ dags/
│  ├─ extract_weather.py          # DAG d'extract & load (API → warehouse)
│  ├─ dbt_run.py                  # DAG pour dbt run + test
│  └─ analytics_weather.py        # (optionnel) DAG pour les métriques dbt
├─ weather_dbt/                   # Projet dbt
│  ├─ models/
│  │  ├─ staging/...
│  │  └─ marts/...
│  ├─ dbt_project.yml
│  └─ packages.yml
├─ docker-compose.override.yml    # ajoute le service Postgres warehouse
├─ requirements.txt               # libs Airflow image (dbt, psycopg2…)
├─ Dockerfile                     # image Astro Runtime personnalisée
├─ .env.example                   # variables d'env à copier/adapter
├─ .gitignore
└─ README.md
```

---

## Variables d’environnement

J’ai créé un fichier **`.env`** à la racine à partir de **`.env.example`** :

```bash
cp .env.example .env
# puis j’édite .env pour ajouter ma clé API et les mots de passe
```

Extrait de variables :
```dotenv
# Airflow internal Postgres (fourni par Astro)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=airflow

# Warehouse Postgres (mon entrepôt de données)
WAREHOUSE_USER=warehouse
WAREHOUSE_PASSWORD=warehouse
WAREHOUSE_DB=weather
WAREHOUSE_PORT=5433
WAREHOUSE_HOST=warehouse

# API
WEATHERSTACK_API_KEY=CHANGE_ME
```

Astro charge automatiquement `.env` si je l’indique avec `--env .env`.

---

## Docker & Compose

Le fichier **`docker-compose.override.yml`** ajoute un conteneur **Postgres 14** pour le *warehouse* et monte mon projet dbt dans les conteneurs Airflow.

Extrait :  
```yaml
services:
  warehouse:
    image: postgres:14
    env_file:
      - .env
    environment:
      POSTGRES_USER: ${WAREHOUSE_USER}
      POSTGRES_PASSWORD: ${WAREHOUSE_PASSWORD}
      POSTGRES_DB: ${WAREHOUSE_DB}
    ports:
      - "5433:5432"
    volumes:
      - warehouse_data:/var/lib/postgresql/data
```

J’ai choisi le port **5433** pour éviter le conflit avec le Postgres interne d’Airflow (qui tourne sur 5432).

---

## Lancer le projet (Astro + Docker)

1. Installer les prérequis : Docker Desktop et Astro CLI  
2. Construire et démarrer le projet avec les variables d’environnement :  
```bash
astro dev start --no-cache --wait 180s --env .env
```
3. Accéder aux services :  
- Airflow UI → http://localhost:8080 (admin / admin par défaut)  
- Postgres warehouse → `localhost:5433`  
4. Arrêter le projet :  
```bash
astro dev stop
```

---

## Exécuter les DAGs

Depuis l’UI Airflow :  
- `extract_weather` → récupère la météo (ex. Paris) et l’insère dans `raw_weather`.  
- `dbt_run` → lance `dbt run` puis `dbt test` sur le projet `weather_dbt`.  
- `analytics_weather` (optionnel) → calcule et teste `weather_metrics`.  

---

## dbt – structure & commandes utiles

Quelques modèles clés :  
- `models/staging/stg_weather.sql` – projection/renommage + tests de qualité  
- `models/marts/dim_city.sql` – dimension  
- `models/marts/fact_weather.sql` – faits par observation  
- `models/marts/weather_metrics.sql` – métriques (moyennes journalières, anomalies mensuelles, humidex)  

Pour exécuter dbt dans le conteneur scheduler :  
```bash
docker exec -it $(docker ps -qf "name=scheduler") bash
dbt debug --project-dir /usr/app/weather_dbt --profiles-dir /usr/app
dbt run   --project-dir /usr/app/weather_dbt --profiles-dir /usr/app
dbt test  --project-dir /usr/app/weather_dbt --profiles-dir /usr/app
```

Dans mes DAGs, je passe aussi `--no-write-json --log-format text --log-path /tmp --target-path /tmp/target` pour éviter des problèmes de permissions.

---

## Validation rapide

- `select * from analytics.stg_weather limit 5;`  
- `select * from analytics.dim_city limit 5;`  
- `select * from analytics.fact_weather limit 5;`  
- `select * from analytics.analytics.weather_metrics limit 5;` (si le DAG analytics est activé)  

---

## Dépannage (FAQ)

- **Le conteneur `warehouse` redémarre en boucle / demande un mot de passe**  
  → Je vérifie que `.env` est bien chargé par Astro : `astro dev start --env .env`  
  → Je recrée le volume `warehouse_data` si j’ai changé les secrets.  

- **dbt ne se connecte pas**  
  → Dans `profiles.yml` côté conteneurs Airflow, j’utilise `host: warehouse` et `port: 5432`.  
  → Depuis ma machine, j’utilise `host.docker.internal:5433`.  

- **Erreurs de permissions dbt**  
  → J’utilise `--no-write-json`, `--log-path /tmp`, `--target-path /tmp/target` (déjà prévu dans les DAGs).  

---

## Licence
Ce dépôt est un projet personnel à visée éducative. Chacun peut le réutiliser ou l’étendre dans le cadre d’un apprentissage.
