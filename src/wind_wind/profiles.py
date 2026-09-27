import atlite
import sqlite3
from atlite.gis import ExclusionContainer

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from pydantic import BaseModel, StrictInt, Field
from typing_extensions import TypedDict

from wind_wind.consts import atlite_default_turbines
from wind_wind.paths import TURBINES_DIR, INPUT_DIR, MODELLED_PROFILES_DIR
from wind_wind.cutout import get_cutout
from wind_wind.db import DEFAULT_DB_CONN, WindProfile, Session, get_session, DTYPE, engine, series_to_bytes
from wind_wind.containers import AvailabilityMapType

smooth = {
       "eta":0.950000, 
        "Delta_v":1.0000, 
        "sigma":2.0000
    }

PROVINCES_test = {
    "02": "dolnośląskie",
    "04": "kujawsko-pomorskie",
    "06": "lubelskie",
}


PROVINCES = {
    "02": "dolnośląskie",
    "04": "kujawsko-pomorskie",
    "06": "lubelskie",
    "08": "lubuskie",
    "10": "łódzkie",
    "12": "małopolskie",
    "14": "mazowieckie",
    "16": "opolskie",
    "18": "podkarpackie",
    "20": "podlaskie",
    "22": "pomorskie",
    "24": "śląskie",
    "26": "świętokrzyskie",
    "28": "warmińsko-mazurskie",
    "30": "wielkopolskie",
    "32": "zachodniopomorskie"
}

class SmoothDict(TypedDict):
    eta: float = 0.95,
    Delta_v: float = 1.0,
    sigma: float = 1.0,


class Wind(BaseModel, arbitrary_types_allowed=True):
    weather_year: StrictInt = 2025
    country_code: str = "PL"
    turbine_name: str = "IEA_Reference_3.4MW_130"
    smooth: SmoothDict | bool = False
    cf: float | None = None
    profile: pd.DataFrame | None = None
    conn: sqlite3 = DEFAULT_DB_CONN

    @property
    def border(self):
        # gdf = gpd.read_file(INPUT_DIR / "outlines" / "ne_110m_admin_0_countries.shp")
        gdf = gpd.read_file(INPUT_DIR / "outlines" / "ne_110m_admin_0_countries_lakes.shp")
        border = gdf.loc[gdf["ISO_A2"] == self.country_code, "geometry"]
        return border

    def get_turbine(self):
        turbine_model = self.turbine_name
        atlite_defaults = atlite_default_turbines
        if not turbine_model in atlite_defaults:
            turbine_path = TURBINES_DIR / "yaml" / f"{turbine_model}.yaml"
            return atlite.resource.get_windturbineconfig(turbine_path)
        return turbine_model
    
    def generate(self):
        cutout = get_cutout(self.country_code, self.weather_year)
        excluder = ExclusionContainer()
        border = self.border.geometry.to_crs(excluder.crs)
        masked, transform = excluder.compute_shape_availability(border)
        
        fig, ax = plt.subplots()
        excluder.plot_shape_availability(border)
        cutout.grid.to_crs(excluder.crs).plot(
            edgecolor="grey", color="None", ax=ax, ls=":"
        )

        # Availability matrix
        A = cutout.availabilitymatrix(border, excluder)

        # Cutout preparation
        cutout.prepare()

        # Area & capacity
        # cap_per_sqkm = 7.5
        area = cutout.grid.set_index(["y", "x"]).to_crs(3035).area / 1e6
        area = xr.DataArray(area, dims=("spatial"))
        capacity_matrix = A.stack(spatial=["y", "x"]) * area  # * cap_per_sqkm

        # Profile generation
        turbine_config = self.get_turbine()
        wind = cutout.wind(
            turbine=turbine_config,
            matrix=capacity_matrix,
            index=border.index,
            return_capacity=True,
            smooth=self.smooth,
            # interpolation_method=self.interpolation_method,
            add_cutout_windspeed=True,
            aggregate_time=None
        )
        # Conversion to df
        wind_xr, wind_capacity = wind
        wind_df = wind_xr.to_pandas()
        wind_capacity = wind_capacity.to_pandas()
        wind_capacity_sum = wind_capacity.sum()

        # Profile normalization
        wind_df = wind_df / wind_capacity_sum

        # Remove artefacts from xarray
        wind_df = wind_df.unstack()
        wind_df = wind_df.droplevel("dim_0")

        # Use PyPSA convention for timeseries
        wind_df.index.name = "snapshot"

        self.profile = wind_df
        self.cf = round(wind_df.mean(axis=0)*100, 3)

        turbine_dir = MODELLED_PROFILES_DIR / self.country_code / str(self.weather_year)
        turbine_dir.mkdir(exist_ok=True, parents=True)
        filename = f"{self.country_code}_{self.weather_year}_{self.turbine_name}.csv"
        wind_df.to_csv(turbine_dir / filename)

    
    def save_to_db_2(self):
        conn = self.conn
        values = self.profile.to_numpy(dtype=np.float32)
        conn.execute(
            "INSERT INTO wind_profiles (turbine_name, year, country_code, capacity_factor, data) "
            "VALUES (?, ?, ?, ?, ?)",
            (self.turbine_name, self.weather_year, self.country_code, self.cf, values.tobytes()),
        )
        conn.commit()

        row = conn.execute("SELECT data FROM wind_profiles WHERE id = ?", (1,)).fetchone()
        ts = np.frombuffer(row[0], dtype=np.float32)
        print(ts)

    def save_to_db(self):
        with Session(engine) as session:
            ts = WindProfile(
                turbine_name = self.turbine_name,
                weather_year = self.weather_year,
                country_code = self.country_code,
                capacity_factor = self.cf,
                data=series_to_bytes(self.profile),
            )
            session.add(ts)
            session.commit()



