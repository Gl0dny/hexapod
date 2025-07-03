from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Optional
import logging
import threading
import time
import numpy as np

from utils import rename_thread
from .base_gait import BaseGait, GaitPhase, GaitState
from .tripod_gait import TripodGait
from .wave_gait import WaveGait

logger = logging.getLogger("robot_logger")

if TYPE_CHECKING:
    from robot import Hexapod
    from imu import IMU

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

    def _execute_phase(self, state: GaitState) -> None:
        """
        Execute a single gait phase with three-phase path planning.
        
        This method calculates target positions for all legs using circle-based
        targeting and moves them to their new positions. For swing legs, this
        includes the three-phase path planning (lift → travel → lower).
        
        All legs in the same phase (swing or stance) move simultaneously,
        regardless of how many legs are in each phase.
        
        Args:
            state (GaitState): The current gait state to execute
        """
        logger.info(f"Executing phase: {state.phase}")
        logger.info(f"Swing legs: {state.swing_legs}")
        logger.info(f"Stance legs: {state.stance_legs}")
        
        # Calculate paths for all legs using circle-based targeting
        swing_paths = {}  # Store paths for swing legs
        stance_paths = {}  # Store paths for stance legs
        
        # Calculate swing paths with three-phase path planning
        for leg_idx in state.swing_legs:
            logger.debug(f"\nCalculating swing path for leg {leg_idx}")
            swing_target = self.current_gait.calculate_leg_target(leg_idx, is_swing=True)
            self.current_gait.calculate_leg_path(leg_idx, swing_target, is_swing=True)
            swing_paths[leg_idx] = self.current_gait.leg_paths[leg_idx]
            logger.debug(f"Leg {leg_idx} swing path has {len(swing_paths[leg_idx].waypoints)} waypoints")
        
        # Calculate stance paths
        for leg_idx in state.stance_legs:
            logger.debug(f"\nCalculating stance path for leg {leg_idx}")
            stance_target = self.current_gait.calculate_leg_target(leg_idx, is_swing=False)
            self.current_gait.calculate_leg_path(leg_idx, stance_target, is_swing=False)
            stance_paths[leg_idx] = self.current_gait.leg_paths[leg_idx]
            logger.debug(f"Leg {leg_idx} stance path has {len(stance_paths[leg_idx].waypoints)} waypoints")
        
        # Execute all movements simultaneously through waypoints
        # Swing and stance legs move together, with stance legs pushing while swing legs lift/move
        if state.swing_legs or state.stance_legs:
            logger.debug(f"\nExecuting simultaneous movement:")
            logger.debug(f"  Swing legs: {state.swing_legs}")
            logger.debug(f"  Stance legs: {state.stance_legs}")
            self._execute_waypoints(state.swing_legs, swing_paths, state.stance_legs, stance_paths)

    def _execute_waypoints(self, swing_legs: List[int], swing_paths: Dict[int, BaseGait.LegPath], 
                          stance_legs: List[int], stance_paths: Dict[int, BaseGait.LegPath]) -> None:
        """
        Execute movement through waypoints for swing and stance legs simultaneously.
        
        This method moves swing and stance legs through their waypoints at the same time,
        ensuring that stance legs are pushing while swing legs are lifting and moving.
        This creates proper gait coordination where the robot maintains stability
        throughout the movement.
        
        Key Features:
        - All legs move simultaneously at each waypoint
        - Stance legs push while swing legs execute their three-phase path
        - Maximum waypoints synchronization ensures smooth coordination
        - Legs that complete their paths early stay at final positions
        
        Args:
            swing_legs (List[int]): List of swing leg indices
            swing_paths (Dict[int, BaseGait.LegPath]): Dictionary mapping swing leg indices to their paths
            stance_legs (List[int]): List of stance leg indices  
            stance_paths (Dict[int, BaseGait.LegPath]): Dictionary mapping stance leg indices to their paths
        """
        logger.debug(f"Executing simultaneous movement for {len(swing_legs)} swing legs and {len(stance_legs)} stance legs")
        
        # Combine all legs and paths for unified execution
        all_legs = swing_legs + stance_legs
        all_paths = {**swing_paths, **stance_paths}
        
        # Find the maximum number of waypoints across all legs
        max_waypoints = max(len(all_paths[leg_idx].waypoints) for leg_idx in all_legs) if all_legs else 0
        logger.debug(f"Maximum waypoints across all legs: {max_waypoints}")
        
        # Track which legs have completed their paths
        completed_legs = set()
        
        # Move through waypoints simultaneously
        for waypoint_idx in range(max_waypoints):
            logger.debug(f"  Waypoint {waypoint_idx + 1}/{max_waypoints} for all legs")
            
            # Prepare target positions for all legs at this waypoint
            all_positions = list(self.hexapod.current_leg_positions)  # Start with current positions
            
            for leg_idx in all_legs:
                path = all_paths[leg_idx]
                
                if leg_idx in completed_legs:
                    # This leg has completed its path, keep it at final position
                    final_waypoint = path.waypoints[-1]
                    all_positions[leg_idx] = (final_waypoint.x, final_waypoint.y, final_waypoint.z)
                    leg_type = "swing" if leg_idx in swing_legs else "stance"
                    logger.debug(f"    {leg_type.capitalize()} leg {leg_idx}: {final_waypoint.to_tuple()} (completed, staying at final position)")
                    
                elif waypoint_idx < len(path.waypoints):
                    # This leg has more waypoints to go
                    waypoint = path.waypoints[waypoint_idx]
                    all_positions[leg_idx] = (waypoint.x, waypoint.y, waypoint.z)
                    leg_type = "swing" if leg_idx in swing_legs else "stance"
                    logger.debug(f"    {leg_type.capitalize()} leg {leg_idx}: {waypoint.to_tuple()}")
                    
                    # Check if this is the final waypoint for this leg
                    if waypoint_idx == len(path.waypoints) - 1:
                        completed_legs.add(leg_idx)
                        logger.debug(f"    {leg_type.capitalize()} leg {leg_idx} completed its path")
                        
                else:
                    # This leg has fewer waypoints, use its final position
                    final_waypoint = path.waypoints[-1]
                    all_positions[leg_idx] = (final_waypoint.x, final_waypoint.y, final_waypoint.z)
                    leg_type = "swing" if leg_idx in swing_legs else "stance"
                    logger.debug(f"    {leg_type.capitalize()} leg {leg_idx}: {final_waypoint.to_tuple()} (final position)")
                    completed_legs.add(leg_idx)
                    logger.debug(f"    {leg_type.capitalize()} leg {leg_idx} completed its path")
            
            try:
                # Move all legs to their target positions simultaneously
                self.hexapod.move_all_legs(all_positions)
                
                # Wait for all movements to complete
                # self.hexapod.wait_until_motion_complete()
                time.sleep(0.3)  # Delay between waypoints
                
                logger.debug(f"    All legs moved successfully to waypoint {waypoint_idx + 1}")
                
            except Exception as e:
                logger.error(f"    Error moving legs to waypoint {waypoint_idx + 1}: {e}")
                logger.error(f"    Attempting to return to safe position...")
                from robot.hexapod import PredefinedPosition
                self.hexapod.move_to_position(PredefinedPosition.UPRIGHT)
                self.hexapod.wait_until_motion_complete()
                raise e
        
        logger.debug(f"  Completed simultaneous movement for all legs")

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
        logger.info("Starting gait generation thread")
        while self.is_running:
            if not self.current_state:
                logger.warning("No current state set, stopping gait")
                break

            # Check if stop event is set
            if self.stop_event and self.stop_event.is_set():
                logger.warning("Stop event detected, stopping gait")
                break

            try:
                # Execute current phase
                self._execute_phase(self.current_state)
                
                # Wait for dwell time or until stability is compromised
                logger.debug(f"\nWaiting for dwell time: {self.current_state.dwell_time}s")
                start_time = time.time()
                while (time.time() - start_time < self.current_state.dwell_time and
                       self._check_stability()):
                    # Check stop event during dwell time
                    if self.stop_event and self.stop_event.is_set():
                        logger.warning("Stop event detected during dwell time")
                        return
                    time.sleep(0.01)  # Small sleep to prevent CPU hogging

                # Check stop event before transitioning
                if self.stop_event and self.stop_event.is_set():
                    logger.warning("Stop event detected before state transition")
                    break

                # Transition to next state
                next_phases = self.current_gait.gait_graph[self.current_state.phase]
                logger.info(f"\nTransitioning to next phase: {next_phases[0]}")
                self.current_state = self.current_gait.get_state(next_phases[0])
                
            except Exception as e:
                logger.error(f"\nError in gait generation: {e}")
                logger.error(f"Current state: {self.current_state}")
                logger.error(f"Current leg positions: {self.hexapod.current_leg_positions}")
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