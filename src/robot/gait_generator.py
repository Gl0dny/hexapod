from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Tuple, Optional
import logging
import threading
import time
from enum import Enum, auto
from dataclasses import dataclass
import numpy as np
from abc import ABC, abstractmethod
import math

logger = logging.getLogger("robot_logger")

if TYPE_CHECKING:
    from robot import Hexapod
    from imu import IMU

class GaitPhase(Enum):
    """Represents different phases in a gait cycle."""
    TRIPOD_A = auto()  # Legs 1,3,5 swing, 2,4,6 stance
    TRIPOD_B = auto()  # Legs 2,4,6 swing, 1,3,5 stance
    WAVE_1 = auto()    # Leg 1 swing
    WAVE_2 = auto()    # Leg 2 swing
    WAVE_3 = auto()    # Leg 3 swing
    WAVE_4 = auto()    # Leg 4 swing
    WAVE_5 = auto()    # Leg 5 swing
    WAVE_6 = auto()    # Leg 6 swing

@dataclass
class GaitState:
    """Represents a state in the gait state machine."""
    phase: GaitPhase
    swing_legs: List[int]  # List of leg indices in swing phase
    stance_legs: List[int]  # List of leg indices in stance phase
    dwell_time: float  # Time to spend in this state
    stability_threshold: float  # Maximum allowed IMU deviation

class BaseGait(ABC):
    """Base class for all gait patterns."""
    def __init__(self, hexapod: Hexapod,
                 swing_distance: float = 0.0,
                 swing_height: float = 30.0,
                 stance_distance: float = 0.0,
                 dwell_time: float = 2.0,
                 stability_threshold: float = 0.2,
                 transition_steps: int = 20) -> None:  # Number of steps for smooth transition
        self.hexapod = hexapod
        self.reference_position = (-22.5, 0.0, 0.0)  # This should match the zero position
        self.gait_graph: Dict[GaitPhase, List[GaitPhase]] = {}
        
        # Gait parameters
        self.swing_distance = swing_distance
        self.swing_height = swing_height
        self.stance_distance = stance_distance
        self.dwell_time = dwell_time
        self.stability_threshold = stability_threshold
        self.transition_steps = transition_steps
        
        self._setup_gait_graph()

    def ease_in_out_quad(self, t: float) -> float:
        """Quadratic easing function for smooth acceleration and deceleration."""
        return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2

    def calculate_swing_trajectory(self, start_pos: Tuple[float, float, float], 
                                 end_pos: Tuple[float, float, float], 
                                 progress: float) -> Tuple[float, float, float]:
        """
        Calculate a point along the swing trajectory using a parabolic path.
        
        Args:
            start_pos: Starting position (x, y, z)
            end_pos: Ending position (x, y, z)
            progress: Progress from 0 to 1
            
        Returns:
            Current position along the trajectory
        """
        # Apply easing to the progress
        eased_progress = self.ease_in_out_quad(progress)
        
        # Linear interpolation for x and y
        x = start_pos[0] + eased_progress * (end_pos[0] - start_pos[0])
        y = start_pos[1] + eased_progress * (end_pos[1] - start_pos[1])
        
        # Parabolic height profile
        # Use 4 * t * (1-t) to create a smooth parabolic curve
        # But ensure we reach the target height at the end
        if progress < 1.0:
            height_factor = 4 * eased_progress * (1 - eased_progress)
            z = start_pos[2] + height_factor * self.swing_height
        else:
            z = end_pos[2]  # Ensure we reach the target height
        
        return (x, y, z)

    def calculate_stance_trajectory(self, start_pos: Tuple[float, float, float],
                                  end_pos: Tuple[float, float, float],
                                  progress: float) -> Tuple[float, float, float]:
        """
        Calculate a point along the stance trajectory with smooth transition.
        
        Args:
            start_pos: Starting position (x, y, z)
            end_pos: Ending position (x, y, z)
            progress: Progress from 0 to 1
            
        Returns:
            Current position along the trajectory
        """
        # Apply easing to the progress
        eased_progress = self.ease_in_out_quad(progress)
        
        # Linear interpolation for all coordinates
        x = start_pos[0] + eased_progress * (end_pos[0] - start_pos[0])
        y = start_pos[1] + eased_progress * (end_pos[1] - start_pos[1])
        z = start_pos[2] + eased_progress * (end_pos[2] - start_pos[2])
        
        return (x, y, z)

    @abstractmethod
    def _setup_gait_graph(self) -> None:
        """Set up the gait graph for the specific gait pattern."""
        pass

    @abstractmethod
    def get_state(self, phase: GaitPhase) -> GaitState:
        """Get the GaitState for a given phase."""
        pass

    @abstractmethod
    def get_swing_position(self, leg_index: int) -> Tuple[float, float, float]:
        """Calculate the swing position for a given leg."""
        pass

    @abstractmethod
    def get_stance_position(self, leg_index: int) -> Tuple[float, float, float]:
        """Calculate the stance position for a given leg."""
        pass

