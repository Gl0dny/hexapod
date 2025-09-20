"""
Unit tests for utility functions.
"""
import pytest
import threading
import math
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from hexapod.utils.utils import (
    map_range, parse_percentage, rename_thread,
    euler_rotation_matrix, homogeneous_transformation_matrix,
    Vector2D, Vector3D
)


class TestMapRange:
    """Test cases for map_range function."""
    
    def test_map_range_normal_case(self):
        """Test map_range with normal values."""
        result = map_range(50, 0, 100, 0, 255)
        assert result == 127  # (50-0) * (255-0) // (100-0) + 0 = 50 * 255 // 100 = 127
    
    def test_map_range_minimum_value(self):
        """Test map_range with minimum input value."""
        result = map_range(0, 0, 100, 0, 255)
        assert result == 0
    
    def test_map_range_maximum_value(self):
        """Test map_range with maximum input value."""
        result = map_range(100, 0, 100, 0, 255)
        assert result == 255
    
    def test_map_range_below_minimum(self):
        """Test map_range with value below input minimum."""
        result = map_range(-10, 0, 100, 0, 255)
        assert result == 0  # Should clamp to out_min
    
    def test_map_range_above_maximum(self):
        """Test map_range with value above input maximum."""
        result = map_range(150, 0, 100, 0, 255)
        assert result == 255  # Should clamp to out_max
    
    def test_map_range_negative_ranges(self):
        """Test map_range with negative ranges."""
        result = map_range(0, -100, 100, -50, 50)
        assert result == 0  # (0-(-100)) * (50-(-50)) // (100-(-100)) + (-50) = 100 * 100 // 200 - 50 = 0
    
    def test_map_range_same_input_range(self):
        """Test map_range with same input min and max."""
        result = map_range(5, 10, 10, 0, 100)
        assert result == 0  # Should return out_min when in_min == in_max
    
    def test_map_range_middle_value(self):
        """Test map_range with middle value."""
        result = map_range(25, 0, 50, 0, 100)
        assert result == 50  # (25-0) * (100-0) // (50-0) + 0 = 25 * 100 // 50 = 50


class TestParsePercentage:
    """Test cases for parse_percentage function."""
    
    def test_parse_percentage_string_with_percent(self):
        """Test parse_percentage with string ending in %."""
        result = parse_percentage("50%")
        assert result == 50
    
    def test_parse_percentage_string_without_percent(self):
        """Test parse_percentage with string without %."""
        result = parse_percentage("75")
        assert result == 75
    
    def test_parse_percentage_integer(self):
        """Test parse_percentage with integer."""
        result = parse_percentage(25)
        assert result == 25
    
    def test_parse_percentage_minimum_value(self):
        """Test parse_percentage with minimum valid value."""
        result = parse_percentage("0%")
        assert result == 0
    
    def test_parse_percentage_maximum_value(self):
        """Test parse_percentage with maximum valid value."""
        result = parse_percentage("100%")
        assert result == 100
    
    def test_parse_percentage_below_minimum(self):
        """Test parse_percentage with value below 0."""
        with pytest.raises(ValueError, match="The parameter for percentage parsing must be between 0 and 100"):
            parse_percentage("-1%")
    
    def test_parse_percentage_above_maximum(self):
        """Test parse_percentage with value above 100."""
        with pytest.raises(ValueError, match="The parameter for percentage parsing must be between 0 and 100"):
            parse_percentage("101%")
    
    def test_parse_percentage_invalid_string(self):
        """Test parse_percentage with invalid string."""
        with pytest.raises(ValueError):
            parse_percentage("invalid")
    
    def test_parse_percentage_float_string(self):
        """Test parse_percentage with float string."""
        with pytest.raises(ValueError):
            parse_percentage("50.5%")


class TestRenameThread:
    """Test cases for rename_thread function."""
    
    def test_rename_thread_with_number(self):
        """Test rename_thread with thread that has number."""
        thread = threading.Thread()
        thread.name = "Thread-5"
        
        rename_thread(thread, "CustomThread")
        
        assert thread.name == "CustomThread-5"
    
    def test_rename_thread_without_number(self):
        """Test rename_thread with thread without number."""
        thread = threading.Thread()
        thread.name = "SomeOtherName"
        
        rename_thread(thread, "CustomThread")
        
        assert thread.name == "CustomThread"
    
    def test_rename_thread_empty_name(self):
        """Test rename_thread with empty thread name."""
        thread = threading.Thread()
        thread.name = ""
        
        rename_thread(thread, "CustomThread")
        
        assert thread.name == "CustomThread"
    
    def test_rename_thread_custom_name(self):
        """Test rename_thread with custom thread name."""
        thread = threading.Thread()
        thread.name = "MyThread-3"
        
        rename_thread(thread, "Worker")
        
        # The function only extracts numbers from "Thread-" prefixed names
        # Custom names without "Thread-" prefix get the new name without number
        assert thread.name == "Worker"


