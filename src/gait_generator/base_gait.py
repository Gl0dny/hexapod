from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Tuple, Optional, Union
import math
from dataclasses import dataclass
from abc import ABC, abstractmethod
from utils import Vector2D, Vector3D

if TYPE_CHECKING:
    from robot import Hexapod

from enum import Enum, auto

class GaitPhase(Enum):
    TRIPOD_A = auto()
    TRIPOD_B = auto()
    WAVE_1 = auto()
    WAVE_2 = auto()
    WAVE_3 = auto()
    WAVE_4 = auto()
    WAVE_5 = auto()
    WAVE_6 = auto()

@dataclass
class GaitState:
    phase: GaitPhase
    swing_legs: List[int]
    stance_legs: List[int]
    dwell_time: float
    stability_threshold: float

class BaseGait(ABC):
    @dataclass
    class LegPath:
        waypoints: List[Vector3D]
        current_waypoint_index: int = 0
        def add_waypoint(self, waypoint: Vector3D) -> None:
            self.waypoints.append(waypoint)
        def get_current_target(self) -> Vector3D:
            if self.waypoints:
                return self.waypoints[self.current_waypoint_index]
            return Vector3D(0, 0, 0)
        def advance_to_next_waypoint(self) -> bool:
            if self.current_waypoint_index < len(self.waypoints) - 1:
                self.current_waypoint_index += 1
                return True
            return False
        def reset(self) -> None:
            self.current_waypoint_index = 0
    DIRECTION_MAP = {
        'forward': (0.0, 1.0),
        'backward': (0.0, -1.0),
        'right': (1.0, 0.0),
        'left': (-1.0, 0.0),
        'diagonal-fr': (0.707, 0.707),
        'diagonal-fl': (-0.707, 0.707),
        'diagonal-br': (0.707, -0.707),
        'diagonal-bl': (-0.707, -0.707),
        'stop': (0.0, 0.0),
    }
    def __init__(self, hexapod: 'Hexapod', step_radius: float = 30.0, leg_lift_distance: float = 10.0, leg_lift_incline: float = 2.0, stance_height: float = 0.0, dwell_time: float = 0.5, stability_threshold: float = 0.2) -> None:
        self.hexapod = hexapod
        self.gait_graph: Dict[GaitPhase, List[GaitPhase]] = {}
        self.step_radius = step_radius
        self.leg_lift_distance = leg_lift_distance
        self.leg_lift_incline = leg_lift_incline
        self.stance_height = stance_height
        self.dwell_time = dwell_time
        self.stability_threshold = stability_threshold
        self.direction_input = Vector2D(0, 0)
        self.rotation_input = 0.0
        self.leg_mount_angles = [i * 60 for i in range(6)]
        self.leg_paths: List[BaseGait.LegPath] = [self.LegPath([]) for _ in range(6)]
        self._setup_gait_graph()
    def project_point_to_circle(self, radius: float, point: Vector2D, direction: Vector2D) -> Vector2D:
        if direction.magnitude() == 0:
            return point
        if (point.magnitude() == 0 or 
            point.normalized() == direction.normalized() or 
            point.normalized() == direction.normalized() * -1):
            return direction.normalized() * radius
        if direction.magnitude() > radius - 0.005:
            direction = direction.normalized() * (radius - 0.005)
        length_c = point.magnitude()
        angle_beta = 180 - Vector2D.angle_between_vectors(direction, point)
        sin_gamma = (length_c * math.sin(math.radians(angle_beta))) / radius
        angle_gamma = math.degrees(math.asin(sin_gamma))
        angle_alpha = 180 - angle_beta - angle_gamma
        projection_length = (radius * math.sin(math.radians(angle_alpha))) / math.sin(math.radians(angle_beta))
        return point + direction.normalized() * projection_length
    def calculate_leg_target(self, leg_index: int, is_swing: bool) -> Vector3D:
        if self.direction_input.magnitude() == 0 and self.rotation_input == 0:
            current_pos = Vector3D(*self.hexapod.current_leg_positions[leg_index])
            current_pos.z = -self.stance_height
            return current_pos
        projection_direction = Vector2D(0, 0)
        projection_origin = Vector2D(0, 0)
        rotation_projection = Vector2D(0, 0)
        if self.rotation_input != 0:
            if self.rotation_input > 0:
                rotation_projection = Vector2D(1, 0)
            else:
                rotation_projection = Vector2D(-1, 0)
        if is_swing:
            projection_direction = self.direction_input + rotation_projection
            projection_origin = Vector2D(0, 0)
        else:
            projection_direction = self.direction_input.inverse() + rotation_projection.inverse()
            current_pos_2d = Vector2D(*self.hexapod.current_leg_positions[leg_index][:2])
            projection_origin = current_pos_2d
        if self.rotation_input != 0:
            movement_distance = self.step_radius * abs(self.rotation_input)
            if is_swing:
                target_2d = projection_direction.normalized() * movement_distance
            else:
                target_2d = projection_direction.normalized() * movement_distance
        else:
            effective_radius = self.step_radius
            target_2d = self.project_point_to_circle(effective_radius, projection_origin, projection_direction)
        target_3d = Vector3D(target_2d.x, target_2d.y, -self.stance_height)
        return target_3d
    def calculate_leg_path(self, leg_index: int, target: Vector3D, is_swing: bool) -> None:
        current_pos = Vector3D(*self.hexapod.current_leg_positions[leg_index])
        path = self.LegPath([])
        if is_swing:
            current_to_target = target - current_pos
            missing_height = target.z + self.leg_lift_distance - current_pos.z
            distance_from_current_to_lift_xy = abs(missing_height) / self.leg_lift_incline
            distance_from_target_to_lower_xy = self.leg_lift_distance / self.leg_lift_incline
            distance_from_current_to_target_xy = current_to_target.xy_plane().magnitude()
            num_waypoints = 0
            step_height = self.leg_lift_distance
            if self.rotation_input != 0:
                num_waypoints = 1
            elif (distance_from_current_to_lift_xy + distance_from_target_to_lower_xy < distance_from_current_to_target_xy and 
                  abs(missing_height) > 2):
                num_waypoints = 2
            elif missing_height < 2:
                num_waypoints = 1
                step_height = self.leg_lift_distance - ((distance_from_current_to_lift_xy + distance_from_target_to_lower_xy - distance_from_current_to_target_xy) / 2) * self.leg_lift_incline
            else:
                num_waypoints = 1
                step_height = distance_from_current_to_target_xy * self.leg_lift_incline
            path.add_waypoint(current_pos)
            if self.rotation_input != 0:
                lift_move_waypoint = Vector3D(target.x, target.y, current_pos.z + step_height)
                path.add_waypoint(lift_move_waypoint)
            else:
                if num_waypoints == 2:
                    lift_direction = current_to_target.xy_plane().normalized()
                    lift_waypoint = current_pos + lift_direction * (abs(missing_height) / self.leg_lift_incline)
                    lift_waypoint.z = current_pos.z + missing_height
                    path.add_waypoint(lift_waypoint)
                if num_waypoints > 0:
                    travel_waypoint = Vector3D(target.x, target.y, current_pos.z + step_height)
                    path.add_waypoint(travel_waypoint)
            path.add_waypoint(target)
        else:
            path.add_waypoint(current_pos)
            path.add_waypoint(target)
        self.leg_paths[leg_index] = path
    @abstractmethod
    def _setup_gait_graph(self) -> None:
        pass
    @abstractmethod
    def get_state(self, phase: GaitPhase) -> GaitState:
        pass
    def set_direction(self, direction: Union[str, Tuple[float, float]], rotation: float = 0.0) -> None:
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