class TripodGait(BaseGait):
    """Tripod gait pattern where three legs move at a time."""
    def __init__(self, hexapod: Hexapod,
                 swing_distance: float = 0.0,
                 swing_height: float = 30.0,
                 stance_distance: float = 0.0,
                 dwell_time: float = 2.0,
                 stability_threshold: float = 0.2) -> None:
        super().__init__(hexapod, swing_distance, swing_height, stance_distance,
                        dwell_time, stability_threshold)

    def _setup_gait_graph(self) -> None:
        """Set up the tripod gait graph."""
        self.gait_graph[GaitPhase.TRIPOD_A] = [GaitPhase.TRIPOD_B]
        self.gait_graph[GaitPhase.TRIPOD_B] = [GaitPhase.TRIPOD_A]

    def get_state(self, phase: GaitPhase) -> GaitState:
        """Get the GaitState for a given tripod phase."""
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

    def get_swing_position(self, leg_index: int) -> Tuple[float, float, float]:
        """Calculate the swing position for a given leg."""
        return (
            self.reference_position[0] + self.swing_distance,
            self.reference_position[1],
            self.reference_position[2] + self.swing_height
        )

    def get_stance_position(self, leg_index: int) -> Tuple[float, float, float]:
        """Calculate the stance position for a given leg."""
        return (
            self.reference_position[0] - self.stance_distance,
            self.reference_position[1],
            self.reference_position[2]
        )

class WaveGait(BaseGait):
    """Wave gait pattern where one leg moves at a time."""
    def __init__(self, hexapod: Hexapod,
                 swing_distance: float = 0.0,
                 swing_height: float = 30.0,
                 stance_distance: float = 0.0,
                 dwell_time: float = 1.0,  # Shorter dwell time for wave gait
                 stability_threshold: float = 0.2) -> None:
        super().__init__(hexapod, swing_distance, swing_height, stance_distance,
                        dwell_time, stability_threshold)

    def _setup_gait_graph(self) -> None:
        """Set up the wave gait graph."""
        self.gait_graph[GaitPhase.WAVE_1] = [GaitPhase.WAVE_2]
        self.gait_graph[GaitPhase.WAVE_2] = [GaitPhase.WAVE_3]
        self.gait_graph[GaitPhase.WAVE_3] = [GaitPhase.WAVE_4]
        self.gait_graph[GaitPhase.WAVE_4] = [GaitPhase.WAVE_5]
        self.gait_graph[GaitPhase.WAVE_5] = [GaitPhase.WAVE_6]
        self.gait_graph[GaitPhase.WAVE_6] = [GaitPhase.WAVE_1]

    def get_state(self, phase: GaitPhase) -> GaitState:
        """Get the GaitState for a given wave phase."""
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

    def get_swing_position(self, leg_index: int) -> Tuple[float, float, float]:
        """Calculate the swing position for a given leg."""
        return (
            self.reference_position[0] + self.swing_distance,
            self.reference_position[1],
            self.reference_position[2] + self.swing_height
        )

    def get_stance_position(self, leg_index: int) -> Tuple[float, float, float]:
        """Calculate the stance position for a given leg."""
        return (
            self.reference_position[0] - self.stance_distance,
            self.reference_position[1],
            self.reference_position[2]
        )

