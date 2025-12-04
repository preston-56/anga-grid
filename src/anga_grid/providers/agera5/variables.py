AGERA5_DEFAULT_VARIABLES: tuple[str, ...] = (
    "temperature_air_mean_daily",
    "temperature_air_min_daily",
    "temperature_air_max_daily",
    "precipitation_flux",
    "solar_radiation_flux",
    "vapour_pressure_daily",
    "wind_speed_10m_mean_daily",
    "relative_humidity_2m_12h",
)

AGERA5_VAR_RENAMES: dict[str, str] = {
    "Temperature_Air_Mean_Daily": "temperature_air_mean_daily",
    "Temperature_Air_Min_Daily": "temperature_air_min_daily",
    "Temperature_Air_Max_Daily": "temperature_air_max_daily",
    "Precipitation_Flux": "precipitation_flux",
    "Solar_Radiation_Flux": "solar_radiation_flux",
    "Vapour_Pressure_Mean": "vapour_pressure_daily",
    "Wind_Speed_10m_Mean": "wind_speed_10m_mean_daily",
    "Relative_Humidity_2m_12h": "relative_humidity_2m_12h",
}
