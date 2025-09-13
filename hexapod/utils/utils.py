"""
Utility functions and classes for the Hexapod Voice Control System.

This module provides common utility functions used throughout the hexapod system,
including mathematical operations, threading utilities, and data structures.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import threading
import math
from dataclasses import dataclass

import numpy as np

if TYPE_CHECKING:
    from typing import Tuple, Union

def map_range(value: int, in_min: int, in_max: int, out_min: int, out_max: int) -> int:
        """
        Maps a value from one range to another.
        
        Args:
            value (int): The input value to map.
            in_min (int): The minimum value of the input range.
            in_max (int): The maximum value of the input range.
            out_min (int): The minimum value of the output range.
            out_max (int): The maximum value of the output range.

        Returns:
            int: The mapped value, clamped to the output range.
        """
        if value < in_min:
            return out_min
        elif value > in_max:
            return out_max
        else:
            return (value - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

def parse_percentage(value: Union[str, int]) -> int:
    """
    Parse a percentage value ensuring it's between 0 and 100.
    
    Args:
        value (Union[str, int]): The value to parse, can be a string ending with '%' or an integer.
    
    Returns:
        int: The parsed percentage value.
    
    Raises:
        ValueError: If the value is not a valid percentage.
    """
    if isinstance(value, str) and value.endswith('%'):
        value = value.rstrip('%')
    int_value = int(value)
    if not 0 <= int_value <= 100:
        raise ValueError(f"The parameter for percentage parsing must be between 0 and 100.")
    return int_value
        
def rename_thread(thread: threading.Thread, custom_name: str) -> None:
    """
    Renames the given thread while preserving its original number.

    Args:
        thread (threading.Thread): The thread object to rename.
        custom_name (str): The custom base name for the thread.
    """
    original_name = thread.name

    thread_number = ""
    if original_name.startswith("Thread-"):
        thread_number = original_name.split('-')[1]

    if thread_number:
        thread.name = f"{custom_name}-{thread_number}"
    else:
        thread.name = f"{custom_name}"

def euler_rotation_matrix(roll: float, pitch: float, yaw: float) -> np.ndarray:
    """
    Create a combined rotation matrix from roll, pitch, and yaw angles.
    
    Args:
        roll (float): The roll angle in degrees.
        pitch (float): The pitch angle in degrees.
        yaw (float): The yaw angle in degrees.

    Returns:
        np.ndarray: The combined rotation matrix.
    """
    roll_rad = np.radians(roll)
    pitch_rad = np.radians(pitch)
    yaw_rad = np.radians(yaw)
    
    R_x = np.array([
        [1, 0, 0],
        [0, np.cos(roll_rad), -np.sin(roll_rad)],
        [0, np.sin(roll_rad), np.cos(roll_rad)]
    ])
    
    R_y = np.array([
        [np.cos(pitch_rad), 0, np.sin(pitch_rad)],
        [0, 1, 0],
        [-np.sin(pitch_rad), 0, np.cos(pitch_rad)]
    ])
    
    R_z = np.array([
        [np.cos(yaw_rad), -np.sin(yaw_rad), 0],
        [np.sin(yaw_rad), np.cos(yaw_rad), 0],
        [0, 0, 1]
    ])
    
    return R_z @ R_y @ R_x

def homogeneous_transformation_matrix(tx: float = 0, ty: float = 0, tz: float = 0, roll: float = 0, pitch: float = 0, yaw: float = 0) -> np.ndarray:
    """
    Create a homogeneous transformation matrix from translation and rotation parameters.
    
    Args:
        tx (float, optional): Translation along the x-axis. Defaults to 0.
        ty (float, optional): Translation along the y-axis. Defaults to 0.
        tz (float, optional): Translation along the z-axis. Defaults to 0.
        roll (float, optional): Roll angle in degrees. Defaults to 0.
        pitch (float, optional): Pitch angle in degrees. Defaults to 0.
        yaw (float, optional): Yaw angle in degrees. Defaults to 0.

    Returns:
        np.ndarray: The homogeneous transformation matrix.
    """
    # Create rotation matrix
    R = euler_rotation_matrix(roll, pitch, yaw)
    
    # Create homogeneous transformation matrix
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = [tx, ty, tz]
    
    return T

@dataclass
class Vector2D:
    """
    2D vector for mathematical operations in the X-Y plane.
    
    This class provides essential vector operations for circle-based gait calculations,
    including direction vectors, movement projections, and geometric transformations.
    
    Attributes:
        x (float): X-component of the vector
        y (float): Y-component of the vector
    """
    x: float
    y: float
    
    def __add__(self, other: Vector2D) -> Vector2D:
        """Add two vectors component-wise."""
        return Vector2D(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: Vector2D) -> Vector2D:
        """Subtract two vectors component-wise."""
        return Vector2D(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: float) -> Vector2D:
        """Multiply vector by a scalar."""
        return Vector2D(self.x * scalar, self.y * scalar)
    
    def __truediv__(self, scalar: float) -> Vector2D:
        """Divide vector by a scalar."""
        return Vector2D(self.x / scalar, self.y / scalar)
    
    def magnitude(self) -> float:
        """
        Calculate the magnitude (length) of the vector.
        
        Returns:
            float: The length of the vector using Pythagorean theorem
        """
        return math.sqrt(self.x * self.x + self.y * self.y)
    
    def normalized(self) -> Vector2D:
        """
        Return a normalized version of the vector (unit vector).
        
        A unit vector has magnitude 1 and points in the same direction.
        
        Returns:
            Vector2D: Unit vector in the same direction, or zero vector if original is zero
        """
        mag = self.magnitude()
        if mag == 0:
            return Vector2D(0, 0)
        return Vector2D(self.x / mag, self.y / mag)
    
    def inverse(self) -> Vector2D:
        """
        Return the inverse of the vector (opposite direction).
        
        Returns:
            Vector2D: Vector pointing in the opposite direction
        """
        return Vector2D(-self.x, -self.y)
    
    def dot(self, other: Vector2D) -> float:
        """
        Calculate the dot product with another vector.
        
        Args:
            other (Vector2D): The other vector to dot with
            
        Returns:
            float: Dot product value
        """
        return self.x * other.x + self.y * other.y
    
    def rotate(self, angle_degrees: float) -> Vector2D:
        """
        Rotate the vector by the given angle in degrees.
        
        Uses rotation matrix transformation:
        [cos(θ) -sin(θ)] [x]
        [sin(θ)  cos(θ)] [y]
        
        Args:
            angle_degrees (float): Angle to rotate by in degrees (positive = counterclockwise)
            
        Returns:
            Vector2D: Rotated vector
        """
        angle_rad = math.radians(angle_degrees)
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)
        return Vector2D(
            self.x * cos_angle - self.y * sin_angle,
            self.x * sin_angle + self.y * cos_angle
        )
    
    def to_tuple(self) -> Tuple[float, float]:
        """Convert to tuple for compatibility with existing code."""
        return (self.x, self.y)
    
    @staticmethod
    def angle_between_vectors(v1: Vector2D, v2: Vector2D) -> float:
        """
        Calculate the angle between two vectors in degrees.
        
        Uses dot product formula: cos(θ) = (v1·v2) / (|v1|·|v2|)
        
        Args:
            v1 (Vector2D): First vector
            v2 (Vector2D): Second vector
            
        Returns:
            float: Angle between vectors in degrees (0-180)
        """
        dot_product = v1.dot(v2)
        mag1 = v1.magnitude()
        mag2 = v2.magnitude()
        
        if mag1 == 0 or mag2 == 0:
            return 0
        
        cos_angle = dot_product / (mag1 * mag2)
        cos_angle = max(-1, min(1, cos_angle))  # Clamp to valid range
        return math.degrees(math.acos(cos_angle))


@dataclass
class Vector3D:
    """
    3D vector for representing positions and movements in 3D space.
    
    This class handles 3D coordinates for leg positions, including height (Z-axis)
    for stance height and leg lift calculations.
    
    Attributes:
        x (float): X-component of the vector
        y (float): Y-component of the vector  
        z (float): Z-component of the vector (height)
    """
    x: float
    y: float
    z: float
    
    def __add__(self, other: Vector3D) -> Vector3D:
        """Add two vectors component-wise."""
        return Vector3D(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other: Vector3D) -> Vector3D:
        """Subtract two vectors component-wise."""
        return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar: float) -> Vector3D:
        """Multiply vector by a scalar."""
        return Vector3D(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def __truediv__(self, scalar: float) -> Vector3D:
        """Divide vector by a scalar."""
        return Vector3D(self.x / scalar, self.y / scalar, self.z / scalar)
    
    def magnitude(self) -> float:
        """
        Calculate the magnitude (length) of the vector.
        
        Returns:
            float: The 3D length of the vector
        """
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)
    
    def normalized(self) -> Vector3D:
        """
        Return a normalized version of the vector (unit vector).
        
        Returns:
            Vector3D: Unit vector in the same direction, or zero vector if original is zero
        """
        mag = self.magnitude()
        if mag == 0:
            return Vector3D(0, 0, 0)
        return Vector3D(self.x / mag, self.y / mag, self.z / mag)
    
    def xy_plane(self) -> Vector3D:
        """
        Return the vector with z component set to 0 (projection onto XY plane).
        
        Useful for 2D calculations when height is not relevant.
        
        Returns:
            Vector3D: Vector with same x,y but z=0
        """
        return Vector3D(self.x, self.y, 0)
    
    def to_vector2(self) -> Vector2D:
        """
        Convert to 2D vector by dropping z component.
        
        Returns:
            Vector2D: 2D vector with same x,y components
        """
        return Vector2D(self.x, self.y)
    
    def to_tuple(self) -> Tuple[float, float, float]:
        """Convert to tuple for compatibility with existing code."""
        return (self.x, self.y, self.z)