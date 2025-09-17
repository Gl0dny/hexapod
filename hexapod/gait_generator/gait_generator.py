"""
Gait generation system for hexapod robot locomotion.

This module provides the main GaitGenerator class that orchestrates different
walking gaits for the hexapod robot. It supports multiple gait patterns including
tripod and wave gaits, with real-time gait phase management and smooth transitions.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import threading
import time
import math

from hexapod.utils import rename_thread, Vector3D
from hexapod.gait_generator import BaseGait, GaitPhase, GaitState
from hexapod.gait_generator import TripodGait, WaveGait
from hexapod.interface import get_custom_logger

logger = get_custom_logger("gait_generator_logger")

if TYPE_CHECKING:
    from typing import Dict, List, Optional, Union
    from hexapod.robot import Hexapod


class GaitGenerator:
    """
    Main gait generator that manages the execution of gait patterns.

    This class coordinates the gait state machine, executes leg movements,
    and handles timing. It runs the gait in a separate thread to allow
    continuous movement while the main program continues to run.
    """

    DEFAULT_DWELL_TIME = 1.0  # seconds

    def __init__(
        self, hexapod: Hexapod, stop_event: Optional[threading.Event] = None
    ) -> None:
        """
        Initialize the GaitGenerator with references to the hexapod.

        Args:
            hexapod (Hexapod): The Hexapod instance to control
            stop_event (threading.Event, optional): Event to signal stopping the gait
        """
        self.hexapod = hexapod
        self.is_running: bool = False
        self.thread: Optional[threading.Thread] = None
        self.current_state: Optional[GaitState] = None
        self.current_gait: Optional[BaseGait] = None
        self.stop_event: threading.Event = (
            stop_event if stop_event is not None else threading.Event()
        )
        self.cycle_count: int = 0
        self.total_phases_executed: int = 0
        self.stop_requested: bool = False
        self.pending_direction: Optional[Union[str, tuple]] = None
        self.pending_rotation: Optional[float] = None

    def create_gait(
        self,
        gait_type: str = "tripod",
        *,
        step_radius: float = 30.0,
        leg_lift_distance: float = 20.0,
        stance_height: float = 0.0,
        dwell_time: float = 0.5,
        use_full_circle_stance: bool = False,
    ) -> None:
        """
        Factory method to create and set the current gait instance. Supports 'tripod' and 'wave'.
        All gait parameters can be specified and are forwarded to the gait constructor.
        The created gait is set as the current_gait of the generator.
        Args:
            gait_type (str): The type of gait to create ('tripod' or 'wave').
            step_radius (float): Radius of circular workspace for each leg (mm)
            leg_lift_distance (float): Height legs lift during swing (mm)
            stance_height (float): Height above ground for stance (mm)
            dwell_time (float): Time in each phase (seconds)
            use_full_circle_stance (bool): Stance leg movement pattern (half or full circle)
        """
        gait: BaseGait
        if gait_type == "tripod":
            gait = TripodGait(
                self.hexapod,
                step_radius,
                leg_lift_distance,
                stance_height,
                dwell_time,
                use_full_circle_stance,
            )
        elif gait_type == "wave":
            gait = WaveGait(
                self.hexapod,
                step_radius,
                leg_lift_distance,
                stance_height,
                dwell_time,
                use_full_circle_stance,
            )
        else:
            raise ValueError(f"Unknown gait type: {gait_type}")

        self.current_gait = gait

        # Set the initial state based on gait type
        if gait_type == "tripod":
            self.current_state = self.current_gait.get_state(GaitPhase.TRIPOD_A)
        elif gait_type == "wave":
            self.current_state = self.current_gait.get_state(GaitPhase.WAVE_1)
        else:
            raise ValueError(f"Unknown gait type: {gait_type}")

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
        if self.current_gait is None:
            logger.error("No current gait set, cannot calculate paths")
            return
        
        for leg_idx in state.swing_legs:
            logger.debug(f"\nCalculating swing path for leg {leg_idx}")
            swing_target = self.current_gait.calculate_leg_target(
                leg_idx, is_swing=True
            )
            self.current_gait.calculate_leg_path(leg_idx, swing_target, is_swing=True)
            swing_paths[leg_idx] = self.current_gait.leg_paths[leg_idx]
            logger.debug(
                f"Leg {leg_idx} swing path has {len(swing_paths[leg_idx].waypoints)} waypoints"
            )

        # Calculate stance paths
        for leg_idx in state.stance_legs:
            logger.debug(f"\nCalculating stance path for leg {leg_idx}")
            stance_target = self.current_gait.calculate_leg_target(
                leg_idx, is_swing=False
            )
            self.current_gait.calculate_leg_path(leg_idx, stance_target, is_swing=False)
            stance_paths[leg_idx] = self.current_gait.leg_paths[leg_idx]
            logger.debug(
                f"Leg {leg_idx} stance path has {len(stance_paths[leg_idx].waypoints)} waypoints"
            )

        # Execute all movements simultaneously through waypoints
        # Swing and stance legs move together, with stance legs pushing while swing legs lift/move
        if state.swing_legs or state.stance_legs:
            logger.debug(f"\nExecuting simultaneous movement:")
            logger.debug(f"  Swing legs: {state.swing_legs}")
            logger.debug(f"  Stance legs: {state.stance_legs}")
            self._execute_waypoints(
                state.swing_legs, swing_paths, state.stance_legs, stance_paths
            )

    def _execute_waypoints(
        self,
        swing_legs: List[int],
        swing_paths: Dict[int, BaseGait.LegPath],
        stance_legs: List[int],
        stance_paths: Dict[int, BaseGait.LegPath],
    ) -> None:
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
        logger.debug(
            f"Executing simultaneous movement for {len(swing_legs)} swing legs and {len(stance_legs)} stance legs"
        )

        # Combine all legs and paths for unified execution
        all_legs = swing_legs + stance_legs
        all_paths = {**swing_paths, **stance_paths}

        # Find the maximum number of waypoints across all legs
        max_waypoints = (
            max(len(all_paths[leg_idx].waypoints) for leg_idx in all_legs)
            if all_legs
            else 0
        )
        logger.debug(f"Maximum waypoints across all legs: {max_waypoints}")

        # Track which legs have completed their paths
        completed_legs = set()

        # Move through waypoints simultaneously
        for waypoint_idx in range(max_waypoints):
            logger.debug(f"  Waypoint {waypoint_idx + 1}/{max_waypoints} for all legs")

            # Prepare target positions for all legs at this waypoint
            all_positions = list(
                self.hexapod.current_leg_positions
            )  # Start with current positions

            for leg_idx in all_legs:
                path = all_paths[leg_idx]

                if leg_idx in completed_legs:
                    # This leg has completed its path, keep it at final position
                    final_waypoint = path.waypoints[-1]
                    all_positions[leg_idx] = (
                        final_waypoint.x,
                        final_waypoint.y,
                        final_waypoint.z,
                    )
                    leg_type = "swing" if leg_idx in swing_legs else "stance"
                    logger.debug(
                        f"    {leg_type.capitalize()} leg {leg_idx}: {final_waypoint.to_tuple()} (completed, staying at final position)"
                    )

                elif waypoint_idx < len(path.waypoints):
                    # This leg has more waypoints to go
                    waypoint = path.waypoints[waypoint_idx]
                    all_positions[leg_idx] = (waypoint.x, waypoint.y, waypoint.z)
                    leg_type = "swing" if leg_idx in swing_legs else "stance"
                    logger.debug(
                        f"    {leg_type.capitalize()} leg {leg_idx}: {waypoint.to_tuple()}"
                    )

                    # Check if this is the final waypoint for this leg
                    if waypoint_idx == len(path.waypoints) - 1:
                        completed_legs.add(leg_idx)
                        logger.debug(
                            f"    {leg_type.capitalize()} leg {leg_idx} completed its path"
                        )

                else:
                    # This leg has fewer waypoints, use its final position
                    final_waypoint = path.waypoints[-1]
                    all_positions[leg_idx] = (
                        final_waypoint.x,
                        final_waypoint.y,
                        final_waypoint.z,
                    )
                    leg_type = "swing" if leg_idx in swing_legs else "stance"
                    logger.debug(
                        f"    {leg_type.capitalize()} leg {leg_idx}: {final_waypoint.to_tuple()} (final position)"
                    )
                    completed_legs.add(leg_idx)
                    logger.debug(
                        f"    {leg_type.capitalize()} leg {leg_idx} completed its path"
                    )

            try:
                # Move all legs to their target positions simultaneously
                self.hexapod.move_all_legs(all_positions)

                # Wait for all movements to complete
                # self.hexapod.wait_until_motion_complete()
                dwell_time = (
                    self.current_gait.dwell_time
                    if self.current_gait and hasattr(self.current_gait, "dwell_time")
                    else self.DEFAULT_DWELL_TIME
                )
                time.sleep(dwell_time)  # Delay between waypoints

                logger.debug(
                    f"    All legs moved successfully to waypoint {waypoint_idx + 1}"
                )

            except Exception as e:
                logger.exception(
                    f"    Error moving legs to waypoint {waypoint_idx + 1}: {e}"
                )
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
        - Stop event checking between phases (completes current cycle if stop requested)
        - Error handling and recovery
        """
        logger.info("Starting full gait cycle execution")

        # Always reset to canonical start phase for each cycle
        if self.current_gait is None:
            logger.error("No current gait set, cannot execute cycle")
            return
            
        if isinstance(self.current_gait, TripodGait):
            self.current_state = self.current_gait.get_state(GaitPhase.TRIPOD_A)
        elif isinstance(self.current_gait, WaveGait):
            self.current_state = self.current_gait.get_state(GaitPhase.WAVE_1)

        # Get the starting phase
        if self.current_state is None:
            logger.error("Failed to get current state, cannot execute cycle")
            return
            
        current_phase = self.current_state.phase
        cycle_start_phase = current_phase

        # Determine how many phases constitute a full cycle based on gait type
        phases_per_cycle = len(self.current_gait.gait_graph)
        phases_executed = 0

        logger.info(f"Executing full cycle starting from phase: {cycle_start_phase}")
        logger.info(f"Expected phases per cycle: {phases_per_cycle}")
        logger.info(f"Gait type: {type(self.current_gait).__name__}")

        # Check if stop was requested before starting this cycle
        if self.stop_event.is_set() and not self.stop_requested:
            logger.warning(
                "Stop event detected before cycle start - completing current cycle"
            )
            self.stop_requested = True

        while self.is_running:
            # Check if stop event is set during cycle execution
            if self.stop_event.is_set() and not self.stop_requested:
                logger.warning(
                    "Stop event detected during cycle execution - will complete current cycle"
                )
                self.stop_requested = True

            try:
                # Execute current phase
                if self.current_state is None:
                    logger.error("Current state is None, cannot execute phase")
                    break
                    
                logger.info(
                    f"Executing phase {phases_executed + 1}/{phases_per_cycle}: {self.current_state.phase}"
                )
                self._execute_phase(self.current_state)
                phases_executed += 1

                # Check if we've completed a full cycle
                if phases_executed >= phases_per_cycle:
                    logger.info(f"Completed full gait cycle ({phases_executed} phases)")
                    logger.info(
                        f"Cycle completed - phases_executed: {phases_executed}, phases_per_cycle: {phases_per_cycle}"
                    )
                    break

                # Wait for dwell time
                if self.current_state is None:
                    logger.error("Current state is None, cannot wait for dwell time")
                    break
                    
                logger.debug(
                    f"Waiting for dwell time: {self.current_state.dwell_time}s"
                )
                start_time = time.time()
                while time.time() - start_time < self.current_state.dwell_time:
                    # Check stop event during dwell time
                    if self.stop_event.is_set() and not self.stop_requested:
                        logger.warning(
                            "Stop event detected during dwell time - will complete current cycle"
                        )
                        self.stop_requested = True
                    time.sleep(0.01)  # Small sleep to prevent CPU hogging

                # Check stop event before transitioning
                if self.stop_event.is_set() and not self.stop_requested:
                    logger.warning(
                        "Stop event detected before state transition - will complete current cycle"
                    )
                    self.stop_requested = True

                # If stop was requested, complete the cycle but don't start a new one
                if self.stop_requested:
                    logger.warning(
                        "Stop requested - completing current cycle before stopping"
                    )
                    # Continue to complete the current cycle

                # Transition to next state
                if self.current_gait is None or self.current_state is None:
                    logger.error("Current gait or state is None, cannot transition")
                    break
                    
                next_phases = self.current_gait.gait_graph[self.current_state.phase]
                logger.info(f"Transitioning to next phase: {next_phases[0]}")
                self.current_state = self.current_gait.get_state(next_phases[0])

            except Exception as e:
                logger.exception(f"Error in cycle execution: {e}")
                logger.error(f"Current state: {self.current_state}")
                logger.error(f"Phases executed: {phases_executed}")
                logger.error(
                    f"Current leg positions: {self.hexapod.current_leg_positions}"
                )
                raise

        logger.info(
            f"Full cycle execution completed. Executed {phases_executed} phases"
        )

        # Update cycle statistics
        self.cycle_count += 1
        self.total_phases_executed += phases_executed

    def execute_cycles(self, num_cycles: int) -> None:
        """
        Execute a specific number of gait cycles in a background thread.

        This method executes the specified number of complete gait cycles
        in a separate thread and then stops. Useful for controlled movement
        over a specific distance or for testing purposes.

        When a stop event is detected, the current cycle is completed before stopping
        to ensure graceful termination.

        Args:
            num_cycles (int): Number of complete cycles to execute
        """
        if num_cycles <= 0:
            logger.error(f"Invalid number of cycles: {num_cycles}")
            return

        self.is_running = True
        self.stop_requested = False
        self.stop_event.clear()

        logger.info(f"Executing {num_cycles} gait cycles in background thread")

        # Start gait execution in background thread using unified loop directly
        self.thread = threading.Thread(
            target=self._run_gait_loop, kwargs={"max_cycles": num_cycles}
        )
        rename_thread(self.thread, f"GaitGenerator-Cycles-{num_cycles}")
        self.thread.start()

    def _run_gait_loop(
        self,
        *,
        max_cycles: Optional[int] = None,
        max_duration: Optional[float] = None,
        handle_direction_changes: bool = False,
    ) -> int:
        """
        Shared gait execution loop used by all thread methods.

        This method contains the common logic for executing gait cycles with different
        termination conditions. It handles cycle execution, stop event checking,
        error handling, and cleanup.

        Args:
            max_cycles: Maximum number of cycles to execute (None for unlimited)
            max_duration: Maximum duration to run in seconds (None for unlimited)
            handle_direction_changes: Whether to handle pending direction/rotation changes

        Returns:
            int: Number of cycles completed
        """
        logger.info(
            f"Starting gait loop - max_cycles: {max_cycles}, max_duration: {max_duration}"
        )
        cycles_completed = 0
        start_time = time.time()

        while self.is_running:
            # Check termination conditions
            if max_cycles is not None and cycles_completed >= max_cycles:
                logger.info(f"Reached maximum cycles ({max_cycles}), stopping")
                break

            if max_duration is not None:
                elapsed = time.time() - start_time
                if elapsed >= max_duration:
                    logger.warning(
                        f"Time limit reached ({max_duration}s), will finish current cycle and stop"
                    )
                    self.stop_requested = True

            if self.stop_event.is_set() and not self.stop_requested:
                logger.warning(
                    "Stop event detected, will finish current cycle and stop"
                )
                self.stop_requested = True

            if not self.current_state:
                logger.error("No current state set, stopping gait")
                break

            try:
                # Execute full gait cycle
                cycles_completed += 1
                logger.info(f"Executing cycle {cycles_completed}")
                self._execute_full_cycle()
                logger.info(f"Completed cycle {cycles_completed}")

                # If stop was requested during the cycle, stop after completing it
                if self.stop_requested:
                    logger.info(
                        "Stop requested - completed current cycle, stopping gait"
                    )
                    break

                # Handle pending direction/rotation change after cycle (only for continuous mode)
                if handle_direction_changes and (
                    self.pending_direction is not None
                    or self.pending_rotation is not None
                ):
                    if self.current_gait is None:
                        logger.error("Current gait is None, cannot handle direction changes")
                        break
                        
                    new_direction = (
                        self.pending_direction
                        if self.pending_direction is not None
                        else self.current_gait.direction_input
                    )
                    new_rotation = (
                        self.pending_rotation
                        if self.pending_rotation is not None
                        else self.current_gait.rotation_input
                    )
                    logger.info(
                        f"Direction/rotation change requested: {new_direction}, {new_rotation}, returning to neutral before applying."
                    )
                    self.return_legs_to_neutral()
                    self.current_gait.set_direction(new_direction, new_rotation)
                    logger.info(
                        f"Direction/rotation updated to: {new_direction}, rotation: {new_rotation}"
                    )
                    self.pending_direction = None
                    self.pending_rotation = None

                # Pause between cycles
                if self.is_running and not self.stop_event.is_set():
                    dwell_time = (
                        self.current_gait.dwell_time
                        if self.current_gait
                        and hasattr(self.current_gait, "dwell_time")
                        else self.DEFAULT_DWELL_TIME
                    )
                    logger.debug(f"Pause between cycles: {dwell_time}s")
                    time.sleep(dwell_time)

            except Exception as e:
                logger.exception(f"Error in cycle {cycles_completed}: {e}")
                logger.error(f"Current state: {self.current_state}")
                logger.error(
                    f"Current leg positions: {self.hexapod.current_leg_positions}"
                )
                raise

        # Cleanup
        self.return_legs_to_neutral()
        self._cleanup_thread_state()

        if max_duration is not None:
            elapsed_time = time.time() - start_time
            logger.info(
                f"Completed {cycles_completed} cycles in {elapsed_time:.2f} seconds"
            )
        else:
            logger.info(f"Completed {cycles_completed} cycles")

        return cycles_completed

    def _cleanup_thread_state(self) -> None:
        """
        Clean up thread state without calling self.stop() to avoid deadlock.
        """
        self.is_running = False
        self.current_state = None
        self.current_gait = None
        self.cycle_count = 0
        self.total_phases_executed = 0
        self.stop_requested = False

    def stop(self) -> None:
        """
        Stop the gait generation.

        This method safely stops the gait execution, waits for the thread
        to finish, and cleans up resources.
        """
        if self.is_running:
            self.is_running = False
            self.stop_event.set()

            if self.thread:
                self.thread.join()
            self._cleanup_thread_state()

    def run_for_duration(self, seconds: float) -> None:
        """
        Run the gait for a specific amount of time (in seconds) in a background thread.
        The last cycle will always finish, even if the time is up.
        If a stop event is set, it will also stop after the current cycle.
        """
        if seconds <= 0:
            logger.error(f"Invalid duration: {seconds}")
            return

        self.is_running = True
        self.stop_requested = False
        self.stop_event.clear()

        logger.info(f"Running gait for {seconds:.2f} seconds in background thread")

        # Start gait execution in background thread using unified loop directly
        self.thread = threading.Thread(
            target=self._run_gait_loop, kwargs={"max_duration": seconds}
        )
        rename_thread(self.thread, f"GaitGenerator-Duration-{seconds}s")
        self.thread.start()

    def start(self) -> None:
        """
        Start the gait generation in a separate thread.

        This method starts the gait execution in a background thread using the
        current gait that was set by create_gait(). The gait will continue running
        until stopped or the stop event is set.
        """
        if not self.is_running and self.current_gait:
            self.is_running = True
            self.stop_requested = False  # Reset stop flag when starting
            self.stop_event.clear()

            # Start gait execution in background thread using unified loop directly
            self.thread = threading.Thread(
                target=self._run_gait_loop, kwargs={"handle_direction_changes": True}
            )
            rename_thread(
                self.thread, f"GaitGenerator-{self.current_gait.__class__.__name__}"
            )
            self.thread.start()
        elif not self.current_gait:
            raise ValueError("No current gait set. Call create_gait() first.")

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
            "total_cycles": self.cycle_count,
            "total_phases": self.total_phases_executed,
            "is_running": self.is_running,
        }

    def is_stop_requested(self) -> bool:
        """
        Check if a stop has been requested.

        Returns:
            bool: True if a stop event has been set and the gait will stop
                  after completing the current cycle
        """
        return self.stop_requested

    def _calculate_rotation_per_cycle(self, step_radius: float) -> float:
        """
        Calculate rotation per cycle based on hexapod geometry.

        The calculation is based on the hexapod's physical geometry:
        - End effector radius: hexagon_side_length + coxa_length + femur_length
        - Step radius: gait parameter

        For rotation, each leg moves by step_radius × rotation_input per cycle.
        The effective rotation depends on the hexapod's end effector radius and leg coordination.

        Args:
            step_radius: Gait step radius in mm

        Returns:
            float: Rotation angle per cycle in degrees
        """
        # Use the hexapod's calculated end effector radius
        # This includes: hexagon_side_length + coxa_length + femur_length
        end_effector_radius = self.hexapod.end_effector_radius

        # For rotation, the effective movement radius is the hexapod's end effector radius
        # Each gait cycle moves the hexapod by approximately step_radius distance
        # The rotation angle per cycle = (step_radius / end_effector_radius) * (180/π) degrees

        rotation_per_cycle_radians = step_radius / end_effector_radius
        rotation_per_cycle_degrees = math.degrees(rotation_per_cycle_radians)

        return rotation_per_cycle_degrees

    def _calculate_cycles_for_angle(
        self, angle_degrees: float, step_radius: float
    ) -> int:
        """
        Calculate the number of gait cycles needed to rotate by the specified angle.

        Args:
            angle_degrees: Target rotation angle in degrees
            step_radius: Gait step radius in mm

        Returns:
            int: Number of gait cycles needed
        """
        rotation_per_cycle = self._calculate_rotation_per_cycle(step_radius)
        cycles_needed = abs(angle_degrees) / rotation_per_cycle
        cycles_needed = math.ceil(cycles_needed)

        end_effector_radius = self.hexapod.end_effector_radius
        logger.info(f"Rotation calculation:")
        logger.info(f"  Target angle: {angle_degrees}°")
        logger.info(f"  End effector radius: {end_effector_radius:.1f} mm")
        logger.info(f"  Step radius: {step_radius} mm")
        logger.info(f"  Rotation per cycle: {rotation_per_cycle:.1f}°")
        logger.info(f"  Cycles needed: {cycles_needed}")

        return max(1, cycles_needed)  # Minimum 1 cycle

    def execute_rotation_by_angle(
        self, angle_degrees: float, rotation_direction: float, step_radius: float
    ) -> None:
        """
        Execute rotation by a specific angle using the current gait.

        This method calculates the required number of cycles based on the hexapod's
        physical geometry and executes the rotation using the current gait in a background thread.

        Args:
            angle_degrees: Target rotation angle in degrees (positive = clockwise)
            rotation_direction: Rotation direction multiplier (1.0 = clockwise, -1.0 = counterclockwise)
            step_radius: Gait step radius in mm (uses current gait's step_radius)
        """
        if not self.current_gait:
            raise ValueError("No current gait set. Call create_gait() first.")

        # Use current gait's step_radius
        step_radius = getattr(self.current_gait, "step_radius")

        # Calculate cycles needed for the target angle
        cycles_needed = self._calculate_cycles_for_angle(angle_degrees, step_radius)

        # Set rotation direction on the current gait
        self.current_gait.set_direction("neutral", rotation=rotation_direction)

        # Execute the calculated number of cycles in background thread
        logger.info(
            f"Executing {cycles_needed} cycles for {angle_degrees}° rotation in background thread"
        )
        self.execute_cycles(cycles_needed)

        logger.info(f"Started rotation execution for {angle_degrees}° rotation")

    def return_legs_to_neutral(self) -> None:
        """
        Move all legs to the neutral (0,0) position using gait-appropriate movement patterns.
        For tripod gait: moves legs in groups of 3 (like swing legs)
        For wave gait: moves legs one by one
        This is called after the gait is stopped, for all gaits.
        """
        if not self.current_gait or not self.hexapod:
            logger.warning("No current gait or hexapod, cannot return legs to neutral.")
            return

        stance_height = (
            self.current_gait.stance_height
            if hasattr(self.current_gait, "stance_height")
            else 0.0
        )
        dwell_time = (
            self.current_gait.dwell_time
            if hasattr(self.current_gait, "dwell_time")
            else self.DEFAULT_DWELL_TIME
        )

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
                        leg_idx, Vector3D(*target), is_swing=True
                    )
                    swing_paths[leg_idx] = self.current_gait.leg_paths[leg_idx]
                    logger.info(
                        f"Leg {leg_idx} path has {len(swing_paths[leg_idx].waypoints)} waypoints"
                    )

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
                    leg_idx, Vector3D(*target), is_swing=True
                )
                path = self.current_gait.leg_paths[leg_idx]
                logger.info(
                    f"Returning leg {leg_idx} to neutral via {len(path.waypoints)} waypoints."
                )
                for waypoint in path.waypoints:
                    all_positions = list(self.hexapod.current_leg_positions)
                    all_positions[leg_idx] = (waypoint.x, waypoint.y, waypoint.z)
                    self.hexapod.move_all_legs(all_positions)
                    time.sleep(dwell_time)
                logger.info(f"Leg {leg_idx} returned to neutral.")

        logger.info("All legs returned to neutral position.")

    def queue_direction(
        self, direction: Union[str, tuple], rotation: float = 0.0
    ) -> None:
        """
        Queue a new direction and/or rotation to be applied after the current cycle and a return to neutral.
        This should be called by the controller/gamepad instead of calling BaseGait.set_direction directly.
        The actual direction change will be applied by the gait generator thread at a safe time.
        """
        # WARNING: Do not call self.current_gait.set_direction directly from the controller/gamepad.
        if not self.current_gait:
            return
        current_dir = self.current_gait.direction_input
        current_rot = self.current_gait.rotation_input
        # Convert to tuple for comparison if needed
        if hasattr(current_dir, "to_tuple"):
            current_dir_tuple = current_dir.to_tuple()
        else:
            current_dir_tuple = (
                getattr(current_dir, "x", 0),
                getattr(current_dir, "y", 0),
            )
        if isinstance(direction, str):
            direction_tuple = self.current_gait.DIRECTION_MAP.get(direction, (0, 0))
        elif isinstance(direction, tuple):
            direction_tuple = direction
        else:
            direction_tuple = (0, 0)
        # Only set as pending if different from current
        if (direction_tuple, rotation) != (current_dir_tuple, current_rot):
            self.pending_direction = direction
            self.pending_rotation = rotation

    def is_gait_running(self) -> bool:
        """
        Check if the gait generator is currently running.

        Returns:
            bool: True if the gait generator is running, False otherwise
        """
        return self.is_running and self.thread is not None and self.thread.is_alive()
