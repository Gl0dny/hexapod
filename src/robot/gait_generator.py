from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Tuple, Optional, Union
import logging
import threading
import time
import math
from enum import Enum, auto
from dataclasses import dataclass
import numpy as np
from abc import ABC, abstractmethod

from utils import rename_thread

logger = logging.getLogger("robot_logger")

if TYPE_CHECKING:
    from robot import Hexapod
    from imu import IMU

class GaitPhase(Enum):
    """
    Represents different phases in a gait cycle.
    
    For tripod gait:
    - TRIPOD_A: Legs 1,3,5 swing, 2,4,6 stance
    - TRIPOD_B: Legs 2,4,6 swing, 1,3,5 stance
    
    For wave gait:
    - WAVE_1 through WAVE_6: Each leg swings individually in sequence
    """
    TRIPOD_A = auto()  # Legs 1,3,5 swing, 2,4,6 stance
    TRIPOD_B = auto()  # Legs 2,4,6 swing, 1,3,5 stance
    WAVE_1 = auto()    # Leg 1 swing
    WAVE_2 = auto()    # Leg 2 swing
    WAVE_3 = auto()    # Leg 3 swing
    WAVE_4 = auto()    # Leg 4 swing
    WAVE_5 = auto()    # Leg 5 swing
    WAVE_6 = auto()    # Leg 6 swing

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
        dot_product = v1.x * v2.x + v1.y * v2.y
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

@dataclass
class GaitState:
    """
    Represents a state in the gait state machine.
    
    Each gait state defines which legs are in swing phase (moving) and which
    are in stance phase (supporting the robot), along with timing parameters.
    
    Attributes:
        phase (GaitPhase): Current phase of the gait cycle
        swing_legs (List[int]): List of leg indices currently in swing phase
        stance_legs (List[int]): List of leg indices currently in stance phase
        dwell_time (float): Time to spend in this state (seconds)
        stability_threshold (float): Maximum allowed IMU deviation for stability
    """
    phase: GaitPhase
    swing_legs: List[int]  # List of leg indices in swing phase
    stance_legs: List[int]  # List of leg indices in stance phase
    dwell_time: float  # Time to spend in this state
    stability_threshold: float  # Maximum allowed IMU deviation

