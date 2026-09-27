from pydantic import BaseModel
from enum import Enum, auto


class CutoutCoords(BaseModel):
    W: float
    E: float
    S: float
    N: float


class AvailabilityMapType(Enum):
    EXISTING = auto()
    POTENTIAL = auto()