class TestEulerRotationMatrix:
    """Test cases for euler_rotation_matrix function."""
    
    def test_euler_rotation_matrix_zero_angles(self):
        """Test euler_rotation_matrix with zero angles."""
        result = euler_rotation_matrix(0, 0, 0)
        expected = np.eye(3)
        np.testing.assert_allclose(result, expected, rtol=1e-10)
    
    def test_euler_rotation_matrix_roll_only(self):
        """Test euler_rotation_matrix with roll only."""
        result = euler_rotation_matrix(90, 0, 0)
        expected = np.array([
            [1, 0, 0],
            [0, 0, -1],
            [0, 1, 0]
        ])
        np.testing.assert_allclose(result, expected, atol=1e-15)
    
    def test_euler_rotation_matrix_pitch_only(self):
        """Test euler_rotation_matrix with pitch only."""
        result = euler_rotation_matrix(0, 90, 0)
        expected = np.array([
            [0, 0, 1],
            [0, 1, 0],
            [-1, 0, 0]
        ])
        np.testing.assert_allclose(result, expected, atol=1e-15)
    
    def test_euler_rotation_matrix_yaw_only(self):
        """Test euler_rotation_matrix with yaw only."""
        result = euler_rotation_matrix(0, 0, 90)
        expected = np.array([
            [0, -1, 0],
            [1, 0, 0],
            [0, 0, 1]
        ])
        np.testing.assert_allclose(result, expected, atol=1e-15)
    
    def test_euler_rotation_matrix_combined(self):
        """Test euler_rotation_matrix with combined angles."""
        result = euler_rotation_matrix(30, 45, 60)
        # Test that result is a valid rotation matrix (orthogonal)
        assert np.allclose(np.linalg.det(result), 1.0, rtol=1e-10)  # Determinant should be 1
        assert np.allclose(result @ result.T, np.eye(3), rtol=1e-10)  # Should be orthogonal
    
    def test_euler_rotation_matrix_negative_angles(self):
        """Test euler_rotation_matrix with negative angles."""
        result = euler_rotation_matrix(-30, -45, -60)
        # Test that result is a valid rotation matrix
        assert np.allclose(np.linalg.det(result), 1.0, rtol=1e-10)
        assert np.allclose(result @ result.T, np.eye(3), rtol=1e-10)
    
    def test_euler_rotation_matrix_large_angles(self):
        """Test euler_rotation_matrix with large angles."""
        result = euler_rotation_matrix(360, 720, 180)
        # Should be equivalent to smaller angles due to periodicity
        expected = euler_rotation_matrix(0, 0, 180)
        np.testing.assert_allclose(result, expected, atol=1e-15)


class TestHomogeneousTransformationMatrix:
    """Test cases for homogeneous_transformation_matrix function."""
    
    def test_homogeneous_transformation_matrix_default(self):
        """Test homogeneous_transformation_matrix with default parameters."""
        result = homogeneous_transformation_matrix()
        expected = np.eye(4)
        np.testing.assert_allclose(result, expected, rtol=1e-10)
    
    def test_homogeneous_transformation_matrix_translation_only(self):
        """Test homogeneous_transformation_matrix with translation only."""
        result = homogeneous_transformation_matrix(tx=1, ty=2, tz=3)
        expected = np.array([
            [1, 0, 0, 1],
            [0, 1, 0, 2],
            [0, 0, 1, 3],
            [0, 0, 0, 1]
        ])
        np.testing.assert_allclose(result, expected, rtol=1e-10)
    
    def test_homogeneous_transformation_matrix_rotation_only(self):
        """Test homogeneous_transformation_matrix with rotation only."""
        result = homogeneous_transformation_matrix(roll=90, pitch=0, yaw=0)
        expected = np.array([
            [1, 0, 0, 0],
            [0, 0, -1, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1]
        ])
        np.testing.assert_allclose(result, expected, atol=1e-15)
    
    def test_homogeneous_transformation_matrix_combined(self):
        """Test homogeneous_transformation_matrix with translation and rotation."""
        result = homogeneous_transformation_matrix(tx=1, ty=2, tz=3, roll=30, pitch=45, yaw=60)
        # Test that it's a valid transformation matrix
        assert result.shape == (4, 4)
        assert np.allclose(result[3, :], [0, 0, 0, 1])  # Last row should be [0, 0, 0, 1]
        # Test that rotation part is orthogonal
        rotation_part = result[:3, :3]
        assert np.allclose(rotation_part @ rotation_part.T, np.eye(3), rtol=1e-10)