class BaseGait(ABC):
    """
    Base class for all gait patterns with circle-based end effector abstraction.
    
    This class implements the core circle-based targeting system that makes
    hexapod movement direction-independent. Instead of using fixed reference
    positions, legs are projected onto circular workspaces based on movement
    direction, allowing smooth movement in any direction.
    
    Key concepts:
    - Circle-based targeting: Legs are projected onto circular boundaries
    - Direction independence: Same gait works for any movement direction
    - Three-phase path planning: Lift → Travel → Lower for swing legs
    - Vector mathematics: Clean mathematical operations for all calculations
    """
    
    @dataclass
    class LegPath:
        """
        Represents a path for a leg movement with multiple waypoints.
        
        This class manages the smooth trajectory a leg follows from its current position
        to its target position. For swing legs, this typically includes lift, travel, and
        lower phases for natural movement.
        
        Attributes:
            waypoints (List[Vector3D]): List of 3D positions the leg will move through
            current_waypoint_index (int): Index of the current waypoint being executed
        """
        waypoints: List[Vector3D]
        current_waypoint_index: int = 0
        
        def add_waypoint(self, waypoint: Vector3D) -> None:
            """
            Add a waypoint to the path.
            
            Args:
                waypoint (Vector3D): 3D position to add to the path
            """
            self.waypoints.append(waypoint)
        
        def get_current_target(self) -> Vector3D:
            """
            Get the current target waypoint.
            
            Returns:
                Vector3D: Current waypoint, or zero vector if no waypoints exist
            """
            if self.waypoints:
                return self.waypoints[self.current_waypoint_index]
            return Vector3D(0, 0, 0)
        
        def advance_to_next_waypoint(self) -> bool:
            """
            Advance to the next waypoint in the path.
            
            Returns:
                bool: True if there are more waypoints, False if at the end
            """
            if self.current_waypoint_index < len(self.waypoints) - 1:
                self.current_waypoint_index += 1
                return True
            return False
        
        def reset(self) -> None:
            """Reset the path to start from the beginning."""
            self.current_waypoint_index = 0
    
    # Direction mapping for consistent movement vectors
    # Using 1/√2 ≈ 0.707 for diagonal directions to maintain unit magnitude
    DIRECTION_MAP = {
        # Cardinal directions
        'forward': (1.0, 0.0),
        'backward': (-1.0, 0.0),
        'right': (0.0, 1.0),
        'left': (0.0, -1.0),
        
        # Diagonal directions (0.707 = 1/√2 for unit magnitude)
        'diagonal-fr': (0.707, 0.707),    # Forward-Right
        'diagonal-fl': (0.707, -0.707),   # Forward-Left
        'diagonal-br': (-0.707, 0.707),   # Backward-Right
        'diagonal-bl': (-0.707, -0.707),  # Backward-Left
        
        # Stop/neutral
        'stop': (0.0, 0.0),
    }
    
    def __init__(self, hexapod: Hexapod,
                 step_radius: float = 40.0,
                 leg_lift_distance: float = 30.0,
                 leg_lift_incline: float = 2.0,
                 stance_height: float = 0.0,  # Height of stance legs above ground (mm), 0.0 = reference position
                 dwell_time: float = 1.0,
                 stability_threshold: float = 0.2) -> None:
        """
        Initialize the base gait with circle-based parameters.
        
        Args:
            hexapod (Hexapod): The hexapod robot instance
            step_radius (float): Radius of the circular workspace for each leg (mm)
            leg_lift_distance (float): Height legs lift during swing phase (mm)
            leg_lift_incline (float): Incline ratio for smooth leg movement (mm/degree)
            stance_height (float): Height above ground for stance legs (mm). 
                                 A value of 0.0 matches the reference position (starting/home position).
                                 Positive values lower legs (raise body), negative values raise legs (lower body).
            dwell_time (float): Time to spend in each gait phase (seconds)
            stability_threshold (float): Maximum IMU deviation for stability check
        """
        self.hexapod = hexapod
        self.gait_graph: Dict[GaitPhase, List[GaitPhase]] = {}
        
        # Circle-based gait parameters
        self.step_radius = step_radius
        self.leg_lift_distance = leg_lift_distance
        self.leg_lift_incline = leg_lift_incline
        self.stance_height = stance_height
        self.dwell_time = dwell_time
        self.stability_threshold = stability_threshold
        
        # Movement parameters - set by user to control robot movement
        self.direction_input = Vector2D(0, 0)  # Movement direction and speed
        self.rotation_input = 0.0  # Rotation speed (positive = clockwise)
        
        # Leg mounting angles (in degrees, relative to forward direction)
        # Based on your hexagon setup with 137mm side length
        # Legs are mounted at 0°, 60°, 120°, 180°, 240°, 300° in regular hexagon
        self.leg_mount_angles = [i * 60 for i in range(6)]  # Regular hexagon
        
        # Leg paths for three-phase movement - one path per leg
        self.leg_paths: List[self.LegPath] = [self.LegPath([]) for _ in range(6)]
        
        self._setup_gait_graph()

    def project_point_to_circle(self, radius: float, point: Vector2D, direction: Vector2D) -> Vector2D:
        """
        Project a point onto a circle using a direction vector.
        
        This is the core function that creates direction-independent movement.
        It projects a point inside a circle onto the circle's boundary along
        a given direction vector using trigonometry.
        
        The projection ensures that:
        1. The result is always on the circle boundary
        2. The movement follows the desired direction
        3. The projection is mathematically accurate
        
        Args:
            radius (float): Radius of the target circle
            point (Vector2D): Starting point (can be inside or outside circle)
            direction (Vector2D): Direction vector for projection
            
        Returns:
            Vector2D: Point projected onto the circle boundary
            
        Example:
            # Project origin (0,0) in forward direction (1,0) onto circle of radius 80
            result = project_point_to_circle(80.0, Vector2D(0,0), Vector2D(1,0))
            # Returns: Vector2D(80.0, 0.0)
        """
        # No direction for projection -> no calculation
        if direction.magnitude() == 0:
            return point
        
        # If point is at origin or has same direction as input, simple calculation
        if (point.magnitude() == 0 or 
            point.normalized() == direction.normalized() or 
            point.normalized() == direction.normalized() * -1):
            return direction.normalized() * radius
        
        # If direction is too long, clamp it to circle boundary
        if direction.magnitude() > radius - 0.005:
            direction = direction.normalized() * (radius - 0.005)
        
        # Calculate projection using trigonometry (law of sines)
        length_c = point.magnitude()
        angle_beta = 180 - Vector2D.angle_between_vectors(direction, point)
        
        # Calculate missing angles using law of sines
        sin_gamma = (length_c * math.sin(math.radians(angle_beta))) / radius
        angle_gamma = math.degrees(math.asin(sin_gamma))
        angle_alpha = 180 - angle_beta - angle_gamma
        
        # Calculate projection length
        projection_length = (radius * math.sin(math.radians(angle_alpha))) / math.sin(math.radians(angle_beta))
        
        # Return projected point
        return point + direction.normalized() * projection_length
    
    def calculate_leg_target(self, leg_index: int, is_swing: bool) -> Vector3D:
        """
        Calculate the target position for a specific leg using circle-based targeting.
        
        This function determines where each leg should move based on:
        1. Current movement direction and rotation
        2. Whether the leg is in swing or stance phase
        3. The leg's mounting angle in the hexagon
        4. Circle projection onto the workspace boundary
        
        Args:
            leg_index (int): Index of the leg (0-5)
            is_swing (bool): True if leg is in swing phase, False if in stance phase
            
        Returns:
            Vector3D: Target position in 3D space
            
        Note:
            Swing legs project from center outward in movement direction
            Stance legs project from current position in opposite direction
        """
        # If no movement input, maintain current position with proper stance height
        if self.direction_input.magnitude() == 0 and self.rotation_input == 0:
            current_pos = Vector3D(*self.hexapod.current_leg_positions[leg_index])
            current_pos.z = -self.stance_height  # Adjust for stance height
            return current_pos
        
        # Calculate projection direction and origin
        projection_direction = Vector2D(0, 0)
        projection_origin = Vector2D(0, 0)
        
        # Add rotation projection based on leg mounting angle
        rotation_projection = Vector2D(0, 0)
        if self.rotation_input < 0:
            # Counterclockwise rotation: legs move perpendicular to mounting angle
            rotation_projection = Vector2D(1, 0).rotate(self.leg_mount_angles[leg_index] - 90)
        elif self.rotation_input > 0:
            # Clockwise rotation: legs move in opposite perpendicular direction
            rotation_projection = Vector2D(-1, 0).rotate(self.leg_mount_angles[leg_index] - 90)
        
        if is_swing:
            # Swing legs: project from center in movement direction
            projection_direction = self.direction_input + rotation_projection
            projection_origin = Vector2D(0, 0)
        else:
            # Stance legs: project from current position in opposite direction
            projection_direction = self.direction_input.inverse() + rotation_projection.inverse()
            current_pos_2d = Vector2D(*self.hexapod.current_leg_positions[leg_index][:2])
            projection_origin = current_pos_2d
        
        # Project target onto circle
        target_2d = self.project_point_to_circle(self.step_radius, projection_origin, projection_direction)
        
        # Convert to 3D with proper stance height
        target_3d = Vector3D(target_2d.x, target_2d.y, -self.stance_height)
        
        return target_3d
    
    def calculate_leg_path(self, leg_index: int, target: Vector3D, is_swing: bool) -> None:
        """
        Calculate the path for a leg to reach its target.
        
        For swing legs, this creates a three-phase path:
        1. Lift phase: Move up and forward to clear obstacles
        2. Travel phase: Move horizontally to target position
        3. Lower phase: Move down to final target
        
        For stance legs, this creates a direct path to target.
        
        The path ensures smooth, natural leg movement that mimics biological
        walking patterns and avoids jerky transitions.
        
        Args:
            leg_index (int): Index of the leg (0-5)
            target (Vector3D): Target position to reach
            is_swing (bool): True if leg is in swing phase, False if in stance phase
        """
        current_pos = Vector3D(*self.hexapod.current_leg_positions[leg_index])
        path = self.LegPath([])
        
        if is_swing:
            # Calculate three-phase path for swing legs
            current_to_target = target - current_pos
            
            # Calculate lift parameters based on incline ratio
            missing_height = target.z + self.leg_lift_distance - current_pos.z
            distance_from_current_to_lift_xy = abs(missing_height) / self.leg_lift_incline
            distance_from_target_to_lower_xy = self.leg_lift_distance / self.leg_lift_incline
            distance_from_current_to_target_xy = current_to_target.xy_plane().magnitude()
            
            # Determine number of waypoints needed based on distance
            num_waypoints = 0
            step_height = self.leg_lift_distance
            
            if (distance_from_current_to_lift_xy + distance_from_target_to_lower_xy < distance_from_current_to_target_xy and 
                abs(missing_height) > 2):
                # Long distance: need both lift and travel waypoints
                num_waypoints = 2
            elif missing_height < 2:
                # Short distance: adjust step height
                num_waypoints = 1
                step_height = self.leg_lift_distance - ((distance_from_current_to_lift_xy + distance_from_target_to_lower_xy - distance_from_current_to_target_xy) / 2) * self.leg_lift_incline
            else:
                # Medium distance: single travel waypoint
                num_waypoints = 1
                step_height = distance_from_current_to_target_xy * self.leg_lift_incline
            
            # Create waypoints for three-phase movement
            path.add_waypoint(current_pos)  # Phase 1: Start position
            
            if num_waypoints == 2:
                # Phase 2: Lift waypoint (up and forward)
                lift_direction = current_to_target.xy_plane().normalized()
                lift_waypoint = current_pos + lift_direction * (abs(missing_height) / self.leg_lift_incline)
                lift_waypoint.z = current_pos.z + missing_height
                path.add_waypoint(lift_waypoint)
            
            # Phase 3: Travel waypoint (horizontal movement)
            if num_waypoints > 0:
                travel_direction = current_to_target.xy_plane().normalized()
                travel_waypoint = current_pos + travel_direction * (step_height / self.leg_lift_incline)
                travel_waypoint.z = current_pos.z - step_height
                path.add_waypoint(travel_waypoint)
            
            path.add_waypoint(target)  # Phase 4: Final target
            
        else:
            # Direct path for stance legs (no lift needed)
            path.add_waypoint(current_pos)
            path.add_waypoint(target)
        
        self.leg_paths[leg_index] = path

    @abstractmethod
    def _setup_gait_graph(self) -> None:
        """
        Set up the gait graph for the specific gait pattern.
        
        The gait graph defines the state transitions for the gait cycle.
        Each gait pattern (tripod, wave) has different transition rules.
        """
        pass

    @abstractmethod
    def get_state(self, phase: GaitPhase) -> GaitState:
        """
        Get the GaitState for a given phase.
        
        Args:
            phase (GaitPhase): The phase to get state for
            
        Returns:
            GaitState: Complete state information for the phase
        """
        pass

    def set_direction(self, direction: Union[str, Tuple[float, float]], rotation: float = 0.0) -> None:
        """
        Set the movement direction and rotation for the hexapod.
        
        This method updates the movement parameters that control where the robot moves.
        The direction and rotation values are used by all legs to calculate their
        target positions using circle-based projection.
        
        Note: For diagonal movement, the value 0.707 (1/√2) is used to maintain
        unit magnitude. This ensures that diagonal movement has the same speed as
        cardinal directions: √(0.707² + 0.707²) = √(0.5 + 0.5) = √1 = 1.0
        
        Args:
            direction (Union[str, Tuple[float, float]]): Either a direction name or a tuple (x, y)
                
                String names (recommended):
                - 'forward', 'backward', 'left', 'right'
                - 'diagonal-fr', 'diagonal-fl', 'diagonal-br', 'diagonal-bl'
                - 'stop'
                
                Direct tuples:
                - (1, 0): Forward
                - (-1, 0): Backward  
                - (0, 1): Right
                - (0, -1): Left
                - (0.707, 0.707): Diagonal forward-right
                - (0.707, -0.707): Diagonal forward-left
                - (-0.707, 0.707): Diagonal backward-right
                - (-0.707, -0.707): Diagonal backward-left
                
            rotation (float): Rotation speed
                - Positive: Clockwise rotation
                - Negative: Counterclockwise rotation
                - 0: No rotation
                
        Examples:
            gait.set_direction('forward', 0.0)           # Forward movement
            gait.set_direction('diagonal-fr', 0.0)       # Diagonal forward-right
            gait.set_direction((0.5, 0.5), 0.0)         # Custom direction
        """
        if isinstance(direction, str):
            if direction not in self.DIRECTION_MAP:
                available = list(self.DIRECTION_MAP.keys())
                raise ValueError(f"Unknown direction '{direction}'. Available: {available}")
            direction_tuple = self.DIRECTION_MAP[direction]
            self.direction_input = Vector2D(direction_tuple[0], direction_tuple[1])
        elif isinstance(direction, tuple):
            self.direction_input = Vector2D(direction[0], direction[1])
        else:
            raise TypeError(f"Direction must be string or tuple, got {type(direction)}")
        
        self.rotation_input = rotation

