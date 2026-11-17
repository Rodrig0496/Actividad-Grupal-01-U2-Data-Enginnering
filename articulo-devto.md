---
title: "De una API meteorológica a un tablero público con dbt y DuckDB"
published: false
description: "Construimos un pipeline batch para comparar el clima de tres ciudades peruanas y publicamos el resultado con GitHub Actions y GitHub Pages."
tags: dataengineering, dbt, python, githubactions
---

¿Cómo cambia la precipitación a lo largo del año entre Tacna, Lima y Piura? Para explorarlo construimos **Clima Perú**, un pipeline que toma datos meteorológicos diarios de 2025, los transforma con SQL y publica un tablero junto con el CSV de resultados.

[Ver el tablero](https://rodrig0496.github.io/Actividad-Grupal-01-U2-Data-Enginnering/) · [Explorar el repositorio](https://github.com/Rodrig0496/Actividad-Grupal-01-U2-Data-Enginnering) · [Ver el workflow](https://github.com/Rodrig0496/Actividad-Grupal-01-U2-Data-Enginnering/actions/workflows/pages.yml)

## De la API al modelo diario

Python consulta el archivo histórico de Open-Meteo una vez por ciudad. Pedimos la temperatura máxima y mínima a dos metros, y la precipitación acumulada de cada día. Fijamos `America/Lima` para que el límite de cada día coincida con la hora local, y usamos el reanálisis ERA5 para mantener la misma fuente en las tres ubicaciones. [Documentación de Open-Meteo](https://open-meteo.com/en/docs/historical-weather-api)

Antes de cargar, comparamos las fechas devueltas con el calendario completo y verificamos las unidades. La API entrega las métricas en arreglos paralelos. En Python, `zip(..., strict=True)` hace fallar la ingestión si alguna serie tiene una longitud distinta. La salida esperada son **1.095 filas diarias**, una por cada combinación de ciudad y fecha.

Las filas se cargan en `raw.daily_weather`, dentro de un archivo DuckDB temporal. La base se crea de nuevo en cada ejecución, de modo que volver a procesar 2025 no acumula filas duplicadas. El modelo `stg_weather_daily` expone las columnas que consumen el modelo mensual y las pruebas.

## Del modelo diario al resumen mensual

En `mart_weather_monthly`, dbt usa `ref()` para declarar la dependencia del modelo diario. Este fragmento muestra cómo calculamos dos de las métricas del tablero.

```sql
select
    city,
    cast(date_trunc('month', observed_on) as date) as month,
    round(sum(precipitation_mm), 2) as total_precipitation_mm,
    count(*) filter (where precipitation_mm >= 1) as wet_days
from {{ ref('stg_weather_daily') }}
group by city, month
```

El modelo completo también calcula los promedios mensuales de las máximas y mínimas diarias y cuenta los días incluidos. El resultado tiene **36 filas**, una por cada ciudad y mes. El umbral de 1 mm es una decisión del proyecto para que el conteo de días lluviosos se pueda reproducir a partir de los datos de origen.

En la ejecución de prueba, Piura acumuló **376,6 mm** y registró **74 días con al menos 1 mm**. Febrero y marzo aportaron 94,1 mm cada uno. Lima acumuló 115,1 mm y Tacna, 128,2 mm. El tablero muestra junto al total anual los meses en los que se concentró la lluvia.

## Un fallo de calidad detiene la publicación

`dbt build` ordena los modelos según sus dependencias y ejecuta las pruebas. Las pruebas SQL devuelven las filas que incumplen una condición. Por ejemplo, el conteo mensual debe coincidir con el número de días que tiene ese mes.

```sql
select *
from {{ ref('mart_weather_monthly') }}
where observed_days <> day(last_day(month))
```

Otras pruebas detectan duplicados por ciudad y fecha, claves mensuales ausentes o repetidas, valores nulos o no finitos, temperaturas mínimas mayores que las máximas y precipitación negativa. Si una prueba falla, Python termina con un error antes de generar el artefacto de publicación. [Documentación de `dbt build`](https://docs.getdbt.com/reference/commands/build)

## De GitHub Actions a GitHub Pages

El workflow instala las dependencias y ejecuta `python pipeline.py` en los pull requests y pushes a `main`. En la rama principal, un segundo job depende del primero con `needs: build`. Ese job publica el artefacto que contiene el HTML, el CSS y el CSV. Así, desplegar significa volver a consultar la API, probar los datos y publicar el tablero generado por esa ejecución. [GitHub Pages con workflows personalizados](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)

## Reproducir el pipeline

Clona el repositorio y ejecuta desde la raíz con Python 3.11. Estos comandos son para macOS o Linux. El README incluye los comandos de PowerShell.

```bash
git clone https://github.com/Rodrig0496/Actividad-Grupal-01-U2-Data-Enginnering.git
cd Actividad-Grupal-01-U2-Data-Enginnering
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python pipeline.py
.venv/bin/python -m http.server 8000 --directory site
```

En `http://localhost:8000` puedes recorrer las tablas por ciudad y descargar los resultados mensuales. La misma escala para las barras de precipitación permite comparar un mes de Tacna con uno de Piura. Los datos de ERA5 corresponden a un punto representativo de cada ciudad y las conclusiones se limitan al año 2025. [Datos de reanálisis ERA5](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels)
