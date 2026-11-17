MONTHS = ("Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic")
CITIES_DETAIL = {
    "Tacna": "Costa sur",
    "Lima": "Costa central",
    "Piura": "Costa norte",
}


def number(value, decimals=1):
    return f"{value:.{decimals}f}".replace(".", ",")


def render_city(city, annual, monthly, rain_max):
    max_temp, rain, wet_days = annual
    rows = []
    for _, month, days, maximum, minimum, precipitation, monthly_wet_days in monthly:
        bar_width = precipitation * 100 / rain_max
        rows.append(f"""
            <tr>
              <th scope="row">{MONTHS[month.month - 1]}</th>
              <td>{number(maximum)} °C</td>
              <td>{number(minimum)} °C</td>
              <td class="rain">
                <span>{number(precipitation)} mm</span>
                <span aria-hidden="true" class="bar-track"><span style="--width: {bar_width:.3f}%"></span></span>
              </td>
              <td>{monthly_wet_days} de {days}</td>
            </tr>""")

    return f"""
    <section class="city" id="{city.lower()}" aria-labelledby="heading-{city.lower()}">
      <header class="city-heading">
        <h2 id="heading-{city.lower()}">{city}</h2>
        <p>{CITIES_DETAIL[city]}</p>
      </header>
      <dl class="metrics">
        <div><dt>Máxima diaria media</dt><dd>{number(max_temp)} <span>°C</span></dd></div>
        <div><dt>Precipitación anual</dt><dd>{number(rain)} <span>mm</span></dd></div>
        <div><dt>Días con ≥ 1 mm</dt><dd>{wet_days}</dd></div>
      </dl>
      <div class="table-scroll" role="region" aria-label="Datos mensuales de {city}" tabindex="0">
        <table>
          <thead>
            <tr><th scope="col">Mes</th><th scope="col">Máx. media</th><th scope="col">Mín. media</th>
            <th scope="col">Precipitación</th><th scope="col">Días con ≥ 1 mm</th></tr>
          </thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </div>
    </section>"""


def render_dashboard(year, cities, annual, monthly):
    annual_by_city = {city: values for city, *values in annual}
    rain_max = max(1, *(row[5] for row in monthly))
    links = "\n".join(f'<a href="#{city.lower()}">{city}</a>' for city in cities)
    sections = "\n".join(
        render_city(city, annual_by_city[city], [row for row in monthly if row[0] == city], rain_max)
        for city in cities
    )
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Tablero de temperatura y precipitación para Tacna, Lima y Piura en {year}.">
  <title>Clima Perú · {year}</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="hero">
    <div class="container">
      <p class="period">Enero–diciembre {year}</p>
      <h1>Clima Perú</h1>
      <p class="intro">Temperatura y precipitación en Tacna, Lima y Piura.</p>
      <a class="download" href="clima-mensual.csv" download>Descargar datos mensuales (CSV)</a>
    </div>
  </header>
  <main class="container">
    <nav aria-label="Ciudades">{links}</nav>
    <p class="reading-note">Las barras de precipitación usan la misma escala en las tres ciudades.</p>
    {sections}
  </main>
  <footer class="container">
    <p>Agregaciones propias a partir de datos diarios en hora de Perú. Fuente <a href="https://open-meteo.com/en/docs/historical-weather-api">Open-Meteo</a>, reanálisis <a href="https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels">ERA5 de Copernicus</a>. <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>.</p>
    <a href="https://github.com/Rodrig0496/Actividad-Grupal-01-U2-Data-Enginnering">Código en GitHub</a>
  </footer>
</body>
</html>
"""
