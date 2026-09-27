import pandas as pd
from wind_wind.paths import CUTOUTS_DIR, INPUT_DIR
from wind_wind.profiles import Wind, WindProvince

# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)

wpp = WindProvince()
wpp.generate()

"""
result = []
for turbine_name in ["Vestas_V112_3MW", "2019COE_Market_Average_2.6MW_121"]:
    stats = {}
    wind_profile = Wind(turbine_name=turbine_name, smooth=True)
    wind_profile.generate()
    stats["turbine"] = turbine_name
    stats["cf"] = wind_profile.cf
    result.append(stats)
    wind_profile.save_to_db()
result = pd.DataFrame(result)
print(result)
"""