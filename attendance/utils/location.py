"""
Location validation utilities for teacher attendance system.

This module provides functions to validate GPS coordinates against school location
using the Haversine formula to calculate distances on Earth's surface.

The Haversine formula calculates the great-circle distance between two points
on a sphere given their longitudes and latitudes. This is useful for determining
if a teacher is within the school premises when recording attendance.

Formula:
    a = sin²(Δφ/2) + cos φ1 ⋅ cos φ2 ⋅ sin²(Δλ/2)
    c = 2 ⋅ atan2(√a, √(1−a))
    d = R ⋅ c

Where:
    φ = latitude
    λ = longitude
    R = Earth's radius (mean radius = 6,371km)
    Δφ = φ2 - φ1
    Δλ = λ2 - λ1

References:
    - https://en.wikipedia.org/wiki/Haversine_formula
    - https://www.movable-type.co.uk/scripts/latlong.html
"""

from math import radians, cos, sin, asin, sqrt
from typing import Tuple
from django.conf import settings


# Earth's radius in meters (mean radius)
EARTH_RADIUS_METERS = 6371000


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth using the Haversine formula.
    
    This function calculates the shortest distance over the earth's surface between two points,
    giving an "as-the-crow-flies" distance between the points (ignoring any hills, valleys, etc.).
    
    Args:
        lat1: Latitude of first point in decimal degrees (-90 to 90)
        lon1: Longitude of first point in decimal degrees (-180 to 180)
        lat2: Latitude of second point in decimal degrees (-90 to 90)
        lon2: Longitude of second point in decimal degrees (-180 to 180)
    
    Returns:
        Distance between the two points in meters
    
    Raises:
        ValueError: If latitude or longitude values are out of valid range
    
    Example:
        >>> # Distance between two points in Yogyakarta
        >>> distance = haversine_distance(-7.7956, 110.3695, -7.7960, 110.3700)
        >>> print(f"Distance: {distance:.2f} meters")
        Distance: 56.78 meters
    
    Note:
        - Accuracy is typically within 0.5% for distances up to a few hundred kilometers
        - For very short distances (< 1 meter), floating point precision may affect accuracy
        - Does not account for elevation differences
    """
    # Validate input ranges
    if not -90 <= lat1 <= 90 or not -90 <= lat2 <= 90:
        raise ValueError("Latitude must be between -90 and 90 degrees")
    if not -180 <= lon1 <= 180 or not -180 <= lon2 <= 180:
        raise ValueError("Longitude must be between -180 and 180 degrees")
    
    # Convert decimal degrees to radians
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    
    # Calculate differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    
    # Calculate distance in meters
    distance = EARTH_RADIUS_METERS * c
    
    return distance


def validate_school_location(lat: float, lon: float) -> Tuple[bool, float]:
    """
    Validate if given coordinates are within acceptable radius of school location.
    
    This function checks if a teacher's GPS coordinates are within the configured
    radius of the school's location. This is used to verify that teachers are
    physically present at school when recording their attendance.
    
    Args:
        lat: Latitude to validate in decimal degrees (-90 to 90)
        lon: Longitude to validate in decimal degrees (-180 to 180)
    
    Returns:
        Tuple of (is_valid, distance):
            - is_valid: True if within school radius, False otherwise
            - distance: Actual distance from school in meters
    
    Raises:
        ValueError: If latitude or longitude values are out of valid range
        AttributeError: If required settings are not configured
    
    Example:
        >>> # Check if coordinates are within school premises
        >>> is_valid, distance = validate_school_location(-7.7956, 110.3695)
        >>> if is_valid:
        ...     print(f"Valid location, {distance:.2f}m from school center")
        ... else:
        ...     print(f"Invalid location, {distance:.2f}m from school (too far)")
    
    Configuration:
        Requires the following settings in Django settings:
        - SCHOOL_LATITUDE: School's latitude coordinate
        - SCHOOL_LONGITUDE: School's longitude coordinate
        - SCHOOL_RADIUS_METERS: Acceptable radius in meters (default: 150)
    
    Note:
        - Default radius is 150 meters if not configured
        - Returns (False, 0.0) if school coordinates are not configured
        - Distance is always returned as a positive value
    """
    # Get school coordinates from settings
    try:
        school_lat = getattr(settings, 'SCHOOL_LATITUDE', None)
        school_lon = getattr(settings, 'SCHOOL_LONGITUDE', None)
        school_radius = getattr(settings, 'SCHOOL_RADIUS_METERS', 150)
    except AttributeError as e:
        raise AttributeError(
            f"Missing required setting: {e}. "
            "Please configure SCHOOL_LATITUDE, SCHOOL_LONGITUDE, and SCHOOL_RADIUS_METERS in settings."
        )
    
    # Check if school coordinates are configured
    if school_lat is None or school_lon is None:
        # Return invalid if school location is not configured
        # This allows the system to work without location validation
        return False, 0.0
    
    # Calculate distance from school
    try:
        distance = haversine_distance(school_lat, school_lon, lat, lon)
    except ValueError as e:
        # Invalid coordinates provided
        raise ValueError(f"Invalid coordinates: {e}")
    
    # Check if within acceptable radius
    is_valid = distance <= school_radius
    
    return is_valid, distance


def get_school_location() -> Tuple[float, float, float]:
    """
    Get configured school location and radius from settings.
    
    Returns:
        Tuple of (latitude, longitude, radius_meters)
    
    Raises:
        AttributeError: If school location is not configured in settings
    
    Example:
        >>> lat, lon, radius = get_school_location()
        >>> print(f"School at ({lat}, {lon}) with {radius}m radius")
    """
    school_lat = getattr(settings, 'SCHOOL_LATITUDE', None)
    school_lon = getattr(settings, 'SCHOOL_LONGITUDE', None)
    school_radius = getattr(settings, 'SCHOOL_RADIUS_METERS', 150)
    
    if school_lat is None or school_lon is None:
        raise AttributeError(
            "School location not configured. "
            "Please set SCHOOL_LATITUDE and SCHOOL_LONGITUDE in settings."
        )
    
    return school_lat, school_lon, school_radius
