import inspect
from pathlib import Path

PROJECT_DIR = Path(inspect.getframeinfo(inspect.currentframe()).filename).resolve().parents[2]

INPUT_DIR = PROJECT_DIR / "input"

OUTPUT_DIR = PROJECT_DIR / "output"

MODELLED_PROFILES_DIR = OUTPUT_DIR / "modelled_profiles"

CUTOUTS_DIR = INPUT_DIR / "cutouts"

TURBINES_DIR = INPUT_DIR / "turbines"