class WindProvince(BaseModel, arbitrary_types_allowed = True):
    weather_year: StrictInt = 2025
    country_code: str = "PL"
    turbine_name: str = "IEA_Reference_3.4MW_130"
    smooth: SmoothDict | bool = False
    cf: float | None = None
    profile: pd.DataFrame | None = None
    availability_maps: AvailabilityMapType | None = None


    def get_province_border(self, teryt):
        gdf = gpd.read_file(INPUT_DIR / "outlines" / "wojewodztwa.shp")
        border = gdf.loc[gdf["JPT_KOD_JE"] == teryt, "geometry"]
        return border

    def get_turbine(self):
        turbine_model = self.turbine_name
        atlite_defaults = atlite_default_turbines
        if not turbine_model in atlite_defaults:
            turbine_path = TURBINES_DIR / "yaml" / f"{turbine_model}.yaml"
            return atlite.resource.get_windturbineconfig(turbine_path)
        return turbine_model
    
    def get_weights(self, year):
        df = pd.read_csv(INPUT_DIR / "weights" / "wind_onshore_URE.csv", index_col="year")
        if year < 2020:
            year = 2020
        elif year > 2025:
            year = 2025
        return df.loc[year]


    def generate_province(self, teryt):
        cutout = get_cutout(self.country_code, self.weather_year)
        excluder = ExclusionContainer()
        if self.availability_maps == AvailabilityMapType.POTENTIAL:
            exclusion_map = INPUT_DIR / "availability_maps" / f"{teryt}_wind_onshore_10.tif"
            excluder.add_raster(exclusion_map, invert=True)
        if self.availability_maps == AvailabilityMapType.EXISTING:
            exclusion_map = INPUT_DIR / "availability_maps" / f"{teryt}_existing_wind_turbines_100m.tif"
            excluder.add_raster(exclusion_map)
        border = self.get_province_border(teryt).geometry.to_crs(excluder.crs)
        masked, transform = excluder.compute_shape_availability(border)
        
        fig, ax = plt.subplots()
        excluder.plot_shape_availability(border)
        cutout.grid.to_crs(excluder.crs).plot(
            edgecolor="grey", color="None", ax=ax, ls=":"
        )
    
        # Availability matrix
        A = cutout.availabilitymatrix(border, excluder)

        # Cutout preparation
        cutout.prepare()

        # Area & capacity
        # cap_per_sqkm = 7.5
        area = cutout.grid.set_index(["y", "x"]).to_crs(3035).area / 1e6
        area = xr.DataArray(area, dims=("spatial"))
        capacity_matrix = A.stack(spatial=["y", "x"]) * area  # * cap_per_sqkm

        # Profile generation
        turbine_config = self.get_turbine()
        wind = cutout.wind(
            turbine=turbine_config,
            matrix=capacity_matrix,
            index=border.index,
            return_capacity=True,
            smooth=self.smooth,
            # interpolation_method=self.interpolation_method,
            add_cutout_windspeed=True,
            aggregate_time=None
        )
        # Conversion to df
        wind_xr, wind_capacity = wind
        wind_df = wind_xr.to_pandas()
        wind_capacity = wind_capacity.to_pandas()
        wind_capacity_sum = wind_capacity.sum()

        # Profile normalization
        wind_df = wind_df / wind_capacity_sum

        # Remove artefacts from xarray
        wind_df = wind_df.unstack()
        wind_df = wind_df.droplevel("dim_0")

        # Use PyPSA convention for timeseries
        wind_df.index.name = "snapshot"

        return wind_df


    def generate(self):
        weights = self.get_weights(self.weather_year)

        profiles = []
        for teryt, province_name in PROVINCES.items():
            profile = self.generate_province(teryt)
            profile.name = f"PL {province_name}"
            profiles.append(profile)
        profiles = pd.concat(profiles, axis=1)
        print(profiles)

        wind_df = profiles.mul(weights).sum(axis=1)

        turbine_dir = MODELLED_PROFILES_DIR / self.country_code / str(self.weather_year)
        turbine_dir.mkdir(exist_ok=True, parents=True)
        filename = f"{self.country_code}_provinces_{self.weather_year}_{self.turbine_name}.csv"
        wind_df.to_csv(turbine_dir / filename)
        self.profile = wind_df
        self.cf = round(wind_df.mean(axis=0)*100, 3)
        return wind_df


    def save_to_db(self):
        with Session(engine) as session:
            ts = WindProfile(
                turbine_name = self.turbine_name,
                weather_year = self.weather_year,
                country_code = self.country_code,
                capacity_factor = self.cf,
                data=series_to_bytes(self.profile),
            )
            session.add(ts)
            session.commit()

