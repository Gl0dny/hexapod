from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Tuple, Union
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto

from utils import Vector2D, Vector3D

if TYPE_CHECKING:
    from robot import Hexapod

class GaitPhase(Enum):
    """
    Represents different phases in a gait cycle.
    
    For tripod gait:
    - TRIPOD_A: Legs 0,2,4 swing, 1,3,5 stance (Right, Left Front, Left Back)
    - TRIPOD_B: Legs 1,3,5 swing, 0,2,4 stance (Right Front, Left, Right Back)
    
    For wave gait:
    - WAVE_1 through WAVE_6: Each leg swings individually in sequence
    """
    TRIPOD_A = auto()  # Legs 0,2,4 swing, 1,3,5 stance
    TRIPOD_B = auto()  # Legs 1,3,5 swing, 0,2,4 stance
    WAVE_1 = auto()    # Leg 0 swing (Right)
    WAVE_2 = auto()    # Leg 1 swing (Right Front)
    WAVE_3 = auto()    # Leg 2 swing (Left Front)
    WAVE_4 = auto()    # Leg 3 swing (Left)
    WAVE_5 = auto()    # Leg 4 swing (Left Back)
    WAVE_6 = auto()    # Leg 5 swing (Right Back)


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
    # Coordinate system: +X = Right, +Y = Forward, +Z = Up
    DIRECTION_MAP = {
        # Cardinal directions
        'forward': (0.0, 1.0),    # +Y direction
        'backward': (0.0, -1.0),  # -Y direction
        'right': (1.0, 0.0),      # +X direction
        'left': (-1.0, 0.0),      # -X direction
        
        # Diagonal directions (0.707 = 1/√2 for unit magnitude)
        'diagonal-fr': (0.707, 0.707),    # Forward-Right
        'diagonal-fl': (-0.707, 0.707),   # Forward-Left
        'diagonal-br': (0.707, -0.707),   # Backward-Right
        'diagonal-bl': (-0.707, -0.707),  # Backward-Left
        
        # Stop/neutral
        'stop': (0.0, 0.0),
    }
    
    def __init__(self, hexapod: Hexapod,
                 step_radius: float = 30.0,
                 leg_lift_distance: float = 10.0,
                 leg_lift_incline: float = 2.0,
                 stance_height: float = 0.0,  # Height of stance legs above ground (mm), 0.0 = reference position
                 dwell_time: float = 0.5,
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
        # Based on hexagon setup with 137mm side length
        # Legs are mounted at 0°, 60°, 120°, 180°, 240°, 300° in regular hexagon
        # Leg 0: Right (0°), Leg 1: Right Front (60°), Leg 2: Left Front (120°)
        # Leg 3: Left (180°), Leg 4: Left Back (240°), Leg 5: Right Back (300°)
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
        
        # Handle edge case where angle_beta is 0° or 180° (sin = 0)
        if abs(angle_beta) < 0.1 or abs(angle_beta - 180) < 0.1:
            # Direction and point are collinear, use simple projection
            return direction.normalized() * radius
        
        # Calculate missing angles using law of sines
        sin_gamma = (length_c * math.sin(math.radians(angle_beta))) / radius
        
        # Clamp sin_gamma to valid range [-1, 1] to prevent math domain error
        sin_gamma = max(-1.0, min(1.0, sin_gamma))
        
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
        
        For translation movement:
        - Each leg projects the global movement direction into its local coordinate system
        - The projection accounts for the leg's mounting angle relative to robot's forward direction
        - Swing legs move in the projected direction, stance legs move in opposite direction
        
        Args:
            leg_index (int): Index of the leg (0-5)
            is_swing (bool): True if leg is in swing phase, False if in stance phase
            
        Returns:
            Vector3D: Target position in 3D space
        """
        # If no movement input, maintain current position with proper stance height
        if self.direction_input.magnitude() == 0 and self.rotation_input == 0:
            current_pos = Vector3D(*self.hexapod.current_leg_positions[leg_index])
            current_pos.z = -self.stance_height  # Adjust for stance height
            return current_pos
        
        # Get the leg's mounting angle (in degrees)
        leg_angle_deg = self.leg_mount_angles[leg_index]
        leg_angle_rad = math.radians(leg_angle_deg)
        
        # Calculate projection direction and origin
        projection_direction = Vector2D(0, 0)
        projection_origin = Vector2D(0, 0)
        
        if self.rotation_input != 0:
            # Handle rotation movement
            # For rotation, all legs move in the same relative direction regardless of mounting angle
            if self.rotation_input > 0:  # Clockwise rotation
                rotation_projection = Vector2D(1, 0)  # Right in local coordinate system
            else:  # Counterclockwise rotation
                rotation_projection = Vector2D(-1, 0)   # Left in local coordinate system
            
            if is_swing:
                # Swing legs: project from center in rotation direction
                projection_direction = rotation_projection
                projection_origin = Vector2D(0, 0)
            else:
                # Stance legs: project from current position in opposite rotation direction
                projection_direction = rotation_projection.inverse()
                current_pos_2d = Vector2D(*self.hexapod.current_leg_positions[leg_index][:2])
                projection_origin = current_pos_2d
        else:
            # Handle translation movement
            # Project the global movement direction into the leg's local coordinate system
            global_direction = self.direction_input
            
            # Transform global direction to leg's local coordinate system
            # The leg's local Y-axis is at leg_angle_deg relative to robot's global Y-axis
            # We need to project the global direction onto the leg's local axes
            
            # Calculate the leg's local coordinate system
            # Local Y-axis of the leg (pointing outward from robot center)
            leg_local_y = Vector2D(math.cos(leg_angle_rad), math.sin(leg_angle_rad))
            
            # Local X-axis of the leg (perpendicular to local Y, pointing to the right of local Y)
            # This is calculated as rotating local Y by 90° clockwise
            leg_local_x = Vector2D(math.sin(leg_angle_rad), -math.cos(leg_angle_rad))
            
            # Project global direction onto leg's local axes
            # This gives us how much the leg should move in its own coordinate system
            projection_x = global_direction.dot(leg_local_x)
            projection_y = global_direction.dot(leg_local_y)
            
            # Create the projected direction in leg's local coordinate system
            leg_projected_direction = Vector2D(projection_x, projection_y)
            
            if is_swing:
                # Swing legs: move in the projected direction from center
                projection_direction = leg_projected_direction
                projection_origin = Vector2D(0, 0)
            else:
                # Stance legs: move in opposite direction from current position
                projection_direction = leg_projected_direction.inverse()
                current_pos_2d = Vector2D(*self.hexapod.current_leg_positions[leg_index][:2])
                projection_origin = current_pos_2d
        
        # Calculate target position using circle projection
        if self.rotation_input != 0:
            # For rotation, use relative movements
            movement_distance = self.step_radius * abs(self.rotation_input)
            target_2d = projection_direction.normalized() * movement_distance
        else:
            # For translation, use circle projection
            effective_radius = self.step_radius
            
            if is_swing:
                # For swing legs, move outward from center in projected direction
                target_2d = projection_direction.normalized() * effective_radius
            else:
                # For stance legs, use circle projection from current position
                target_2d = self.project_point_to_circle(effective_radius, projection_origin, projection_direction)
        
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
            
            # Determine number of waypoints needed based on distance and movement type
            num_waypoints = 0
            step_height = self.leg_lift_distance
            
            # For rotation, use simpler 2-waypoint path (lift+move, then lower)
            if self.rotation_input != 0:
                num_waypoints = 1  # Single waypoint for lift+move combined
            elif (distance_from_current_to_lift_xy + distance_from_target_to_lower_xy < distance_from_current_to_target_xy and 
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
            
            # Create waypoints for movement
            path.add_waypoint(current_pos)  # Phase 1: Start position
            
            if self.rotation_input != 0:
                # For rotation: simplified 2-waypoint path
                # Phase 2: Lift and move to target X,Y in one motion
                lift_move_waypoint = Vector3D(target.x, target.y, current_pos.z + step_height)
                path.add_waypoint(lift_move_waypoint)
            else:
                # For non-rotation: three-phase path
                if num_waypoints == 2:
                    # Phase 2: Lift waypoint (up and forward)
                    lift_direction = current_to_target.xy_plane().normalized()
                    lift_waypoint = current_pos + lift_direction * (abs(missing_height) / self.leg_lift_incline)
                    lift_waypoint.z = current_pos.z + missing_height
                    path.add_waypoint(lift_waypoint)
                
                # Phase 3: Travel waypoint (move to target X,Y while lifted)
                if num_waypoints > 0:
                    # Create waypoint at target X,Y but still lifted
                    travel_waypoint = Vector3D(target.x, target.y, current_pos.z + step_height)
                    path.add_waypoint(travel_waypoint)
            
            path.add_waypoint(target)  # Final target (lower to ground)
            
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