class TestVector2D:
    """Test cases for Vector2D class."""
    
    def test_init(self):
        """Test Vector2D initialization."""
        v = Vector2D(3.0, 4.0)
        assert v.x == 3.0
        assert v.y == 4.0
    
    def test_add(self):
        """Test vector addition."""
        v1 = Vector2D(1, 2)
        v2 = Vector2D(3, 4)
        result = v1 + v2
        assert result.x == 4
        assert result.y == 6
    
    def test_sub(self):
        """Test vector subtraction."""
        v1 = Vector2D(5, 7)
        v2 = Vector2D(2, 3)
        result = v1 - v2
        assert result.x == 3
        assert result.y == 4
    
    def test_mul(self):
        """Test vector scalar multiplication."""
        v = Vector2D(2, 3)
        result = v * 2.5
        assert result.x == 5.0
        assert result.y == 7.5
    
    def test_truediv(self):
        """Test vector scalar division."""
        v = Vector2D(6, 8)
        result = v / 2
        assert result.x == 3.0
        assert result.y == 4.0
    
    def test_magnitude(self):
        """Test vector magnitude calculation."""
        v = Vector2D(3, 4)
        assert v.magnitude() == 5.0  # 3-4-5 triangle
    
    def test_magnitude_zero(self):
        """Test vector magnitude with zero vector."""
        v = Vector2D(0, 0)
        assert v.magnitude() == 0.0
    
    def test_normalized(self):
        """Test vector normalization."""
        v = Vector2D(3, 4)
        normalized = v.normalized()
        assert abs(normalized.magnitude() - 1.0) < 1e-10
        assert abs(normalized.x - 0.6) < 1e-10
        assert abs(normalized.y - 0.8) < 1e-10
    
    def test_normalized_zero_vector(self):
        """Test normalization of zero vector."""
        v = Vector2D(0, 0)
        normalized = v.normalized()
        assert normalized.x == 0
        assert normalized.y == 0
    
    def test_inverse(self):
        """Test vector inverse."""
        v = Vector2D(2, -3)
        inverse = v.inverse()
        assert inverse.x == -2
        assert inverse.y == 3
    
    def test_dot(self):
        """Test dot product."""
        v1 = Vector2D(1, 2)
        v2 = Vector2D(3, 4)
        result = v1.dot(v2)
        assert result == 11  # 1*3 + 2*4 = 11
    
    def test_rotate(self):
        """Test vector rotation."""
        v = Vector2D(1, 0)  # Pointing right
        rotated = v.rotate(90)  # Rotate 90 degrees counterclockwise
        assert abs(rotated.x) < 1e-10  # Should be pointing up
        assert abs(rotated.y - 1) < 1e-10
    
    def test_rotate_negative_angle(self):
        """Test vector rotation with negative angle."""
        v = Vector2D(1, 0)  # Pointing right
        rotated = v.rotate(-90)  # Rotate 90 degrees clockwise
        assert abs(rotated.x) < 1e-10  # Should be pointing down
        assert abs(rotated.y + 1) < 1e-10
    
    def test_to_tuple(self):
        """Test conversion to tuple."""
        v = Vector2D(2.5, 3.7)
        result = v.to_tuple()
        assert result == (2.5, 3.7)
    
    def test_angle_between_vectors(self):
        """Test angle between vectors calculation."""
        v1 = Vector2D(1, 0)  # Pointing right
        v2 = Vector2D(0, 1)  # Pointing up
        angle = Vector2D.angle_between_vectors(v1, v2)
        assert abs(angle - 90) < 1e-10
    
    def test_angle_between_vectors_parallel(self):
        """Test angle between parallel vectors."""
        v1 = Vector2D(1, 0)
        v2 = Vector2D(2, 0)
        angle = Vector2D.angle_between_vectors(v1, v2)
        assert abs(angle) < 1e-10
    
    def test_angle_between_vectors_opposite(self):
        """Test angle between opposite vectors."""
        v1 = Vector2D(1, 0)
        v2 = Vector2D(-1, 0)
        angle = Vector2D.angle_between_vectors(v1, v2)
        assert abs(angle - 180) < 1e-10
    
    def test_angle_between_vectors_zero_magnitude(self):
        """Test angle between vectors when one has zero magnitude."""
        v1 = Vector2D(0, 0)
        v2 = Vector2D(1, 0)
        angle = Vector2D.angle_between_vectors(v1, v2)
        assert angle == 0


