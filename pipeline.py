import csv
import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb
import requests

from dashboard import render_dashboard


ROOT = Path(__file__).resolve().parent
YEAR = 2025
START = date(YEAR, 1, 1)
END = date(YEAR, 12, 31)
CITIES = {
    "Tacna": (-18.01, -70.25),
    "Lima": (-12.05, -77.04),
    "Piura": (-5.19, -80.63),
}
VARIABLES = {
    "temperature_2m_max": "°C",
    "temperature_2m_min": "°C",
    "precipitation_sum": "mm",
}


def extract_city(city, latitude, longitude):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": START,
        "end_date": END,
        "daily": ",".join(VARIABLES),
        "timezone": "America/Lima",
        "models": "era5",
    }
    endpoint = "https://archive-api.open-meteo.com/v1/archive"
    print(f"Consultando Open-Meteo para {city}", flush=True)
    response = requests.get(endpoint, params=params, timeout=45)
    response.raise_for_status()
    payload = response.json()

    daily = payload["daily"]
    expected_dates = [
        (START + timedelta(days=offset)).isoformat()
        for offset in range((END - START).days + 1)
    ]
    if daily["time"] != expected_dates:
        raise ValueError(f"{city}: la respuesta no cubre todas las fechas esperadas")
    if any(payload["daily_units"].get(key) != unit for key, unit in VARIABLES.items()):
        raise ValueError(f"{city}: unidades inesperadas en la respuesta")

    return [
        (city, day, maximum, minimum, rain)
        for day, maximum, minimum, rain in zip(
            daily["time"], *(daily[key] for key in VARIABLES), strict=True
        )
    ]


def load_weather(database_path, rows):
    with duckdb.connect(str(database_path)) as connection:
        connection.execute("create schema raw")
        connection.execute("""
            create table raw.daily_weather (
                city varchar,
                observed_on date,
                temperature_max_c double,
                temperature_min_c double,
                precipitation_mm double
            )
        """)
        connection.executemany("insert into raw.daily_weather values (?, ?, ?, ?, ?)", rows)


def transform(database_path, work_dir):
    subprocess.run([
        sys.executable, "-c", "from dbt.cli.main import cli; cli()", "build",
        "--project-dir", str(ROOT / "dbt"), "--profiles-dir", str(ROOT / "dbt"),
        "--target-path", str(work_dir / "target"), "--log-path", str(work_dir / "logs"),
        "--no-send-anonymous-usage-stats", "--no-use-colors",
    ], check=True, env={**os.environ, "CLIMA_DUCKDB_PATH": str(database_path)})


def export_site(database_path):
    with duckdb.connect(str(database_path), read_only=True) as connection:
        result = connection.execute("""
            select city, month, observed_days, avg_max_c, avg_min_c,
                   total_precipitation_mm, wet_days
            from analytics.mart_weather_monthly
            order by city, month
        """)
        columns = [column[0] for column in result.description]
        monthly = result.fetchall()
        annual = connection.execute("""
            select city, round(avg(temperature_max_c), 1),
                   round(sum(precipitation_mm), 1),
                   count(*) filter (where precipitation_mm >= 1)
            from analytics.stg_weather_daily
            group by city
        """).fetchall()

    if len(monthly) != len(CITIES) * 12:
        raise ValueError(f"Se esperaban {len(CITIES) * 12} filas mensuales")

    site = ROOT / "site"
    site.mkdir(exist_ok=True)
    with (site / "clima-mensual.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        writer.writerows(monthly)
    (site / "index.html").write_text(render_dashboard(YEAR, CITIES, annual, monthly), encoding="utf-8")
    (site / "styles.css").write_bytes((ROOT / "dashboard.css").read_bytes())
    print(f"Tablero y CSV generados en {site} ({len(monthly)} filas mensuales)", flush=True)


def main():
    rows = [row for city, coords in CITIES.items() for row in extract_city(city, *coords)]
    with TemporaryDirectory(prefix="clima-", dir=ROOT) as temp_dir:
        work_dir = Path(temp_dir)
        database_path = work_dir / "clima.duckdb"
        load_weather(database_path, rows)
        transform(database_path, work_dir)
        export_site(database_path)


if __name__ == "__main__":
    main()
