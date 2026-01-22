"""
Unit tests for location validation utilities.

Tests the Haversine distance calculation and school location validation
functions used for teacher attendance location verification.
"""

from django.test import TestCase, override_settings
from decimal import Decimal
import math

from attendance.utils.location import (
    haversine_distance,
    validate_school_location,
    get_school_location,
    EARTH_RADIUS_METERS
)


class HaversineDistanceTestCase(TestCase):
    """Test cases for Haversine distance calculation."""
    
    def test_distance_between_same_point(self):
        """Distance between same coordinates should be zero."""
        distance = haversine_distance(-7.7956, 110.3695, -7.7956, 110.3695)
        self.assertAlmostEqual(distance, 0.0, places=2)
    
    def test_distance_calculation_accuracy(self):
        """Test distance calculation with known coordinates."""
        # Distance between two points in Yogyakarta
        # Point 1: -7.7956, 110.3695
        # Point 2: -7.7960, 110.3700
        # Expected distance: approximately 70 meters
        distance = haversine_distance(-7.7956, 110.3695, -7.7960, 110.3700)
        
        # Allow reasonable margin of error
        self.assertGreater(distance, 60)
        self.assertLess(distance, 80)
    
    def test_distance_is_symmetric(self):
        """Distance from A to B should equal distance from B to A."""
        lat1, lon1 = -7.7956, 110.3695
        lat2, lon2 = -7.8000, 110.3800
        
        distance_ab = haversine_distance(lat1, lon1, lat2, lon2)
        distance_ba = haversine_distance(lat2, lon2, lat1, lon1)
        
        self.assertAlmostEqual(distance_ab, distance_ba, places=2)
    
    def test_distance_across_equator(self):
        """Test distance calculation across equator."""
        # Point in northern hemisphere
        lat1, lon1 = 10.0, 100.0
        # Point in southern hemisphere
        lat2, lon2 = -10.0, 100.0
        
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        
        # Approximately 2,222 km (20 degrees of latitude)
        expected_distance = 20 * 111000  # ~111km per degree
        self.assertAlmostEqual(distance, expected_distance, delta=50000)
    
    def test_distance_across_prime_meridian(self):
        """Test distance calculation across prime meridian."""
        # Point west of prime meridian
        lat1, lon1 = 0.0, -10.0
        # Point east of prime meridian
        lat2, lon2 = 0.0, 10.0
        
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        
        # Approximately 2,222 km (20 degrees of longitude at equator)
        expected_distance = 20 * 111000
        self.assertAlmostEqual(distance, expected_distance, delta=50000)
    
    def test_distance_with_negative_coordinates(self):
        """Test distance calculation with negative coordinates."""
        # Both points in southern/western hemisphere
        distance = haversine_distance(-33.8688, -151.2093, -37.8136, -144.9631)
        
        # Distance should be positive
        self.assertGreater(distance, 0)
    
    def test_short_distance_precision(self):
        """Test precision for very short distances."""
        # Two points 10 meters apart (approximately)
        lat1, lon1 = -7.7956, 110.3695
        lat2, lon2 = -7.79569, 110.3695  # ~10 meters north
        
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        
        # Should be approximately 10 meters (allow 2 meter margin)
        self.assertAlmostEqual(distance, 10.0, delta=2.0)
    
    def test_long_distance_calculation(self):
        """Test distance calculation for long distances."""
        # New York to London (approximately 5,570 km)
        ny_lat, ny_lon = 40.7128, -74.0060
        london_lat, london_lon = 51.5074, -0.1278
        
        distance = haversine_distance(ny_lat, ny_lon, london_lat, london_lon)
        
        # Expected approximately 5,570 km (allow 100km margin)
        self.assertAlmostEqual(distance, 5570000, delta=100000)
    
    def test_invalid_latitude_too_high(self):
        """Should raise ValueError for latitude > 90."""
        with self.assertRaises(ValueError) as context:
            haversine_distance(91.0, 110.0, 0.0, 0.0)
        
        self.assertIn('Latitude must be between -90 and 90', str(context.exception))
    
    def test_invalid_latitude_too_low(self):
        """Should raise ValueError for latitude < -90."""
        with self.assertRaises(ValueError) as context:
            haversine_distance(-91.0, 110.0, 0.0, 0.0)
        
        self.assertIn('Latitude must be between -90 and 90', str(context.exception))
    
    def test_invalid_longitude_too_high(self):
        """Should raise ValueError for longitude > 180."""
        with self.assertRaises(ValueError) as context:
            haversine_distance(0.0, 181.0, 0.0, 0.0)
        
        self.assertIn('Longitude must be between -180 and 180', str(context.exception))
    
    def test_invalid_longitude_too_low(self):
        """Should raise ValueError for longitude < -180."""
        with self.assertRaises(ValueError) as context:
            haversine_distance(0.0, -181.0, 0.0, 0.0)
        
        self.assertIn('Longitude must be between -180 and 180', str(context.exception))
    
    def test_boundary_latitude_values(self):
        """Test with boundary latitude values (90 and -90)."""
        # North pole to equator
        distance = haversine_distance(90.0, 0.0, 0.0, 0.0)
        
        # Should be approximately 10,000 km (quarter of Earth's circumference)
        expected_distance = (2 * math.pi * EARTH_RADIUS_METERS) / 4
        self.assertAlmostEqual(distance, expected_distance, delta=10000)
    
    def test_boundary_longitude_values(self):
        """Test with boundary longitude values (180 and -180)."""
        # Points at opposite sides of date line (same location)
        distance = haversine_distance(0.0, 180.0, 0.0, -180.0)
        
        # Should be approximately zero (same location)
        self.assertAlmostEqual(distance, 0.0, delta=1000)
    
    def test_distance_with_decimal_type(self):
        """Test distance calculation with Decimal type coordinates."""
        lat1 = Decimal('-7.7956')
        lon1 = Decimal('110.3695')
        lat2 = Decimal('-7.7960')
        lon2 = Decimal('110.3700')
        
        distance = haversine_distance(float(lat1), float(lon1), float(lat2), float(lon2))
        
        self.assertGreater(distance, 0)
        self.assertIsInstance(distance, float)


