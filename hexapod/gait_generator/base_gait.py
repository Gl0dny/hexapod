"""
Base gait implementation for hexapod robot locomotion.

This module defines the abstract BaseGait class and related data structures
for implementing different walking gaits. It provides the foundation for
gait patterns, phase management, and leg coordination algorithms.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto

from hexapod.utils import Vector2D, Vector3D
from hexapod.interface import get_custom_logger

if TYPE_CHECKING:
    from robot import Hexapod, Dict, List, Tuple, Union

logger = get_custom_logger("gait_generator_logger")


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
    WAVE_1 = auto()  # Leg 0 swing (Right)
    WAVE_2 = auto()  # Leg 1 swing (Right Front)
    WAVE_3 = auto()  # Leg 2 swing (Left Front)
    WAVE_4 = auto()  # Leg 3 swing (Left)
    WAVE_5 = auto()  # Leg 4 swing (Left Back)
    WAVE_6 = auto()  # Leg 5 swing (Right Back)


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
    """

    phase: GaitPhase
    swing_legs: List[int]  # List of leg indices in swing phase
    stance_legs: List[int]  # List of leg indices in stance phase
    dwell_time: float  # Time to spend in this state


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
            logger.debug(f"Adding waypoint {waypoint} to LegPath")
            self.waypoints.append(waypoint)

        def get_current_target(self) -> Vector3D:
            """
            Get the current target waypoint.

            Returns:
                Vector3D: Current waypoint, or zero vector if no waypoints exist
            """
            logger.debug(
                f"Getting current target waypoint at index {self.current_waypoint_index}"
            )
            if self.waypoints:
                waypoint: Vector3D = self.waypoints[self.current_waypoint_index]
                return waypoint
            logger.warning("No waypoints in LegPath, returning zero vector")
            return Vector3D(0, 0, 0)

        def advance_to_next_waypoint(self) -> bool:
            """
            Advance to the next waypoint in the path.

            Returns:
                bool: True if there are more waypoints, False if at the end
            """
            logger.debug(f"Advancing from waypoint {self.current_waypoint_index}")
            if self.current_waypoint_index < len(self.waypoints) - 1:
                self.current_waypoint_index += 1
                logger.debug(f"Advanced to waypoint {self.current_waypoint_index}")
                return True
            logger.debug("No more waypoints to advance to")
            return False

        def reset(self) -> None:
            """Reset the path to start from the beginning."""
            logger.debug("Resetting LegPath to start from the beginning")
            self.current_waypoint_index = 0

    # Direction mapping for consistent movement vectors
    # Using 1/√2 ≈ 0.707 for diagonal directions to maintain unit magnitude
    # Coordinate system: +X = Right, +Y = Forward, +Z = Up
    DIRECTION_MAP = {
        # Cardinal directions
        "forward": (0.0, 1.0),  # +Y direction
        "backward": (0.0, -1.0),  # -Y direction
        "right": (1.0, 0.0),  # +X direction
        "left": (-1.0, 0.0),  # -X direction
        # Diagonal directions (0.707 = 1/√2 for unit magnitude)
        "forward right": (0.707, 0.707),  # Forward-Right
        "forward left": (-0.707, 0.707),  # Forward-Left
        "backward right": (0.707, -0.707),  # Backward-Right
        "backward left": (-0.707, -0.707),  # Backward-Left
        # Stop/neutral
        "neutral": (0.0, 0.0),
    }

    def __init__(
        self,
        hexapod: Hexapod,
        step_radius: float = 30.0,
        leg_lift_distance: float = 10.0,
        stance_height: float = 0.0,  # Height of stance legs above ground (mm), 0.0 = reference position
        dwell_time: float = 0.5,
        use_full_circle_stance: bool = False,
    ) -> None:
        """
        Initialize the base gait with circle-based parameters.

        Args:
            hexapod (Hexapod): The hexapod robot instance
            step_radius (float): Radius of the circular workspace for each leg (mm)
            leg_lift_distance (float): Height legs lift during swing phase (mm)
            stance_height (float): Height above ground for stance legs (mm).
                                 A value of 0.0 matches the reference position (starting/home position).
                                 Positive values lower legs (raise body), negative values raise legs (lower body).
            dwell_time (float): Time to spend in each gait phase (seconds)
            use_full_circle_stance (bool): Stance leg movement pattern
                - False (default): Half circle behavior - stance legs move from current position back to center (0,0)
                - True: Full circle behavior - stance legs move from current position to opposite side of circle

                Example calculations (step_radius=30.0, direction=1.0):

                HALF CIRCLE (default):
                - Swing legs: (0,0) → (+30,0) [30mm movement]
                - Stance legs: (+30,0) → (0,0) [30mm movement back to center]
                - Total stance movement: 30mm

                FULL CIRCLE:
                - Swing legs: (0,0) → (+30,0) [30mm movement]
                - Stance legs: (+30,0) → (-30,0) [60mm movement to opposite side]
                - Total stance movement: 60mm

                Half circle is more efficient as stance legs move half the distance.
        """
        logger.info(
            f"Initializing BaseGait with step_radius={step_radius}, leg_lift_distance={leg_lift_distance}, "
            f"stance_height={stance_height}, dwell_time={dwell_time}, "
            f"use_full_circle_stance={use_full_circle_stance}"
        )
        self.hexapod = hexapod
        self.gait_graph: Dict[GaitPhase, List[GaitPhase]] = {}

        # Circle-based gait parameters
        self.step_radius = step_radius
        self.leg_lift_distance = leg_lift_distance
        self.stance_height = stance_height
        self.dwell_time = dwell_time
        self.use_full_circle_stance = use_full_circle_stance

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
        logger.debug("Gait graph setup complete")

    def project_point_to_circle(
        self, radius: float, point: Vector2D, direction: Vector2D
    ) -> Vector2D:
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
        logger.debug(
            f"Projecting point {point} onto circle with radius {radius} in direction {direction}"
        )
        # No direction for projection -> no calculation
        if direction.magnitude() == 0:
            logger.warning(
                "Direction vector has zero magnitude, returning original point"
            )
            return point

        # If point is at origin or has same direction as input, simple calculation
        if (
            point.magnitude() == 0
            or point.normalized() == direction.normalized()
            or point.normalized() == direction.normalized() * -1
        ):
            logger.debug(
                "Point is at origin or collinear with direction, using simple projection"
            )
            return direction.normalized() * radius

        # If direction is too long, clamp it to circle boundary
        if direction.magnitude() > radius - 0.005:
            logger.debug(
                "Direction magnitude exceeds circle boundary, clamping to boundary"
            )
            direction = direction.normalized() * (radius - 0.005)

        # Calculate projection using trigonometry (law of sines)
        length_c = point.magnitude()
        angle_beta = 180 - Vector2D.angle_between_vectors(direction, point)

        # Handle edge case where angle_beta is 0° or 180° (sin = 0)
        if abs(angle_beta) < 0.1 or abs(angle_beta - 180) < 0.1:
            # Direction and point are collinear, use simple projection
            logger.warning(
                "Angle beta is near 0 or 180 degrees, using simple projection"
            )
            return direction.normalized() * radius

        # Calculate missing angles using law of sines
        sin_gamma = (length_c * math.sin(math.radians(angle_beta))) / radius

        # Clamp sin_gamma to valid range [-1, 1] to prevent math domain error
        sin_gamma = max(-1.0, min(1.0, sin_gamma))

        angle_gamma = math.degrees(math.asin(sin_gamma))
        angle_alpha = 180 - angle_beta - angle_gamma

        # Calculate projection length
        projection_length = (radius * math.sin(math.radians(angle_alpha))) / math.sin(
            math.radians(angle_beta)
        )

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
        logger.debug(f"Calculating leg target for leg {leg_index}, is_swing={is_swing}")
        # If no movement input, handle marching in place
        if self.direction_input.magnitude() == 0 and self.rotation_input == 0:
            logger.info("No movement input, handling marching in place")
            current_pos = Vector3D(*self.hexapod.current_leg_positions[leg_index])

            if is_swing:
                # For swing legs in marching in place: lift up and down
                # Target is the same X,Y position at ground level (path calculation will handle lifting)
                target_pos = Vector3D(current_pos.x, current_pos.y, -self.stance_height)
                logger.debug(
                    f"Swing leg {leg_index} marching in place: lift up and down. Target: {target_pos}"
                )
                return target_pos
            else:
                # For stance legs: maintain current position with proper stance height
                current_pos.z = -self.stance_height  # Adjust for stance height
                logger.debug(
                    f"Stance leg {leg_index} marching in place: maintain current position. Current: {current_pos}, Target: {current_pos}"
                )
                return current_pos

        # Get the leg's mounting angle (in degrees)
        leg_angle_deg = self.leg_mount_angles[leg_index]
        leg_angle_rad = math.radians(leg_angle_deg)
        logger.debug(f"Leg {leg_index} mount angle: {leg_angle_deg} degrees")

        # Calculate projection direction and origin
        projection_direction = Vector2D(0, 0)
        projection_origin = Vector2D(0, 0)

        if self.rotation_input != 0:
            logger.info(f"Rotation input detected: {self.rotation_input}")
            # Handle rotation movement
            # For rotation, all legs move in the same relative direction regardless of mounting angle
            if self.rotation_input > 0:  # Clockwise rotation
                rotation_projection = Vector2D(1, 0)  # Right in local coordinate system
            else:  # Counterclockwise rotation
                rotation_projection = Vector2D(-1, 0)  # Left in local coordinate system

            if is_swing:
                # Swing legs: project from center in rotation direction
                projection_direction = rotation_projection
                projection_origin = Vector2D(0, 0)
                logger.debug(
                    f"Swing leg {leg_index} rotation: project from center in rotation direction. Projection: {projection_direction}, Origin: {projection_origin}"
                )
            else:
                # Stance legs behavior for rotation
                if self.use_full_circle_stance:
                    # Full circle behavior: stance legs move in opposite rotation direction
                    projection_direction = rotation_projection.inverse()
                    current_pos_2d = Vector2D(
                        *self.hexapod.current_leg_positions[leg_index][:2]
                    )
                    projection_origin = current_pos_2d
                    logger.debug(
                        f"Stance leg {leg_index} rotation (full circle): move in opposite rotation direction. Projection: {projection_direction}, Origin: {projection_origin}"
                    )
                else:
                    # Half circle behavior: stance legs move back to center (0,0)
                    current_pos_2d = Vector2D(
                        *self.hexapod.current_leg_positions[leg_index][:2]
                    )
                    # Direction from current position to center
                    projection_direction = current_pos_2d.inverse()
                    projection_origin = current_pos_2d
                    logger.debug(
                        f"Stance leg {leg_index} rotation (half circle): move back to center (0,0). Projection: {projection_direction}, Origin: {projection_origin}"
                    )
        else:
            logger.info(f"Translation input detected: {self.direction_input}")
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
                logger.debug(
                    f"Swing leg {leg_index} translation: move in projected direction from center. Projection: {projection_direction}, Origin: {projection_origin}"
                )
            else:
                # Stance legs behavior
                if self.use_full_circle_stance:
                    # Full circle behavior: stance legs move to opposite side of circle
                    projection_direction = leg_projected_direction.inverse()
                    current_pos_2d = Vector2D(
                        *self.hexapod.current_leg_positions[leg_index][:2]
                    )
                    projection_origin = current_pos_2d
                    logger.debug(
                        f"Stance leg {leg_index} translation (full circle): move to opposite side of circle. Projection: {projection_direction}, Origin: {projection_origin}"
                    )
                else:
                    # Half circle behavior: stance legs move back to center (0,0)
                    current_pos_2d = Vector2D(
                        *self.hexapod.current_leg_positions[leg_index][:2]
                    )
                    # Direction from current position to center
                    projection_direction = current_pos_2d.inverse()
                    projection_origin = current_pos_2d
                    logger.debug(
                        f"Stance leg {leg_index} translation (half circle): move back to center (0,0). Projection: {projection_direction}, Origin: {projection_origin}"
                    )

        # Calculate target position using circle projection
        if self.rotation_input != 0:
            # For rotation, use relative movements
            movement_distance = self.step_radius * abs(self.rotation_input)
            if is_swing:
                # Swing legs: use relative movement
                target_2d = projection_direction.normalized() * movement_distance
                logger.debug(
                    f"Swing leg {leg_index} rotation: use relative movement. Movement distance: {movement_distance}, Projection: {projection_direction}, Target: {target_2d}"
                )
            else:
                # Stance legs for rotation
                if self.use_full_circle_stance:
                    # Full circle behavior: use relative movement
                    target_2d = projection_direction.normalized() * movement_distance
                    logger.debug(
                        f"Stance leg {leg_index} rotation (full circle): use relative movement. Movement distance: {movement_distance}, Projection: {projection_direction}, Target: {target_2d}"
                    )
                else:
                    # Half circle behavior: move back to center (0,0)
                    target_2d = Vector2D(0, 0)
                    logger.debug(
                        f"Stance leg {leg_index} rotation (half circle): move back to center (0,0). Target: {target_2d}"
                    )
        else:
            # For translation, use direction magnitude to scale movement distance (like rotation)
            movement_distance = self.step_radius * self.direction_input.magnitude()
            if movement_distance > 0:
                if is_swing:
                    # For swing legs, use circle projection from center (constrained by workspace)
                    target_2d = self.project_point_to_circle(
                        movement_distance, projection_origin, projection_direction
                    )
                    logger.debug(
                        f"Swing leg {leg_index} translation: use circle projection from center. Movement distance: {movement_distance}, Projection origin: {projection_origin}, Projection: {projection_direction}, Target: {target_2d}"
                    )
                else:
                    # For stance legs
                    if self.use_full_circle_stance:
                        # Full circle behavior: use circle projection from current position
                        target_2d = self.project_point_to_circle(
                            movement_distance, projection_origin, projection_direction
                        )
                        logger.debug(
                            f"Stance leg {leg_index} translation (full circle): use circle projection from current position. Movement distance: {movement_distance}, Projection origin: {projection_origin}, Projection: {projection_direction}, Target: {target_2d}"
                        )
                    else:
                        # Half circle behavior: move back to center (0,0) - no circle projection needed
                        target_2d = Vector2D(0, 0)
                        logger.debug(
                            f"Stance leg {leg_index} translation (half circle): move back to center (0,0). Target: {target_2d}"
                        )
            else:
                # No movement - stay at current position
                if is_swing:
                    target_2d = Vector2D(0, 0)
                    logger.debug(
                        f"Swing leg {leg_index} no movement: stay at current position. Target: {target_2d}"
                    )
                else:
                    current_pos_2d = Vector2D(
                        *self.hexapod.current_leg_positions[leg_index][:2]
                    )
                    target_2d = current_pos_2d
                    logger.debug(
                        f"Stance leg {leg_index} no movement: stay at current position. Target: {target_2d}"
                    )

        # Convert to 3D with proper stance height
        target_3d = Vector3D(target_2d.x, target_2d.y, -self.stance_height)
        logger.debug(f"Calculated target 3D position for leg {leg_index}: {target_3d}")
        return target_3d

    def calculate_leg_path(
        self, leg_index: int, target: Vector3D, is_swing: bool
    ) -> None:
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
        logger.debug(
            f"Calculating leg path for leg {leg_index}, target={target}, is_swing={is_swing}"
        )
        current_pos = Vector3D(*self.hexapod.current_leg_positions[leg_index])
        path = self.LegPath([])

        if is_swing:
            # Check if this is marching in place (no movement input)
            is_marching_in_place = (
                self.direction_input.magnitude() == 0 and self.rotation_input == 0
            )

            if is_marching_in_place:
                # For marching in place: simple up and down movement
                logger.debug(
                    f"Path calculation for leg {leg_index} (marching in place):"
                )
                logger.debug(f"  Current pos: {current_pos}")
                logger.debug(f"  Leg lift distance: {self.leg_lift_distance}")

                # Phase 1: Start position
                path.add_waypoint(current_pos)

                # Phase 2: Lift up in place
                lift_waypoint = Vector3D(
                    current_pos.x, current_pos.y, current_pos.z + self.leg_lift_distance
                )
                path.add_waypoint(lift_waypoint)

                # Phase 3: Lower back to start position
                path.add_waypoint(current_pos)
            else:
                # For actual movement: use 3-waypoint path: lift → move → lower
                logger.debug(f"Path calculation for leg {leg_index} (with movement):")
                logger.debug(f"  Current pos: {current_pos}, Target: {target}")
                logger.debug(f"  Leg lift distance: {self.leg_lift_distance}")

                # Phase 1: Start position
                path.add_waypoint(current_pos)

                # Phase 2: Lift and move to target X,Y
                # Use target.z + leg_lift_distance to ensure consistent lift height from ground
                lift_move_waypoint = Vector3D(
                    target.x, target.y, target.z + self.leg_lift_distance
                )
                path.add_waypoint(lift_move_waypoint)

                # Phase 3: Lower to final target
                path.add_waypoint(target)

        else:
            # Three-phase path for stance legs: push down → move → final position
            # path.add_waypoint(current_pos)  # Phase 1: Start position

            # # Phase 2: Push down slightly (1cm = 10mm) to improve ground contact
            # push_down_z = current_pos.z - 3.0  # Push down 10mm
            # push_down_waypoint = Vector3D(current_pos.x, current_pos.y, push_down_z)
            # path.add_waypoint(push_down_waypoint)

            # # Phase 3: Move to target position while maintaining downward pressure
            # target_with_push = Vector3D(target.x, target.y, target.z - 3.0)  # Slight downward pressure
            # path.add_waypoint(target_with_push)

            # Phase 4: Final position (normal stance height)
            # path.add_waypoint(target)

            # Stance leg: hold position for two steps, then move to target
            path.add_waypoint(current_pos)  # Step 0: Start
            # path.add_waypoint(current_pos)  # Step 1: Hold (while swing leg lifts)
            path.add_waypoint(target)  # Step 2: Move to target (after swing lift)
            # path.add_waypoint(target)  # Step 3: Hold (while swing leg reaches target)

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

    def set_direction(
        self, direction: Union[str, Tuple[float, float]], rotation: float = 0.0
    ) -> None:
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
                - 'forward right', 'forward left', 'backward right', 'backward left'
                - 'neutral'

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
            gait.set_direction('forward right', 0.0)     # Diagonal forward-right
            gait.set_direction((0.5, 0.5), 0.0)         # Custom direction
        """
        if isinstance(direction, str):
            if direction not in self.DIRECTION_MAP:
                available = list(self.DIRECTION_MAP.keys())
                raise ValueError(
                    f"Unknown direction '{direction}'. Available: {available}"
                )
            direction_tuple = self.DIRECTION_MAP[direction]
            self.direction_input = Vector2D(direction_tuple[0], direction_tuple[1])
        elif isinstance(direction, tuple):
            self.direction_input = Vector2D(direction[0], direction[1])
        else:
            raise TypeError(f"Direction must be string or tuple, got {type(direction)}")

        self.rotation_input = rotation
