import sqlite3
import pandas as pd
import numpy as np
from wind_wind.paths import OUTPUT_DIR

DEFAULT_DB_PATH = OUTPUT_DIR / 'profiles.db'
DEFAULT_DB_CONN = sqlite3.connect(DEFAULT_DB_PATH)

from typing import Annotated

from sqlmodel import Field, Session, SQLModel, create_engine, select


class WindProfileBase(SQLModel):
    turbine_name: str = Field(index=True)
    weather_year: int = Field(index=True)
    country_code: str = Field(index=True)
    capacity_factor: float

class WindProfile(WindProfileBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    data: bytes

class WindProfileMeta(WindProfileBase):
    id: int  # response model without values

class WindProfileWithValues(WindProfileMeta):
    values: list[float]

engine = create_engine(
    f"sqlite:///{DEFAULT_DB_PATH}",
    connect_args={"check_same_thread": False},  # needed for SQLite with FastAPI
)



def create_db_and_tables():
    SQLModel.metadata.create_all(engine)



def get_session():
    with Session(engine) as session:
        yield session

DTYPE = np.float32

def series_to_bytes(s: pd.Series) -> bytes:
    return s.to_numpy(dtype=DTYPE).tobytes()

def bytes_to_array(b: bytes) -> np.ndarray:
    return np.frombuffer(b, dtype=DTYPE)

