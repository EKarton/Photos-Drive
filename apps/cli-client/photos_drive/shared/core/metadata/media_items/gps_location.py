from dataclasses import dataclass


@dataclass(frozen=True)
class GpsLocation:
    """
    Represents a GPS location.

    Attributes:
        latitude (float): The latitude in degrees.
        longitude (float): The longitude in degrees.
    """

    latitude: float
    longitude: float