class TripodGait(BaseGait):
    """
    Tripod gait pattern where three legs move at a time with circle-based targeting.
    
    Tripod gait is the most stable and efficient gait for hexapods. It divides
    the six legs into two groups of three that alternate between swing and stance
    phases. This provides excellent stability with three legs always supporting
    the robot.
    
    Leg groups:
    - Group A: Legs 0, 2, 4 (1, 3, 5 in 1-based indexing)
    - Group B: Legs 1, 3, 5 (2, 4, 6 in 1-based indexing)
    """
    def __init__(self, hexapod: Hexapod,
                 step_radius: float = 40.0,
                 leg_lift_distance: float = 30.0,
                 leg_lift_incline: float = 2.0,
                 stance_height: float = 0.0,
                 dwell_time: float = 1.0,
                 stability_threshold: float = 0.2) -> None:
        """
        Initialize tripod gait with circle-based parameters.
        
        Tripod gait divides legs into two groups of three that move alternately:
        - Group A: Legs 1, 3, 5 (swing while 2,4,6 stance)
        - Group B: Legs 2, 4, 6 (swing while 1,3,5 stance)
        
        Args:
            hexapod (Hexapod): The hexapod robot instance
            step_radius (float): Radius of circular workspace for each leg (mm)
            leg_lift_distance (float): Height legs lift during swing (mm)
            leg_lift_incline (float): Incline ratio for smooth movement
            stance_height (float): Height above ground for stance (mm). 
                                 A value of 0.0 matches the reference position (starting/home position).
                                 Positive values lower legs (raise body), negative values raise legs (lower body).
            dwell_time (float): Time in each phase (seconds)
            stability_threshold (float): Maximum IMU deviation allowed
        """
        super().__init__(hexapod, step_radius, leg_lift_distance, leg_lift_incline,
                        stance_height, dwell_time, stability_threshold)

    def _setup_gait_graph(self) -> None:
        """
        Set up the tripod gait graph.
        
        Tripod gait has only two phases that alternate:
        TRIPOD_A -> TRIPOD_B -> TRIPOD_A -> ...
        """
        self.gait_graph[GaitPhase.TRIPOD_A] = [GaitPhase.TRIPOD_B]
        self.gait_graph[GaitPhase.TRIPOD_B] = [GaitPhase.TRIPOD_A]

    def get_state(self, phase: GaitPhase) -> GaitState:
        """
        Get the GaitState for a given tripod phase.
        
        Args:
            phase (GaitPhase): Either TRIPOD_A or TRIPOD_B
            
        Returns:
            GaitState: State with appropriate swing/stance leg assignments
        """
        if phase == GaitPhase.TRIPOD_A:
            return GaitState(
                phase=phase,
                swing_legs=[0, 2, 4],  # Legs 1,3,5 (0-based indexing)
                stance_legs=[1, 3, 5],  # Legs 2,4,6
                dwell_time=self.dwell_time,
                stability_threshold=self.stability_threshold
            )
        else:  # TRIPOD_B
            return GaitState(
                phase=phase,
                swing_legs=[1, 3, 5],
                stance_legs=[0, 2, 4],
                dwell_time=self.dwell_time,
                stability_threshold=self.stability_threshold
            )

