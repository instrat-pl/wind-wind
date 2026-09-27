from wind_wind.historical import get_generation, get_ARE_capacities
import statistics
from wind_wind.profiles import Wind

cfs = []
turbine_name = "Vestas_V112_3MW"
for year in range(2015, 2026):
    wind_profile = Wind(turbine_name=turbine_name, smooth=False, weather_year=year)
    wind_profile.generate()
    cfs.append(wind_profile.cf)
    print(wind_profile.cf)
print(f"{statistics.mean(cfs)}")