class GaitGenerator:
    def __init__(self, hexapod: Hexapod, imu: Optional[IMU] = None) -> None:
        """
        Initializes the GaitGenerator with a reference to the Hexapod and IMU.

        Args:
            hexapod (Hexapod): The Hexapod instance to control.
            imu (IMU, optional): The IMU instance for stability monitoring.
        """
        self.hexapod = hexapod
        self.imu = imu
        self.is_running = False
        self.thread = None
        self.current_state: Optional[GaitState] = None
        self.current_gait: Optional[BaseGait] = None
        self.current_positions: List[Tuple[float, float, float]] = [None] * 6

    def _check_stability(self) -> bool:
        """Checks if the robot is stable based on IMU readings."""
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
        """Executes a single gait phase with smooth transitions."""
        print(f"\nExecuting phase: {state.phase}")
        print(f"Swing legs: {state.swing_legs}")
        print(f"Stance legs: {state.stance_legs}")
        
        # Calculate target positions for all legs
        target_positions = [None] * 6
        
        # Set swing positions
        for leg_idx in state.swing_legs:
            print(f"\nCalculating swing position for leg {leg_idx}")
            target_positions[leg_idx] = self.current_gait.get_swing_position(leg_idx)
            print(f"Leg {leg_idx} swing target: {target_positions[leg_idx]}")
        
        # Set stance positions
        for leg_idx in state.stance_legs:
            print(f"\nCalculating stance position for leg {leg_idx}")
            target_positions[leg_idx] = self.current_gait.get_stance_position(leg_idx)
            print(f"Leg {leg_idx} stance target: {target_positions[leg_idx]}")
        
        # Execute smooth transitions
        for step in range(self.current_gait.transition_steps):
            progress = step / (self.current_gait.transition_steps - 1)
            current_positions = [None] * 6
            
            # Calculate current positions for all legs
            for leg_idx in range(6):
                if leg_idx in state.swing_legs:
                    current_positions[leg_idx] = self.current_gait.calculate_swing_trajectory(
                        self.current_positions[leg_idx] or self.hexapod.get_leg_position(leg_idx),
                        target_positions[leg_idx],
                        progress
                    )
                else:
                    current_positions[leg_idx] = self.current_gait.calculate_stance_trajectory(
                        self.current_positions[leg_idx] or self.hexapod.get_leg_position(leg_idx),
                        target_positions[leg_idx],
                        progress
                    )
            
            # Move all legs to their current positions
            self.hexapod.move_all_legs(current_positions)
            self.current_positions = current_positions
            
            # Small delay between steps for smooth movement
            time.sleep(0.02)  # 50Hz update rate

    def start(self, gait: BaseGait) -> None:
        """
        Starts the gait generation in a separate thread.

        Args:
            gait (BaseGait): The gait instance to execute.
        """
        if not self.is_running:
            self.is_running = True
            self.current_gait = gait
            if isinstance(gait, TripodGait):
                self.current_state = gait.get_state(GaitPhase.TRIPOD_A)
            elif isinstance(gait, WaveGait):
                self.current_state = gait.get_state(GaitPhase.WAVE_1)
            else:
                raise ValueError(f"Unknown gait type: {type(gait)}")
            self.thread = threading.Thread(target=self.run_gait)
            self.thread.start()

    def run_gait(self) -> None:
        """Executes the gait pattern continuously."""
        print("\nStarting gait generation thread")
        while self.is_running:
            if not self.current_state:
                print("No current state set, stopping gait")
                break

            try:
                # Execute current phase
                self._execute_phase(self.current_state)
                
                # Wait for dwell time or until stability is compromised
                print(f"\nWaiting for dwell time: {self.current_state.dwell_time}s")
                start_time = time.time()
                while (time.time() - start_time < self.current_state.dwell_time and
                       self._check_stability()):
                    time.sleep(0.01)  # Small sleep to prevent CPU hogging

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
        """Stops the gait generation."""
        if self.is_running:
            self.is_running = False
            if self.thread:
                self.thread.join()
            self.current_state = None
            self.current_gait = None