class TestVector3D:
    """Test cases for Vector3D class."""
    
    def test_init(self):
        """Test Vector3D initialization."""
        v = Vector3D(1.0, 2.0, 3.0)
        assert v.x == 1.0
        assert v.y == 2.0
        assert v.z == 3.0
    
    def test_add(self):
        """Test vector addition."""
        v1 = Vector3D(1, 2, 3)
        v2 = Vector3D(4, 5, 6)
        result = v1 + v2
        assert result.x == 5
        assert result.y == 7
        assert result.z == 9
    
    def test_sub(self):
        """Test vector subtraction."""
        v1 = Vector3D(5, 7, 9)
        v2 = Vector3D(2, 3, 4)
        result = v1 - v2
        assert result.x == 3
        assert result.y == 4
        assert result.z == 5
    
    def test_mul(self):
        """Test vector scalar multiplication."""
        v = Vector3D(2, 3, 4)
        result = v * 2.5
        assert result.x == 5.0
        assert result.y == 7.5
        assert result.z == 10.0
    
    def test_truediv(self):
        """Test vector scalar division."""
        v = Vector3D(6, 8, 10)
        result = v / 2
        assert result.x == 3.0
        assert result.y == 4.0
        assert result.z == 5.0
    
    def test_magnitude(self):
        """Test vector magnitude calculation."""
        v = Vector3D(2, 3, 6)
        assert v.magnitude() == 7.0  # sqrt(2^2 + 3^2 + 6^2) = sqrt(49) = 7
    
    def test_magnitude_zero(self):
        """Test vector magnitude with zero vector."""
        v = Vector3D(0, 0, 0)
        assert v.magnitude() == 0.0
    
    def test_normalized(self):
        """Test vector normalization."""
        v = Vector3D(2, 3, 6)
        normalized = v.normalized()
        assert abs(normalized.magnitude() - 1.0) < 1e-10
        assert abs(normalized.x - 2/7) < 1e-10
        assert abs(normalized.y - 3/7) < 1e-10
        assert abs(normalized.z - 6/7) < 1e-10
    
    def test_normalized_zero_vector(self):
        """Test normalization of zero vector."""
        v = Vector3D(0, 0, 0)
        normalized = v.normalized()
        assert normalized.x == 0
        assert normalized.y == 0
        assert normalized.z == 0
    
    def test_xy_plane(self):
        """Test XY plane projection."""
        v = Vector3D(1, 2, 3)
        xy = v.xy_plane()
        assert xy.x == 1
        assert xy.y == 2
        assert xy.z == 0
    
    def test_to_vector2(self):
        """Test conversion to Vector2D."""
        v = Vector3D(1, 2, 3)
        v2 = v.to_vector2()
        assert v2.x == 1
        assert v2.y == 2
        assert isinstance(v2, Vector2D)
    
    def test_to_tuple(self):
        """Test conversion to tuple."""
        v = Vector3D(1.5, 2.5, 3.5)
        result = v.to_tuple()
        assert result == (1.5, 2.5, 3.5)
    
    def test_negative_values(self):
        """Test Vector3D with negative values."""
        v = Vector3D(-1, -2, -3)
        assert v.x == -1
        assert v.y == -2
        assert v.z == -3
        assert v.magnitude() == math.sqrt(14)
    
    def test_float_precision(self):
        """Test Vector3D with floating point precision."""
        v = Vector3D(0.1, 0.2, 0.3)
        result = v * 10
        assert abs(result.x - 1.0) < 1e-10
        assert abs(result.y - 2.0) < 1e-10
        assert abs(result.z - 3.0) < 1e-10