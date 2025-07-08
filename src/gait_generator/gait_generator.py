from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Optional
import logging
import threading
import time
import numpy as np

from utils import rename_thread, Vector3D
from .base_gait import BaseGait, GaitPhase, GaitState
from .tripod_gait import TripodGait
from .wave_gait import WaveGait

logger = logging.getLogger("gait_generator_logger")

if TYPE_CHECKING:
    from robot import Hexapod
    from robot.sensors import Imu

class GaitGenerator:
    """
    Main gait generator that manages the execution of gait patterns.
    
    This class coordinates the gait state machine, executes leg movements,
    and handles timing and stability monitoring. It runs the gait in a
    separate thread to allow continuous movement while the main program
    continues to run.
    """
    def __init__(self, hexapod: Hexapod, imu: Optional[Imu] = None, waypoint_dwell_time: float = 0.3) -> None:
        """
        Initialize the GaitGenerator with references to the hexapod and IMU.

        Args:
            hexapod (Hexapod): The Hexapod instance to control
            imu (IMU, optional): The IMU instance for stability monitoring
            waypoint_dwell_time (float): Time to wait between waypoints during leg movement (seconds)
        """
        self.hexapod = hexapod
        self.imu = imu
        self.waypoint_dwell_time = waypoint_dwell_time
        self.is_running = False
        self.thread = None
        self.current_state: Optional[GaitState] = None
        self.current_gait: Optional[BaseGait] = None
        self.stop_event: Optional[threading.Event] = None
        self.cycle_count: int = 0
        self.total_phases_executed: int = 0
        self.stop_requested: bool = False

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
        gyro = self.imu.get_gyroscope()
        
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
                time.sleep(self.waypoint_dwell_time)  # Delay between waypoints
                
                logger.debug(f"    All legs moved successfully to waypoint {waypoint_idx + 1}")
                
            except Exception as e:
                logger.error(f"    Error moving legs to waypoint {waypoint_idx + 1}: {e}")
                logger.error(f"    Attempting to return to safe position...")
                from robot.hexapod import PredefinedPosition
                self.hexapod.move_to_position(PredefinedPosition.HIGH_PROFILE)
                self.hexapod.wait_until_motion_complete()
                raise e
        
        logger.debug(f"  Completed simultaneous movement for all legs")

    def _execute_full_cycle(self) -> None:
        """
        Execute a complete gait cycle.
        
        This method executes all phases of the current gait pattern to complete
        one full cycle. 
        For tripod gait, this means executing both TRIPOD_A and
        TRIPOD_B phases. 
        For wave gait, this means executing all six WAVE phases.
        
        The method handles:
        - Phase transitions through the complete cycle
        - Stability monitoring throughout the cycle
        - Stop event checking between phases (completes current cycle if stop requested)
        - Error handling and recovery
        """
        logger.info("Starting full gait cycle execution")

        # Always reset to canonical start phase for each cycle
        if isinstance(self.current_gait, TripodGait):
            self.current_state = self.current_gait.get_state(GaitPhase.TRIPOD_A)
        elif isinstance(self.current_gait, WaveGait):
            self.current_state = self.current_gait.get_state(GaitPhase.WAVE_1)
        
        # Get the starting phase
        current_phase = self.current_state.phase
        cycle_start_phase = current_phase
        
        # Determine how many phases constitute a full cycle based on gait type
        phases_per_cycle = len(self.current_gait.gait_graph)
        phases_executed = 0
        
        logger.info(f"Executing full cycle starting from phase: {cycle_start_phase}")
        logger.info(f"Expected phases per cycle: {phases_per_cycle}")
        logger.info(f"Gait type: {type(self.current_gait).__name__}")
        
        # Check if stop was requested before starting this cycle
        if self.stop_event and self.stop_event.is_set():
            logger.error("Stop event detected before cycle start - completing current cycle")
            self.stop_requested = True
        
        while self.is_running:
            # Check if stop event is set during cycle execution
            if self.stop_event and self.stop_event.is_set() and not self.stop_requested:
                logger.error("Stop event detected during cycle execution - will complete current cycle")
                self.stop_requested = True
            
            try:
                # Execute current phase
                logger.info(f"Executing phase {phases_executed + 1}/{phases_per_cycle}: {self.current_state.phase}")
                self._execute_phase(self.current_state)
                phases_executed += 1
                
                # Check if we've completed a full cycle
                if phases_executed >= phases_per_cycle:
                    logger.info(f"Completed full gait cycle ({phases_executed} phases)")
                    logger.info(f"Cycle completed - phases_executed: {phases_executed}, phases_per_cycle: {phases_per_cycle}")
                    break
                
                # Wait for dwell time or until stability is compromised
                logger.debug(f"Waiting for dwell time: {self.current_state.dwell_time}s")
                start_time = time.time()
                while (time.time() - start_time < self.current_state.dwell_time and
                       self._check_stability()):
                    # Check stop event during dwell time
                    if self.stop_event and self.stop_event.is_set() and not self.stop_requested:
                        logger.error("Stop event detected during dwell time - will complete current cycle")
                        self.stop_requested = True
                    time.sleep(0.01)  # Small sleep to prevent CPU hogging
                
                # Check stop event before transitioning
                if self.stop_event and self.stop_event.is_set() and not self.stop_requested:
                    logger.error("Stop event detected before state transition - will complete current cycle")
                    self.stop_requested = True
                
                # If stop was requested, complete the cycle but don't start a new one
                if self.stop_requested:
                    logger.error("Stop requested - completing current cycle before stopping")
                    # Continue to complete the current cycle
                
                # Transition to next state
                next_phases = self.current_gait.gait_graph[self.current_state.phase]
                logger.info(f"Transitioning to next phase: {next_phases[0]}")
                self.current_state = self.current_gait.get_state(next_phases[0])
                
            except Exception as e:
                logger.error(f"Error in cycle execution: {e}")
                logger.error(f"Current state: {self.current_state}")
                logger.error(f"Phases executed: {phases_executed}")
                logger.error(f"Current leg positions: {self.hexapod.current_leg_positions}")
                raise
        
        logger.info(f"Full cycle execution completed. Executed {phases_executed} phases")
        
        # Update cycle statistics
        self.cycle_count += 1
        self.total_phases_executed += phases_executed

    def execute_cycles(self, num_cycles: int) -> int:
        """
        Execute a specific number of gait cycles.
        
        This method executes the specified number of complete gait cycles
        and then stops. Useful for controlled movement over a specific distance
        or for testing purposes.
        
        When a stop event is detected, the current cycle is completed before stopping
        to ensure graceful termination.
        
        Args:
            num_cycles (int): Number of complete cycles to execute
            
        Returns:
            int: Number of cycles actually completed
        """
        if num_cycles <= 0:
            logger.error(f"Invalid number of cycles: {num_cycles}")
            return 0
        
        logger.info(f"Executing {num_cycles} gait cycles")
        cycles_completed = 0
        
        # Execute cycles directly without using the background thread
        while self.is_running and cycles_completed < num_cycles:
            logger.info(f"Starting cycle {cycles_completed + 1}/{num_cycles}")
            logger.info(f"Current state before cycle: {self.current_state.phase}")
            # Check if stop event is set
            if self.stop_event and self.stop_event.is_set():
                logger.error("Stop event detected during cycle execution - will complete current cycle")
                self.stop_requested = True
            
            try:
                # Execute one full cycle
                cycles_completed += 1
                logger.info(f"Executing cycle {cycles_completed}/{num_cycles}")
                self._execute_full_cycle()
                logger.info(f"Completed cycle {cycles_completed}/{num_cycles}")
                logger.info(f"After cycle {cycles_completed} - cycle_count: {self.cycle_count}")
                
                # If stop was requested during the cycle, stop after completing it
                if self.stop_requested:
                    logger.error("Stop requested - completed current cycle, stopping execution")
                    break
                
                # Brief pause between cycles for stability
                if cycles_completed < num_cycles and self.is_running and (not self.stop_event or not self.stop_event.is_set()):
                    logger.debug(f"Pause between cycles: {self.current_gait.dwell_time}s")
                    time.sleep(self.current_gait.dwell_time)
                
            except Exception as e:
                logger.error(f"Error in cycle {cycles_completed}: {e}")
                raise
        
        logger.info(f"Completed {cycles_completed} out of {num_cycles} requested cycles")
        
        # Return legs to neutral before stopping
        self.return_legs_to_neutral()
        # Stop the gait generator after completing the cycles
        self.stop()
        return cycles_completed

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
            self.stop_requested = False  # Reset stop flag when starting
            
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
        It continuously executes full gait cycles, handling timing and stability
        monitoring. Each cycle completes all phases of the gait pattern before
        starting the next cycle.
        
        When a stop event is detected, the current cycle is completed before stopping
        to ensure graceful termination of the gait pattern.
        """
        logger.info("Starting gait generation thread")
        cycle_count = 0
        
        while self.is_running:
            if not self.current_state:
                logger.error("No current state set, stopping gait")
                break

            # Check if stop event is set
            if self.stop_event and self.stop_event.is_set():
                logger.error("Stop event detected - will complete current cycle before stopping")
                self.stop_requested = True

            try:
                # Execute full gait cycle
                self._execute_full_cycle()
                
                # If stop was requested during the cycle, stop after completing it
                if self.stop_requested:
                    logger.error("Stop requested - completed current cycle, stopping gait")
                    break
                
                # Pause between cycles using dwell_time
                if self.is_running and (not self.stop_event or not self.stop_event.is_set()):
                    logger.debug(f"Pause between cycles: {self.current_gait.dwell_time}s")
                    time.sleep(self.current_gait.dwell_time)
                
            except Exception as e:
                logger.error(f"\nError in gait generation cycle #{cycle_count}: {e}")
                logger.error(f"Current state: {self.current_state}")
                logger.error(f"Current leg positions: {self.hexapod.current_leg_positions}")
                raise
        
        logger.info(f"Gait generation stopped after {cycle_count} cycles")
        # Return legs to neutral before stopping
        self.return_legs_to_neutral()

    def get_cycle_statistics(self) -> Dict[str, int]:
        """
        Get statistics about the gait execution.
        
        Returns:
            Dict[str, int]: Dictionary containing cycle statistics
                - 'total_cycles': Total number of complete cycles executed
                - 'total_phases': Total number of phases executed
                - 'is_running': Current cycle number (if running)
        """
        return {
            'total_cycles': self.cycle_count,
            'total_phases': self.total_phases_executed,
            'is_running': self.is_running
        }

    def is_stop_requested(self) -> bool:
        """
        Check if a stop has been requested.
        
        Returns:
            bool: True if a stop event has been set and the gait will stop
                  after completing the current cycle
        """
        return self.stop_requested

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
            # Reset cycle statistics
            self.cycle_count = 0
            self.total_phases_executed = 0
            self.stop_requested = False

    def return_legs_to_neutral(self):
        """
        Move all legs to the neutral (0,0) position using gait-appropriate movement patterns.
        For tripod gait: moves legs in groups of 3 (like swing legs)
        For wave gait: moves legs one by one
        This is called after the gait is stopped, for all gaits.
        """
        if not self.current_gait or not self.hexapod:
            logger.warning("No current gait or hexapod, cannot return legs to neutral.")
            return
        
        stance_height = self.current_gait.stance_height if hasattr(self.current_gait, 'stance_height') else 0.0
        
        if isinstance(self.current_gait, TripodGait):
            logger.info("Returning legs to neutral using tripod pattern (groups of 3)")
            # For tripod gait, move legs in two groups like swing legs
            # Group 1: Legs 0, 2, 4 (Right, Left Front, Left Back)
            # Group 2: Legs 1, 3, 5 (Right Front, Left, Right Back)
            
            swing_groups = [[0, 2, 4], [1, 3, 5]]
            
            for group_idx, swing_legs in enumerate(swing_groups):
                logger.info(f"Moving swing group {group_idx + 1}: legs {swing_legs}")
                
                # Calculate paths for all legs in this swing group
                swing_paths = {}
                for leg_idx in swing_legs:
                    target = (0.0, 0.0, -stance_height)
                    self.current_gait.calculate_leg_path(
                        leg_idx,
                        Vector3D(*target),
                        is_swing=True
                    )
                    swing_paths[leg_idx] = self.current_gait.leg_paths[leg_idx]
                    logger.info(f"Leg {leg_idx} path has {len(swing_paths[leg_idx].waypoints)} waypoints")
                
                # Execute movement for this swing group using the existing waypoint execution method
                # Pass empty stance legs list since we're only moving swing legs
                self._execute_waypoints(swing_legs, swing_paths, [], {})
                
                logger.info(f"Swing group {group_idx + 1} returned to neutral")
                
        else:
            # For wave gait or other gaits, move legs one by one
            logger.info("Returning all legs to neutral position one by one.")
            for leg_idx in range(6):
                target = (0.0, 0.0, -stance_height)
                # Use the current gait's path planner for swing legs
                self.current_gait.calculate_leg_path(
                    leg_idx,
                    Vector3D(*target),
                    is_swing=True
                )
                path = self.current_gait.leg_paths[leg_idx]
                logger.info(f"Returning leg {leg_idx} to neutral via {len(path.waypoints)} waypoints.")
                for waypoint in path.waypoints:
                    all_positions = list(self.hexapod.current_leg_positions)
                    all_positions[leg_idx] = (waypoint.x, waypoint.y, waypoint.z)
                    self.hexapod.move_all_legs(all_positions)
                    time.sleep(self.waypoint_dwell_time)
                logger.info(f"Leg {leg_idx} returned to neutral.")
        
        logger.info("All legs returned to neutral position.")