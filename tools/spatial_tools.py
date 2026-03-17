"""
Spatial calculation utilities for conservation target analysis.
Provides Haversine distance and coordinate validation.
"""

import math
from typing import Tuple


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance between two GPS coordinates.
    
    Uses Haversine formula to compute the shortest distance over Earth's surface,
    accounting for spherical geometry. More accurate than Euclidean distance for
    navigation and spatial queries.
    
    Args:
        lat1: Latitude of first point in decimal degrees
        lon1: Longitude of first point in decimal degrees
        lat2: Latitude of second point in decimal degrees
        lon2: Longitude of second point in decimal degrees 
    
    Returns:
        Distance in meters between the two points
    
    Example:
        >>> haversine_distance(40.0150, -105.2050, 40.0200, -105.2100)
        621.4  # approximately 621 meters
    """
    R = 6371000  # Earth radius in meters
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = math.sin(delta_lat / 2) ** 2 + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * \
        math.sin(delta_lon / 2) ** 2
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def validate_coordinates(lat: float, lon: float) -> Tuple[bool, str]:
    """
    Verify GPS coordinates are within valid ranges.
    
    Args:
        lat: Latitude to validate
        lon: Longitude to validate
    
    Returns:
        Tuple of (is_valid, error_message)
        If valid, error_message is empty string
    """
    if not -90 <= lat <= 90:
        return False, f"Latitude {lat} out of range [-90, 90]"
    
    if not -180 <= lon <= 180:
        return False, f"Longitude {lon} out of range [-180, 180]"
    
    return True, ""


def format_distance(meters: float) -> str:
    """
    Convert meters to human-readable distance string.
    
    Args:
        meters: Distance in meters
    
    Returns:
        Formatted string (e.g., "45m" or "1.2km")
    """
    if meters < 1000:
        return f"{meters:.0f}m"
    else:
        return f"{meters / 1000:.1f}km"