class WaveGait(BaseGait):
    """
    Wave gait pattern where one leg moves at a time with circle-based targeting.
    
    Wave gait is the most stable but slowest gait pattern. Only one leg is in
    swing phase at any time, with the other five legs providing maximum stability.
    This gait is useful for precise movements or when stability is critical.
    
    Leg sequence: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 1 -> ...
    """
    def __init__(self, hexapod: Hexapod,
                 step_radius: float = 40.0,
                 leg_lift_distance: float = 30.0,
                 leg_lift_incline: float = 2.0,
                 stance_height: float = 0.0,
                 dwell_time: float = 1.0,
                 stability_threshold: float = 0.2) -> None:
        """
        Initialize wave gait with circle-based parameters.
        
        Wave gait moves legs one at a time in sequence for maximum stability:
        - Legs move in order: 1 → 2 → 3 → 4 → 5 → 6
        - Only one leg is in swing phase at any time
        - Provides maximum stability but slower movement
        
        Args:
            hexapod (Hexapod): The hexapod robot instance
            step_radius (float): Radius of circular workspace for each leg (mm)
            leg_lift_distance (float): Height legs lift during swing (mm)
            leg_lift_incline (float): Incline ratio for smooth movement
            stance_height (float): Height above ground for stance (mm). 
                                 A value of 0.0 matches the reference position (starting/home position).
                                 Positive values lower legs (raise body), negative values raise legs (lower body).
            dwell_time (float): Time in each phase (seconds)
            stability_threshold (float): Maximum IMU deviation allowed
        """
        super().__init__(hexapod, step_radius, leg_lift_distance, leg_lift_incline,
                        stance_height, dwell_time, stability_threshold)

    def _setup_gait_graph(self) -> None:
        """
        Set up the wave gait graph.
        
        Wave gait cycles through all six legs in sequence:
        WAVE_1 -> WAVE_2 -> WAVE_3 -> WAVE_4 -> WAVE_5 -> WAVE_6 -> WAVE_1 -> ...
        """
        self.gait_graph[GaitPhase.WAVE_1] = [GaitPhase.WAVE_2]
        self.gait_graph[GaitPhase.WAVE_2] = [GaitPhase.WAVE_3]
        self.gait_graph[GaitPhase.WAVE_3] = [GaitPhase.WAVE_4]
        self.gait_graph[GaitPhase.WAVE_4] = [GaitPhase.WAVE_5]
        self.gait_graph[GaitPhase.WAVE_5] = [GaitPhase.WAVE_6]
        self.gait_graph[GaitPhase.WAVE_6] = [GaitPhase.WAVE_1]

    def get_state(self, phase: GaitPhase) -> GaitState:
        """
        Get the GaitState for a given wave phase.
        
        Args:
            phase (GaitPhase): One of WAVE_1 through WAVE_6
            
        Returns:
            GaitState: State with one swing leg and five stance legs
        """
        swing_leg = {
            GaitPhase.WAVE_1: 0,  # Leg 1
            GaitPhase.WAVE_2: 1,  # Leg 2
            GaitPhase.WAVE_3: 2,  # Leg 3
            GaitPhase.WAVE_4: 3,  # Leg 4
            GaitPhase.WAVE_5: 4,  # Leg 5
            GaitPhase.WAVE_6: 5   # Leg 6
        }[phase]
        
        stance_legs = [i for i in range(6) if i != swing_leg]
        
        return GaitState(
            phase=phase,
            swing_legs=[swing_leg],
            stance_legs=stance_legs,
            dwell_time=self.dwell_time,
            stability_threshold=self.stability_threshold
        )

