# https://atlite.readthedocs.io/en/master/examples/landuse-availability.html
from pathlib import Path
import os
import atlite
import logging
from wind_wind.containers import CutoutCoords
from wind_wind.paths import CUTOUTS_DIR

logging.basicConfig(level=logging.INFO)

import cdsapi


PL_COORDS = CutoutCoords(
    S = 49.0,
    N = 55.0,
    W = 14.0,
    E = 24.25,
)

def get_cutout(
    country_code: str = "PL", 
    year: int = 2025, 
    coords: CutoutCoords = PL_COORDS, 
    cutout_dir: Path = CUTOUTS_DIR,
    cutout_name: str | None = None,
    ) -> atlite.Cutout:
    os.makedirs(cutout_dir, exist_ok=True)
    
    if cutout_name is None:
        cutout_name = f"{country_code}_{year}.nc"
    
    cutout_path = cutout_dir / cutout_name

    if cutout_path.is_file():
        print(f"Cutout {cutout_name} exists.")
        cutout = atlite.Cutout(cutout_path)
    else:
        print(f"Cutout {cutout_name} doesn't exist. Downloading...")
        client = cdsapi.Client()
        cutout = atlite.Cutout(
            cutout_path,
            module="era5", 
            crs=3035, x=slice(coords.W, coords.E), y=slice(coords.S, coords.N), 
            time=slice(f"{year}-01-01", f"{year}-12-31")
        )
        print(cutout.data)

        cutout.prepare(data_format="grib", show_progress=True)
        print(f"Cutout {cutout_name} downloaded.")

    print(f"Cutout {cutout_name} loaded.")

    return cutout