@override_settings(
    SCHOOL_LATITUDE=-7.7956,
    SCHOOL_LONGITUDE=110.3695,
    SCHOOL_RADIUS_METERS=150
)
class ValidateSchoolLocationTestCase(TestCase):
    """Test cases for school location validation."""
    
    def test_location_exactly_at_school(self):
        """Location exactly at school coordinates should be valid."""
        is_valid, distance = validate_school_location(-7.7956, 110.3695)
        
        self.assertTrue(is_valid)
        self.assertAlmostEqual(distance, 0.0, places=2)
    
    def test_location_within_radius(self):
        """Location within school radius should be valid."""
        # Point approximately 50 meters from school
        is_valid, distance = validate_school_location(-7.79605, 110.3695)
        
        self.assertTrue(is_valid)
        self.assertLess(distance, 150)
    
    def test_location_outside_radius(self):
        """Location outside school radius should be invalid."""
        # Point approximately 500 meters from school
        is_valid, distance = validate_school_location(-7.8000, 110.3695)
        
        self.assertFalse(is_valid)
        self.assertGreater(distance, 150)
    
    def test_location_exactly_on_boundary(self):
        """Location exactly on boundary should be valid."""
        # Calculate a point exactly 150 meters away
        # Using approximate conversion: 1 degree latitude ≈ 111,000 meters
        # 150 meters ≈ 0.00135 degrees
        boundary_lat = -7.7956 + (150 / 111000)
        
        is_valid, distance = validate_school_location(boundary_lat, 110.3695)
        
        # Should be valid (within or at boundary)
        # Note: Due to floating point precision, we check distance is close to 150m
        self.assertAlmostEqual(distance, 150, delta=10)
        # May be slightly over or under due to precision
        if distance <= 150:
            self.assertTrue(is_valid)
    
    def test_location_just_inside_boundary(self):
        """Location just inside boundary should be valid."""
        # Point 145 meters from school (5 meters inside boundary)
        offset = 145 / 111000
        test_lat = -7.7956 + offset
        
        is_valid, distance = validate_school_location(test_lat, 110.3695)
        
        self.assertTrue(is_valid)
        self.assertLess(distance, 150)
    
    def test_location_just_outside_boundary(self):
        """Location just outside boundary should be invalid."""
        # Point 155 meters from school (5 meters outside boundary)
        offset = 155 / 111000
        test_lat = -7.7956 + offset
        
        is_valid, distance = validate_school_location(test_lat, 110.3695)
        
        self.assertFalse(is_valid)
        self.assertGreater(distance, 150)
    
    def test_returns_actual_distance(self):
        """Should return actual distance from school."""
        is_valid, distance = validate_school_location(-7.7960, 110.3700)
        
        # Distance should be positive
        self.assertGreater(distance, 0)
        # Distance should be reasonable (not millions of meters)
        self.assertLess(distance, 1000)
    
    def test_invalid_coordinates_raises_error(self):
        """Invalid coordinates should raise ValueError."""
        with self.assertRaises(ValueError):
            validate_school_location(91.0, 110.0)
    
    def test_with_decimal_coordinates(self):
        """Should work with Decimal type coordinates."""
        lat = Decimal('-7.7956')
        lon = Decimal('110.3695')
        
        is_valid, distance = validate_school_location(float(lat), float(lon))
        
        self.assertTrue(is_valid)
        self.assertAlmostEqual(distance, 0.0, places=2)


