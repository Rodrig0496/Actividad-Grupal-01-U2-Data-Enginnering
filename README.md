# Clima Perú

Pipeline batch que procesa datos meteorológicos diarios de Tacna, Lima y Piura para generar un tablero y un CSV mensual de 2025.

- [Tablero público en GitHub Pages](https://rodrig0496.github.io/Actividad-Grupal-01-U2-Data-Enginnering/)
- [Ejecuciones del pipeline y despliegue](https://github.com/Rodrig0496/Actividad-Grupal-01-U2-Data-Enginnering/actions/workflows/pages.yml)
- [Artículo Markdown para DEV.to](articulo-devto.md)

## Flujo de datos

```text
Open-Meteo Archive API (ERA5, JSON diario)
    → Python valida fechas y unidades
    → DuckDB carga raw.daily_weather
    → dbt transforma y prueba los modelos SQL
    → Python genera el tablero y el CSV mensual
    → GitHub Actions publica el artefacto en GitHub Pages
```

La ingestión consulta tres coordenadas representativas en la zona horaria `America/Lima`. El modelo diario tiene una fila por ciudad y fecha. El modelo mensual genera una fila por ciudad y mes con días cubiertos, promedios de las máximas y mínimas diarias, precipitación acumulada y el conteo de días con al menos 1 mm. El período completo tiene 1.095 filas diarias y 36 mensuales.

Las pruebas de dbt verifican claves únicas, coherencia de temperaturas, precipitación válida y cobertura de cada mes. Cada ejecución crea una base DuckDB temporal y reconstruye el período completo. GitHub Actions despliega únicamente si el pipeline y sus pruebas terminan correctamente.

## Ejecutar en local

Requiere Python 3.11 y acceso a Internet para instalar las dependencias y consultar la API.

En Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe pipeline.py
.\.venv\Scripts\python.exe -m http.server 8000 --directory site
```

En macOS o Linux:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python pipeline.py
.venv/bin/python -m http.server 8000 --directory site
```

Abre [el tablero local](http://localhost:8000). El CSV se genera en `site/clima-mensual.csv`.

## Despliegue automático

En el repositorio, **Settings → Pages → Source** debe estar configurado en **GitHub Actions**. El workflow de `.github/workflows/pages.yml` ejecuta el pipeline en los pull requests a `main` y publica el tablero en cada push a `main`. También se puede lanzar manualmente desde la pestaña **Actions** seleccionando la rama `main`.

GitHub Actions ejecuta Python y dbt. GitHub Pages sirve los archivos estáticos generados en `site/`.

## Fuente y alcance

Los resultados son agregaciones del reanálisis ERA5 para un punto representativo de cada ciudad. Las cifras describen 2025 y pueden diferir de mediciones de estaciones locales. Los datos de origen se ofrecen bajo CC BY 4.0. [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) · [Copernicus ERA5](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels) · [Licencia CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
