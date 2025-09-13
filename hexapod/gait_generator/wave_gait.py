"""
Wave gait implementation for hexapod robot locomotion.

This module implements the WaveGait class which provides a wave walking pattern
where legs move one at a time in a sequential manner. This gait provides
maximum stability but slower movement compared to tripod gait.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from .base_gait import BaseGait, GaitPhase, GaitState

if TYPE_CHECKING:
    from robot import Hexapod

class WaveGait(BaseGait):
    """
    Wave gait pattern where one leg moves at a time with circle-based targeting.
    
    Wave gait is the most stable but slowest gait pattern. Only one leg is in
    swing phase at any time, with the other five legs providing maximum stability.
    This gait is useful for precise movements or when stability is critical.
    
    Leg sequence: 0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 0 -> ... (Right -> Right Front -> Left Front -> Left -> Left Back -> Right Back)
    """
    def __init__(self, hexapod: Hexapod,
                 step_radius: float = 30.0,
                 leg_lift_distance: float = 10.0,
                 stance_height: float = 0.0,
                 dwell_time: float = 0.5,
                 use_full_circle_stance: bool = False) -> None:
        """
        Initialize wave gait with circle-based parameters.
        
        Wave gait moves legs one at a time in sequence for maximum stability:
        - Legs move in order: 0 → 1 → 2 → 3 → 4 → 5 (Right → Right Front → Left Front → Left → Left Back → Right Back)
        - Only one leg is in swing phase at any time
        - Provides maximum stability but slower movement
        
        Args:
            hexapod (Hexapod): The hexapod robot instance
            step_radius (float): Radius of circular workspace for each leg (mm)
            leg_lift_distance (float): Height legs lift during swing (mm)
            stance_height (float): Height above ground for stance (mm). 
                                 A value of 0.0 matches the reference position (starting/home position).
                                 Positive values lower legs (raise body), negative values raise legs (lower body).
            dwell_time (float): Time in each phase (seconds)
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
        super().__init__(hexapod, step_radius, leg_lift_distance,
                        stance_height, dwell_time, use_full_circle_stance)

    def _setup_gait_graph(self) -> None:
        """
        Set up the wave gait graph.
        
        Wave gait cycles through all six legs in sequence:
        WAVE_1 -> WAVE_2 -> WAVE_3 -> WAVE_4 -> WAVE_5 -> WAVE_6 -> WAVE_1 -> ...
        (Right -> Right Front -> Left Front -> Left -> Left Back -> Right Back)
        """
        self.gait_graph[GaitPhase.WAVE_1] = [GaitPhase.WAVE_2]  # Right -> Right Front
        self.gait_graph[GaitPhase.WAVE_2] = [GaitPhase.WAVE_3]  # Right Front -> Left Front
        self.gait_graph[GaitPhase.WAVE_3] = [GaitPhase.WAVE_4]  # Left Front -> Left
        self.gait_graph[GaitPhase.WAVE_4] = [GaitPhase.WAVE_5]  # Left -> Left Back
        self.gait_graph[GaitPhase.WAVE_5] = [GaitPhase.WAVE_6]  # Left Back -> Right Back
        self.gait_graph[GaitPhase.WAVE_6] = [GaitPhase.WAVE_1]  # Right Back -> Right

    def get_state(self, phase: GaitPhase) -> GaitState:
        """
        Get the GaitState for a given wave phase.
        
        Args:
            phase (GaitPhase): One of WAVE_1 through WAVE_6
            
        Returns:
            GaitState: State with one swing leg and five stance legs
        """
        swing_leg = {
            GaitPhase.WAVE_1: 0,  # Right
            GaitPhase.WAVE_2: 1,  # Right Front
            GaitPhase.WAVE_3: 2,  # Left Front
            GaitPhase.WAVE_4: 3,  # Left
            GaitPhase.WAVE_5: 4,  # Left Back
            GaitPhase.WAVE_6: 5   # Right Back
        }[phase]
        
        stance_legs = [i for i in range(6) if i != swing_leg]
        
        return GaitState(
            phase=phase,
            swing_legs=[swing_leg],
            stance_legs=stance_legs,
            dwell_time=self.dwell_time
        ) 