from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Optional
import logging
import threading
import time
from enum import Enum, auto
import numpy as np

from utils import rename_thread

logger = logging.getLogger("robot_logger")

if TYPE_CHECKING:
    from robot import Hexapod
    from imu import IMU
    from gait_generator import TripodGait, WaveGait, BaseGait, GaitState

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

class GaitGenerator:
    """
    Main gait generator that manages the execution of gait patterns.
    """
    def __init__(self, hexapod, imu: Optional[object] = None) -> None:
        self.hexapod = hexapod
        self.imu = imu
        self.is_running = False
        self.thread = None
        self.current_state: Optional[GaitState] = None
        self.current_gait: Optional[BaseGait] = None
        self.stop_event: Optional[threading.Event] = None

    def _check_stability(self) -> bool:
        if not self.imu:
            return True
        accel = self.imu.get_acceleration()
        gyro = self.imu.get_gyro()
        accel_magnitude = np.linalg.norm(accel)
        gyro_magnitude = np.linalg.norm(gyro)
        return (abs(accel_magnitude - 9.81) < self.current_state.stability_threshold and
                gyro_magnitude < self.current_state.stability_threshold)

    def _execute_phase(self, state: GaitState) -> None:
        print(f"Executing phase: {state.phase}")
        print(f"Swing legs: {state.swing_legs}")
        print(f"Stance legs: {state.stance_legs}")
        swing_paths = {}
        stance_paths = {}
        for leg_idx in state.swing_legs:
            print(f"\nCalculating swing path for leg {leg_idx}")
            swing_target = self.current_gait.calculate_leg_target(leg_idx, is_swing=True)
            self.current_gait.calculate_leg_path(leg_idx, swing_target, is_swing=True)
            swing_paths[leg_idx] = self.current_gait.leg_paths[leg_idx]
            print(f"Leg {leg_idx} swing path has {len(swing_paths[leg_idx].waypoints)} waypoints")
        for leg_idx in state.stance_legs:
            print(f"\nCalculating stance path for leg {leg_idx}")
            stance_target = self.current_gait.calculate_leg_target(leg_idx, is_swing=False)
            self.current_gait.calculate_leg_path(leg_idx, stance_target, is_swing=False)
            stance_paths[leg_idx] = self.current_gait.leg_paths[leg_idx]
            print(f"Leg {leg_idx} stance path has {len(stance_paths[leg_idx].waypoints)} waypoints")
        if state.swing_legs or state.stance_legs:
            print(f"\nExecuting simultaneous movement:")
            print(f"  Swing legs: {state.swing_legs}")
            print(f"  Stance legs: {state.stance_legs}")
            self._execute_waypoints(state.swing_legs, swing_paths, state.stance_legs, stance_paths)

    def _execute_waypoints(self, swing_legs: List[int], swing_paths: Dict[int, BaseGait.LegPath], stance_legs: List[int], stance_paths: Dict[int, BaseGait.LegPath]) -> None:
        print(f"Executing simultaneous movement for {len(swing_legs)} swing legs and {len(stance_legs)} stance legs")
        all_legs = swing_legs + stance_legs
        all_paths = {**swing_paths, **stance_paths}
        max_waypoints = max(len(all_paths[leg_idx].waypoints) for leg_idx in all_legs) if all_legs else 0
        print(f"Maximum waypoints across all legs: {max_waypoints}")
        completed_legs = set()
        for waypoint_idx in range(max_waypoints):
            print(f"  Waypoint {waypoint_idx + 1}/{max_waypoints} for all legs")
            all_positions = list(self.hexapod.current_leg_positions)
            for leg_idx in all_legs:
                path = all_paths[leg_idx]
                if leg_idx in completed_legs:
                    final_waypoint = path.waypoints[-1]
                    all_positions[leg_idx] = (final_waypoint.x, final_waypoint.y, final_waypoint.z)
                    leg_type = "swing" if leg_idx in swing_legs else "stance"
                    print(f"    {leg_type.capitalize()} leg {leg_idx}: {final_waypoint.to_tuple()} (completed, staying at final position)")
                elif waypoint_idx < len(path.waypoints):
                    waypoint = path.waypoints[waypoint_idx]
                    all_positions[leg_idx] = (waypoint.x, waypoint.y, waypoint.z)
                    leg_type = "swing" if leg_idx in swing_legs else "stance"
                    print(f"    {leg_type.capitalize()} leg {leg_idx}: {waypoint.to_tuple()}")
                    if waypoint_idx == len(path.waypoints) - 1:
                        completed_legs.add(leg_idx)
                        print(f"    {leg_type.capitalize()} leg {leg_idx} completed its path")
                else:
                    final_waypoint = path.waypoints[-1]
                    all_positions[leg_idx] = (final_waypoint.x, final_waypoint.y, final_waypoint.z)
                    leg_type = "swing" if leg_idx in swing_legs else "stance"
                    print(f"    {leg_type.capitalize()} leg {leg_idx}: {final_waypoint.to_tuple()} (final position)")
                    completed_legs.add(leg_idx)
                    print(f"    {leg_type.capitalize()} leg {leg_idx} completed its path")
            try:
                self.hexapod.move_all_legs(all_positions)
                time.sleep(0.3)
                print(f"    All legs moved successfully to waypoint {waypoint_idx + 1}")
            except Exception as e:
                print(f"    Error moving legs to waypoint {waypoint_idx + 1}: {e}")
                print(f"    Attempting to return to safe position...")
                from robot.hexapod import PredefinedPosition
                self.hexapod.move_to_position(PredefinedPosition.UPRIGHT)
                self.hexapod.wait_until_motion_complete()
                raise e
        print(f"  Completed simultaneous movement for all legs")

    def start(self, gait: BaseGait, stop_event: Optional[threading.Event] = None) -> None:
        if not self.is_running:
            self.is_running = True
            self.stop_event = stop_event
            self.current_gait = gait
            if isinstance(gait, TripodGait):
                self.current_state = gait.get_state(GaitPhase.TRIPOD_A)
            elif isinstance(gait, WaveGait):
                self.current_state = gait.get_state(GaitPhase.WAVE_1)
            else:
                raise ValueError(f"Unknown gait type: {type(gait)}")
            self.thread = threading.Thread(target=self.run_gait)
            rename_thread(self.thread, f"GaitGenerator-{gait.__class__.__name__}")
            self.thread.start()

    def run_gait(self) -> None:
        print("Starting gait generation thread")
        while self.is_running:
            if not self.current_state:
                print("No current state set, stopping gait")
                break
            if self.stop_event and self.stop_event.is_set():
                print("Stop event detected, stopping gait")
                break
            try:
                self._execute_phase(self.current_state)
                print(f"\nWaiting for dwell time: {self.current_state.dwell_time}s")
                start_time = time.time()
                while (time.time() - start_time < self.current_state.dwell_time and self._check_stability()):
                    if self.stop_event and self.stop_event.is_set():
                        print("Stop event detected during dwell time")
                        return
                    time.sleep(0.01)
                if self.stop_event and self.stop_event.is_set():
                    print("Stop event detected before state transition")
                    break
                next_phases = self.current_gait.gait_graph[self.current_state.phase]
                print(f"\nTransitioning to next phase: {next_phases[0]}")
                self.current_state = self.current_gait.get_state(next_phases[0])
            except Exception as e:
                print(f"\nError in gait generation: {e}")
                print(f"Current state: {self.current_state}")
                print(f"Current leg positions: {self.hexapod.current_leg_positions}")
                raise

    def stop(self) -> None:
        if self.is_running:
            self.is_running = False
            if self.stop_event:
                self.stop_event.set()
            if self.thread:
                self.thread.join()
            self.current_state = None
            self.current_gait = None
            self.stop_event = None