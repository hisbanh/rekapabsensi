"""
Unit tests for location validation utilities.

Tests the Haversine distance calculation and school location validation
functions used in the teacher attendance system.
"""

from django.test import TestCase, override_settings
from django.conf import settings
from attendance.utils.location import (
    haversine_distance,
    validate_school_location,
    get_school_location,
    EARTH_RADIUS_METERS
)
import math


class HaversineDistanceTestCase(TestCase):
    """Test cases for Haversine distance calculation."""
    
    def test_same_location_returns_zero(self):
        """Distance between identical coordinates should be zero."""
        distance = haversine_distance(-7.7956, 110.3695, -7.7956, 110.3695)
        self.assertAlmostEqual(distance, 0.0, places=2)
    
    def test_known_distance_yogyakarta(self):
        """Test with known distance in Yogyakarta area."""
        # Two points approximately 1km apart in Yogyakarta
        lat1, lon1 = -7.7956, 110.3695
        lat2, lon2 = -7.8050, 110.3695
        
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        
        # Should be approximately 1045 meters (1.045 km)
        # Allow 5% margin for floating point precision
        expected = 1045
        self.assertAlmostEqual(distance, expected, delta=expected * 0.05)
    
    def test_short_distance_accuracy(self):
        """Test accuracy for short distances (< 200m)."""
        # Two points approximately 100m apart
        lat1, lon1 = -7.7956, 110.3695
        lat2, lon2 = -7.7965, 110.3695
        
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        
        # Should be approximately 100 meters
        self.assertGreater(distance, 90)
        self.assertLess(distance, 110)
    
    def test_equator_distance(self):
        """Test distance calculation at equator."""
        # 1 degree of longitude at equator ≈ 111.32 km
        lat1, lon1 = 0.0, 0.0
        lat2, lon2 = 0.0, 1.0
        
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        
        # Should be approximately 111,320 meters
        expected = 111320
        self.assertAlmostEqual(distance, expected, delta=expected * 0.01)
    
    def test_north_south_distance(self):
        """Test distance calculation for north-south movement."""
        # 1 degree of latitude ≈ 111.32 km everywhere
        lat1, lon1 = -7.0, 110.0
        lat2, lon2 = -6.0, 110.0
        
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        
        # Should be approximately 111,195 meters
        expected = 111195
        self.assertAlmostEqual(distance, expected, delta=expected * 0.01)
    
    def test_invalid_latitude_raises_error(self):
        """Invalid latitude should raise ValueError."""
        with self.assertRaises(ValueError) as context:
            haversine_distance(91.0, 110.0, -7.0, 110.0)
        self.assertIn("Latitude must be between -90 and 90", str(context.exception))
        
        with self.assertRaises(ValueError) as context:
            haversine_distance(-7.0, 110.0, -91.0, 110.0)
        self.assertIn("Latitude must be between -90 and 90", str(context.exception))
    
    def test_invalid_longitude_raises_error(self):
        """Invalid longitude should raise ValueError."""
        with self.assertRaises(ValueError) as context:
            haversine_distance(-7.0, 181.0, -7.0, 110.0)
        self.assertIn("Longitude must be between -180 and 180", str(context.exception))
        
        with self.assertRaises(ValueError) as context:
            haversine_distance(-7.0, 110.0, -7.0, -181.0)
        self.assertIn("Longitude must be between -180 and 180", str(context.exception))
    
    def test_boundary_coordinates(self):
        """Test with boundary coordinate values."""
        # North pole to south pole
        distance = haversine_distance(90.0, 0.0, -90.0, 0.0)
        
        # Should be approximately half Earth's circumference (20,015 km)
        expected = math.pi * EARTH_RADIUS_METERS
        self.assertAlmostEqual(distance, expected, delta=expected * 0.01)
    
    def test_antipodal_points(self):
        """Test distance between antipodal points (opposite sides of Earth)."""
        # Yogyakarta and its antipodal point
        lat1, lon1 = -7.7956, 110.3695
        lat2, lon2 = 7.7956, -69.6305
        
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        
        # Should be approximately half Earth's circumference
        expected = math.pi * EARTH_RADIUS_METERS
        self.assertAlmostEqual(distance, expected, delta=expected * 0.01)
    
    def test_symmetry(self):
        """Distance should be same regardless of point order."""
        lat1, lon1 = -7.7956, 110.3695
        lat2, lon2 = -7.8050, 110.3700
        
        distance1 = haversine_distance(lat1, lon1, lat2, lon2)
        distance2 = haversine_distance(lat2, lon2, lat1, lon1)
        
        self.assertAlmostEqual(distance1, distance2, places=10)


