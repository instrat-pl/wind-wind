import atlite
from wind_wind.consts import atlite_default_turbines
from wind_wind.paths import TURBINES_DIR


def get_turbine_config(turbine_model):
    atlite_defaults = atlite_default_turbines
    if not turbine_model in atlite_defaults:
        turbine_path = TURBINES_DIR / "yaml" / f"{turbine_model}.yaml"
        return atlite.resource.get_windturbineconfig(turbine_path)
    return turbine_model