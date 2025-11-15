from typing import Tuple
from pydantic import BaseModel

LocationCoordinates = Tuple[float, float]


class Location(BaseModel):
    type: str = "Point"
    coordinates: LocationCoordinates = (0.0, 0.0)