@override_settings(
    SCHOOL_LATITUDE=-7.7956,
    SCHOOL_LONGITUDE=110.3695,
    SCHOOL_RADIUS_METERS=150
)
class ValidateSchoolLocationTestCase(TestCase):
    """Test cases for school location validation."""
    
    def test_exact_school_location_is_valid(self):
        """Exact school coordinates should be valid."""
        is_valid, distance = validate_school_location(-7.7956, 110.3695)
        
        self.assertTrue(is_valid)
        self.assertAlmostEqual(distance, 0.0, places=2)
    
    def test_within_radius_is_valid(self):
        """Location within school radius should be valid."""
        # Point approximately 100m from school
        is_valid, distance = validate_school_location(-7.7965, 110.3695)
        
        self.assertTrue(is_valid)
        self.assertLess(distance, 150)
    
    def test_outside_radius_is_invalid(self):
        """Location outside school radius should be invalid."""
        # Point approximately 500m from school
        is_valid, distance = validate_school_location(-7.8000, 110.3695)
        
        self.assertFalse(is_valid)
        self.assertGreater(distance, 150)
    
    def test_on_boundary_is_valid(self):
        """Location exactly on radius boundary should be valid."""
        # Calculate a point exactly 150m away
        # Using approximate conversion: 1 degree latitude ≈ 111,320 meters
        # 150m ≈ 0.001348 degrees
        lat_offset = 150 / 111320
        
        is_valid, distance = validate_school_location(
            -7.7956 + lat_offset,
            110.3695
        )
        
        # Should be valid (within or at boundary)
        self.assertTrue(is_valid)
        self.assertAlmostEqual(distance, 150, delta=5)
    
    def test_returns_distance(self):
        """Function should return actual distance."""
        is_valid, distance = validate_school_location(-7.7965, 110.3695)
        
        self.assertIsInstance(distance, float)
        self.assertGreater(distance, 0)
    
    def test_invalid_coordinates_raise_error(self):
        """Invalid coordinates should raise ValueError."""
        with self.assertRaises(ValueError):
            validate_school_location(91.0, 110.0)
        
        with self.assertRaises(ValueError):
            validate_school_location(-7.0, 181.0)
    
    @override_settings(SCHOOL_LATITUDE=None, SCHOOL_LONGITUDE=None)
    def test_missing_school_config_returns_invalid(self):
        """Missing school configuration should return invalid."""
        is_valid, distance = validate_school_location(-7.7956, 110.3695)
        
        self.assertFalse(is_valid)
        self.assertEqual(distance, 0.0)
    
    @override_settings(SCHOOL_RADIUS_METERS=200)
    def test_custom_radius(self):
        """Should respect custom radius setting."""
        # Point approximately 180m from school
        is_valid, distance = validate_school_location(-7.7972, 110.3695)
        
        # Should be valid with 200m radius
        self.assertTrue(is_valid)
        self.assertLess(distance, 200)
    
    @override_settings(SCHOOL_RADIUS_METERS=100)
    def test_smaller_radius(self):
        """Should work with smaller radius."""
        # Point approximately 120m from school
        is_valid, distance = validate_school_location(-7.7967, 110.3695)
        
        # Should be invalid with 100m radius
        self.assertFalse(is_valid)
        self.assertGreater(distance, 100)
    
    def test_different_directions(self):
        """Test validation in different directions from school."""
        school_lat = -7.7956
        school_lon = 110.3695
        
        # Small offset in each direction (approximately 50m)
        offset = 50 / 111320
        
        # North
        is_valid_n, _ = validate_school_location(school_lat - offset, school_lon)
        self.assertTrue(is_valid_n)
        
        # South
        is_valid_s, _ = validate_school_location(school_lat + offset, school_lon)
        self.assertTrue(is_valid_s)
        
        # East
        is_valid_e, _ = validate_school_location(school_lat, school_lon + offset)
        self.assertTrue(is_valid_e)
        
        # West
        is_valid_w, _ = validate_school_location(school_lat, school_lon - offset)
        self.assertTrue(is_valid_w)


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
    
    @override_settings(SCHOOL_LATITUDE=None)
    def test_missing_latitude_raises_error(self):
        """Missing latitude should raise AttributeError."""
        with self.assertRaises(AttributeError) as context:
            get_school_location()
        self.assertIn("School location not configured", str(context.exception))
    
    @override_settings(SCHOOL_LONGITUDE=None)
    def test_missing_longitude_raises_error(self):
        """Missing longitude should raise AttributeError."""
        with self.assertRaises(AttributeError) as context:
            get_school_location()
        self.assertIn("School location not configured", str(context.exception))
    
    @override_settings(SCHOOL_RADIUS_METERS=200)
    def test_custom_radius_returned(self):
        """Should return custom radius if configured."""
        lat, lon, radius = get_school_location()
        
        self.assertEqual(radius, 200)
    
    def test_default_radius_if_not_configured(self):
        """Should return default radius if not configured."""
        # Remove SCHOOL_RADIUS_METERS setting
        if hasattr(settings, 'SCHOOL_RADIUS_METERS'):
            delattr(settings, 'SCHOOL_RADIUS_METERS')
        
        lat, lon, radius = get_school_location()
        
        # Default should be 150
        self.assertEqual(radius, 150)