class GaitGenerator:
    """
    Main gait generator that manages the execution of gait patterns.
    
    This class coordinates the gait state machine, executes leg movements,
    and handles timing and stability monitoring. It runs the gait in a
    separate thread to allow continuous movement while the main program
    continues to run.
    """
    def __init__(self, hexapod: Hexapod, imu: Optional[IMU] = None) -> None:
        """
        Initialize the GaitGenerator with references to the hexapod and IMU.

        Args:
            hexapod (Hexapod): The Hexapod instance to control
            imu (IMU, optional): The IMU instance for stability monitoring
        """
        self.hexapod = hexapod
        self.imu = imu
        self.is_running = False
        self.thread = None
        self.current_state: Optional[GaitState] = None
        self.current_gait: Optional[BaseGait] = None
        self.stop_event: Optional[threading.Event] = None

    def _check_stability(self) -> bool:
        """
        Check if the robot is stable based on IMU readings.
        
        This method monitors accelerometer and gyroscope data to detect
        instability that might cause the robot to fall over.
        
        Returns:
            bool: True if robot is stable, False if instability detected
        """
        if not self.imu:
            return True  # If no IMU, assume stable
        
        # Get current IMU readings
        accel = self.imu.get_acceleration()
        gyro = self.imu.get_gyro()
        
        # Simple stability check - can be enhanced based on specific requirements
        accel_magnitude = np.linalg.norm(accel)
        gyro_magnitude = np.linalg.norm(gyro)
        
        return (abs(accel_magnitude - 9.81) < self.current_state.stability_threshold and
                gyro_magnitude < self.current_state.stability_threshold)

    def _execute_waypoint_movement(self, leg_index: int, waypoints: List[Vector3D], description: str) -> None:
        """
        Execute movement through a series of waypoints for a single leg.
        
        Args:
            leg_index (int): Index of the leg to move
            waypoints (List[Vector3D]): List of waypoints to follow
            description (str): Description of the movement for logging
        """
        print(f"Executing {description} movement for leg {leg_index} through {len(waypoints)} waypoints")
        
        for i, waypoint in enumerate(waypoints):
            print(f"  Leg {leg_index} waypoint {i + 1}/{len(waypoints)}: {waypoint.to_tuple()}")
            
            try:
                self.hexapod.move_leg(leg_index, waypoint.x, waypoint.y, waypoint.z)
                self.hexapod.wait_until_motion_complete()
                time.sleep(0.5)  # Delay between waypoints
                
                print(f"    Leg {leg_index} moved successfully")
                
            except Exception as e:
                print(f"    Error moving leg {leg_index} to waypoint {i + 1}: {e}")
                print(f"    Attempting to return to safe position...")
                from robot.hexapod import PredefinedPosition
                self.hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
                self.hexapod.wait_until_motion_complete()
                raise e
        
        print(f"  Completed {description} movement for leg {leg_index}")

    def _execute_phase(self, state: GaitState) -> None:
        """
        Execute a single gait phase with three-phase path planning.
        
        This method calculates target positions for all legs using circle-based
        targeting and moves them to their new positions. For swing legs, this
        includes the three-phase path planning (lift → travel → lower).
        
        All legs in the same phase (swing or stance) move simultaneously,
        regardless of how many legs are in each phase. This works for any gait pattern:
        - Tripod gait: 3 swing + 3 stance legs move in groups
        - Wave gait: 1 swing + 5 stance legs move in groups
        - Custom gaits: Any number of legs in each phase
        
        Args:
            state (GaitState): The current gait state to execute
        """
        print(f"Executing phase: {state.phase}")
        print(f"Swing legs: {state.swing_legs}")
        print(f"Stance legs: {state.stance_legs}")
        
        # Calculate paths for all legs using circle-based targeting
        swing_paths = {}  # Store paths for swing legs
        stance_paths = {}  # Store paths for stance legs
        
        # Calculate swing paths with three-phase path planning
        for leg_idx in state.swing_legs:
            print(f"\nCalculating swing path for leg {leg_idx}")
            swing_target = self.current_gait.calculate_leg_target(leg_idx, is_swing=True)
            self.current_gait.calculate_leg_path(leg_idx, swing_target, is_swing=True)
            swing_paths[leg_idx] = self.current_gait.leg_paths[leg_idx]
            print(f"Leg {leg_idx} swing path has {len(swing_paths[leg_idx].waypoints)} waypoints")
        
        # Calculate stance paths
        for leg_idx in state.stance_legs:
            print(f"\nCalculating stance path for leg {leg_idx}")
            stance_target = self.current_gait.calculate_leg_target(leg_idx, is_swing=False)
            self.current_gait.calculate_leg_path(leg_idx, stance_target, is_swing=False)
            stance_paths[leg_idx] = self.current_gait.leg_paths[leg_idx]
            print(f"Leg {leg_idx} stance path has {len(stance_paths[leg_idx].waypoints)} waypoints")
        
        # Execute all swing movements simultaneously through waypoints
        if state.swing_legs:
            print(f"\nExecuting swing movements ({len(state.swing_legs)} legs simultaneously):")
            self._execute_group_waypoint_movement(state.swing_legs, swing_paths, "swing")
        
        # Execute all stance movements simultaneously through waypoints
        if state.stance_legs:
            print(f"\nExecuting stance movements ({len(state.stance_legs)} legs simultaneously):")
            self._execute_group_waypoint_movement(state.stance_legs, stance_paths, "stance")

    def _execute_group_waypoint_movement(self, leg_indices: List[int], paths: Dict[int, BaseGait.LegPath], description: str) -> None:
        """
        Execute movement through waypoints for a group of legs simultaneously.
        
        This method moves multiple legs through their waypoints at the same time,
        using move_all_legs for true simultaneous movement. Each leg follows its
        own path independently, and legs that finish their path early stay at
        their final position.
        
        Args:
            leg_indices (List[int]): List of leg indices to move
            paths (Dict[int, BaseGait.LegPath]): Dictionary mapping leg indices to their paths
            description (str): Description of the movement for logging
        """
        print(f"Executing {description} movement for legs {leg_indices} simultaneously")
        
        # Find the maximum number of waypoints across all legs
        max_waypoints = max(len(paths[leg_idx].waypoints) for leg_idx in leg_indices)
        print(f"Maximum waypoints across all legs: {max_waypoints}")
        
        # Track which legs have completed their paths
        completed_legs = set()
        
        # Move through waypoints simultaneously
        for waypoint_idx in range(max_waypoints):
            print(f"  Waypoint {waypoint_idx + 1}/{max_waypoints} for all legs")
            
            # Prepare target positions for all legs at this waypoint
            all_positions = list(self.hexapod.current_leg_positions)  # Start with current positions
            
            for leg_idx in leg_indices:
                path = paths[leg_idx]
                
                if leg_idx in completed_legs:
                    # This leg has completed its path, keep it at final position
                    final_waypoint = path.waypoints[-1]
                    all_positions[leg_idx] = (final_waypoint.x, final_waypoint.y, final_waypoint.z)
                    print(f"    Leg {leg_idx}: {final_waypoint.to_tuple()} (completed, staying at final position)")
                    
                elif waypoint_idx < len(path.waypoints):
                    # This leg has more waypoints to go
                    waypoint = path.waypoints[waypoint_idx]
                    all_positions[leg_idx] = (waypoint.x, waypoint.y, waypoint.z)
                    print(f"    Leg {leg_idx}: {waypoint.to_tuple()}")
                    
                    # Check if this is the final waypoint for this leg
                    if waypoint_idx == len(path.waypoints) - 1:
                        completed_legs.add(leg_idx)
                        print(f"    Leg {leg_idx} completed its path")
                        
                else:
                    # This leg has fewer waypoints, use its final position
                    final_waypoint = path.waypoints[-1]
                    all_positions[leg_idx] = (final_waypoint.x, final_waypoint.y, final_waypoint.z)
                    print(f"    Leg {leg_idx}: {final_waypoint.to_tuple()} (final position)")
                    completed_legs.add(leg_idx)
                    print(f"    Leg {leg_idx} completed its path")
            
            try:
                # Move all legs to their target positions simultaneously
                self.hexapod.move_all_legs(all_positions)
                
                # Wait for all movements to complete
                self.hexapod.wait_until_motion_complete()
                time.sleep(0.5)  # Delay between waypoints
                
                print(f"    All legs moved successfully to waypoint {waypoint_idx + 1}")
                
            except Exception as e:
                print(f"    Error moving legs to waypoint {waypoint_idx + 1}: {e}")
                print(f"    Attempting to return to safe position...")
                from robot.hexapod import PredefinedPosition
                self.hexapod.move_to_position(PredefinedPosition.UPRIGHT)
                self.hexapod.wait_until_motion_complete()
                raise e
        
        print(f"  Completed {description} movement for legs {leg_indices}")

    def start(self, gait: BaseGait, stop_event: Optional[threading.Event] = None) -> None:
        """
        Start the gait generation in a separate thread.

        This method initializes the gait state machine and starts the gait
        execution in a background thread. The gait will continue running
        until stopped or the stop event is set.

        Args:
            gait (BaseGait): The gait instance to execute
            stop_event (threading.Event, optional): Event to signal stopping the gait
        """
        if not self.is_running:
            self.is_running = True
            self.stop_event = stop_event
            self.current_gait = gait
            
            # Set initial state based on gait type
            if isinstance(gait, TripodGait):
                self.current_state = gait.get_state(GaitPhase.TRIPOD_A)
            elif isinstance(gait, WaveGait):
                self.current_state = gait.get_state(GaitPhase.WAVE_1)
            else:
                raise ValueError(f"Unknown gait type: {type(gait)}")
            
            # Start gait execution in background thread
            self.thread = threading.Thread(target=self.run_gait)
            rename_thread(self.thread, f"GaitGenerator-{gait.__class__.__name__}")
            self.thread.start()

    def run_gait(self) -> None:
        """
        Execute the gait pattern continuously.
        
        This is the main gait execution loop that runs in a separate thread.
        It cycles through gait phases, executes leg movements, and handles
        timing and stability monitoring.
        """
        print("Starting gait generation thread")
        while self.is_running:
            if not self.current_state:
                print("No current state set, stopping gait")
                break

            # Check if stop event is set
            if self.stop_event and self.stop_event.is_set():
                print("Stop event detected, stopping gait")
                break

            try:
                # Execute current phase
                self._execute_phase(self.current_state)
                
                # Wait for dwell time or until stability is compromised
                print(f"\nWaiting for dwell time: {self.current_state.dwell_time}s")
                start_time = time.time()
                while (time.time() - start_time < self.current_state.dwell_time and
                       self._check_stability()):
                    # Check stop event during dwell time
                    if self.stop_event and self.stop_event.is_set():
                        print("Stop event detected during dwell time")
                        return
                    time.sleep(0.01)  # Small sleep to prevent CPU hogging

                # Check stop event before transitioning
                if self.stop_event and self.stop_event.is_set():
                    print("Stop event detected before state transition")
                    break

                # Transition to next state
                next_phases = self.current_gait.gait_graph[self.current_state.phase]
                print(f"\nTransitioning to next phase: {next_phases[0]}")
                self.current_state = self.current_gait.get_state(next_phases[0])
                
            except Exception as e:
                print(f"\nError in gait generation: {e}")
                print(f"Current state: {self.current_state}")
                print(f"Current leg positions: {self.hexapod.current_leg_positions}")
                raise

    def stop(self) -> None:
        """
        Stop the gait generation.
        
        This method safely stops the gait execution, waits for the thread
        to finish, and cleans up resources.
        """
        if self.is_running:
            self.is_running = False
            if self.stop_event:
                self.stop_event.set()
            if self.thread:
                self.thread.join()
            self.current_state = None
            self.current_gait = None
            self.stop_event = None