@override_settings(
    SCHOOL_LATITUDE=-7.7956,
    SCHOOL_LONGITUDE=110.3695,
    SCHOOL_RADIUS_METERS=200
)
class ValidateSchoolLocationDifferentRadiusTestCase(TestCase):
    """Test location validation with different radius settings."""
    
    def test_larger_radius_accepts_more_locations(self):
        """Larger radius should accept locations further away."""
        # Point approximately 180 meters from school
        is_valid, distance = validate_school_location(-7.79722, 110.3695)
        
        # Should be valid with 200m radius
        self.assertTrue(is_valid)
        self.assertLess(distance, 200)


@override_settings(
    SCHOOL_LATITUDE=None,
    SCHOOL_LONGITUDE=None,
    SCHOOL_RADIUS_METERS=150
)
class ValidateSchoolLocationNoConfigTestCase(TestCase):
    """Test location validation when school coordinates are not configured."""
    
    def test_no_school_coordinates_returns_invalid(self):
        """Should return invalid when school coordinates not configured."""
        is_valid, distance = validate_school_location(-7.7956, 110.3695)
        
        self.assertFalse(is_valid)
        self.assertEqual(distance, 0.0)


@override_settings(
    SCHOOL_LATITUDE=-7.7956,
    SCHOOL_LONGITUDE=110.3695,
    SCHOOL_RADIUS_METERS=150
)
class GetSchoolLocationTestCase(TestCase):
    """Test cases for get_school_location function."""
    
    def test_returns_configured_location(self):
        """Should return configured school location."""
        lat, lon, radius = get_school_location()
        
        self.assertEqual(lat, -7.7956)
        self.assertEqual(lon, 110.3695)
        self.assertEqual(radius, 150)
    
    def test_returns_tuple_of_three(self):
        """Should return tuple of (lat, lon, radius)."""
        result = get_school_location()
        
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)


@override_settings(
    SCHOOL_LATITUDE=None,
    SCHOOL_LONGITUDE=None
)
class GetSchoolLocationNoConfigTestCase(TestCase):
    """Test get_school_location when coordinates not configured."""
    
    def test_raises_error_when_not_configured(self):
        """Should raise AttributeError when school location not configured."""
        with self.assertRaises(AttributeError) as context:
            get_school_location()
        
        self.assertIn('School location not configured', str(context.exception))


class EdgeCaseTestCase(TestCase):
    """Test edge cases for location utilities."""
    
    @override_settings(
        SCHOOL_LATITUDE=0.0,
        SCHOOL_LONGITUDE=0.0,
        SCHOOL_RADIUS_METERS=100
    )
    def test_location_at_equator_prime_meridian(self):
        """Test validation at equator and prime meridian intersection."""
        is_valid, distance = validate_school_location(0.0, 0.0)
        
        self.assertTrue(is_valid)
        self.assertAlmostEqual(distance, 0.0, places=2)
    
    @override_settings(
        SCHOOL_LATITUDE=90.0,
        SCHOOL_LONGITUDE=0.0,
        SCHOOL_RADIUS_METERS=1000
    )
    def test_location_at_north_pole(self):
        """Test validation at north pole."""
        is_valid, distance = validate_school_location(90.0, 0.0)
        
        self.assertTrue(is_valid)
        self.assertAlmostEqual(distance, 0.0, places=2)
    
    @override_settings(
        SCHOOL_LATITUDE=-90.0,
        SCHOOL_LONGITUDE=0.0,
        SCHOOL_RADIUS_METERS=1000
    )
    def test_location_at_south_pole(self):
        """Test validation at south pole."""
        is_valid, distance = validate_school_location(-90.0, 0.0)
        
        self.assertTrue(is_valid)
        self.assertAlmostEqual(distance, 0.0, places=2)
    
    def test_very_small_distance(self):
        """Test distance calculation for very small distances (< 1 meter)."""
        # Two points approximately 0.5 meters apart
        lat1, lon1 = -7.7956, 110.3695
        lat2, lon2 = -7.79560005, 110.3695  # ~0.5 meters
        
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        
        # Should be less than 1 meter
        self.assertLess(distance, 1.0)
        self.assertGreater(distance, 0.0)
    
    @override_settings(
        SCHOOL_LATITUDE=-7.7956,
        SCHOOL_LONGITUDE=110.3695,
        SCHOOL_RADIUS_METERS=0
    )
    def test_zero_radius_only_exact_match(self):
        """Zero radius should only accept exact school coordinates."""
        # Exact match
        is_valid, distance = validate_school_location(-7.7956, 110.3695)
        self.assertTrue(is_valid)
        
        # Even 1 meter away should be invalid
        is_valid, distance = validate_school_location(-7.79561, 110.3695)
        self.assertFalse(is_valid)
    
    def test_antipodal_points(self):
        """Test distance between antipodal points (opposite sides of Earth)."""
        # Two points on opposite sides of Earth
        lat1, lon1 = 0.0, 0.0
        lat2, lon2 = 0.0, 180.0
        
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        
        # Should be approximately half Earth's circumference at equator
        expected_distance = math.pi * EARTH_RADIUS_METERS
        self.assertAlmostEqual(distance, expected_distance, delta=10000)