class LocationValidationIntegrationTestCase(TestCase):
    """Integration tests for location validation workflow."""
    
    @override_settings(
        SCHOOL_LATITUDE=-7.7956,
        SCHOOL_LONGITUDE=110.3695,
        SCHOOL_RADIUS_METERS=150
    )
    def test_teacher_at_school_entrance(self):
        """Simulate teacher at school entrance (within radius)."""
        # Coordinates approximately 80m from school center
        teacher_lat = -7.7963
        teacher_lon = 110.3695
        
        is_valid, distance = validate_school_location(teacher_lat, teacher_lon)
        
        self.assertTrue(is_valid)
        self.assertLess(distance, 150)
        self.assertGreater(distance, 50)
    
    @override_settings(
        SCHOOL_LATITUDE=-7.7956,
        SCHOOL_LONGITUDE=110.3695,
        SCHOOL_RADIUS_METERS=150
    )
    def test_teacher_at_nearby_location(self):
        """Simulate teacher at nearby location (outside radius)."""
        # Coordinates approximately 300m from school
        teacher_lat = -7.7983
        teacher_lon = 110.3695
        
        is_valid, distance = validate_school_location(teacher_lat, teacher_lon)
        
        self.assertFalse(is_valid)
        self.assertGreater(distance, 150)
    
    @override_settings(
        SCHOOL_LATITUDE=-7.7956,
        SCHOOL_LONGITUDE=110.3695,
        SCHOOL_RADIUS_METERS=150
    )
    def test_multiple_teachers_different_locations(self):
        """Test validation for multiple teachers at different locations."""
        teachers = [
            (-7.7956, 110.3695, True),   # At school center
            (-7.7960, 110.3695, True),   # 44m away
            (-7.7968, 110.3695, True),   # 133m away - within boundary
            (-7.8000, 110.3695, False),  # 489m away
        ]
        
        for lat, lon, expected_valid in teachers:
            is_valid, distance = validate_school_location(lat, lon)
            
            if expected_valid:
                self.assertTrue(
                    is_valid,
                    f"Expected valid for ({lat}, {lon}) at {distance:.2f}m"
                )
            else:
                self.assertFalse(
                    is_valid,
                    f"Expected invalid for ({lat}, {lon}) at {distance:.2f}m"
                )
