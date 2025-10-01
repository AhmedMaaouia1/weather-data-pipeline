FROM quay.io/astronomer/astro-runtime:9.0.0

# Installer dbt Postgres
RUN pip install dbt-postgres==1.8.2

# Installer dbt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt