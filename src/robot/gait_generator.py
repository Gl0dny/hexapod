from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Tuple, Optional
import logging
import threading
import time
from enum import Enum, auto
from dataclasses import dataclass
import numpy as np
from abc import ABC, abstractmethod

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
    def __init__(self, hexapod: Hexapod, imu: Optional[IMU] = None) -> None:
        self.hexapod = hexapod
        self.imu = imu
        self.reference_position = (-22.5, 0.0, 0.0)  # This should match the zero position
        self.gait_graph: Dict[GaitPhase, List[GaitPhase]] = {}
        self._setup_gait_graph()

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
    def __init__(self, hexapod: Hexapod, imu: Optional[IMU] = None) -> None:
        super().__init__(hexapod, imu)
        self.swing_distance = 0  # mm
        self.swing_height = 30   # mm
        self.stance_distance = 30  # mm

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
                dwell_time=2.0,
                stability_threshold=0.2
            )
        else:  # TRIPOD_B
            return GaitState(
                phase=phase,
                swing_legs=[1, 3, 5],
                stance_legs=[0, 2, 4],
                dwell_time=2.0,
                stability_threshold=0.2
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
    def __init__(self, hexapod: Hexapod, imu: Optional[IMU] = None) -> None:
        super().__init__(hexapod, imu)
        self.swing_distance = 0  # mm
        self.swing_height = 30   # mm
        self.stance_distance = 30  # mm

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
            dwell_time=1.0,
            stability_threshold=0.2
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
        """Executes a single gait phase."""
        print(f"\nExecuting phase: {state.phase}")
        print(f"Swing legs: {state.swing_legs}")
        print(f"Stance legs: {state.stance_legs}")
        
        # Calculate target positions for all legs
        target_positions = [None] * 6  # Initialize list for all 6 legs
        
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
        
        print("\nMoving all legs to target positions:")
        for i, pos in enumerate(target_positions):
            print(f"Leg {i} target: {pos}")
        
        # Move all legs to their target positions
        self.hexapod.move_all_legs(target_positions)

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