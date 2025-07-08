from __future__ import annotations
from typing import TYPE_CHECKING

from .base_gait import BaseGait, GaitPhase, GaitState

if TYPE_CHECKING:
    from robot import Hexapod

class TripodGait(BaseGait):
    """
    Tripod gait pattern where three legs move at a time with circle-based targeting.
    
    Tripod gait is the most stable and efficient gait for hexapods. It divides
    the six legs into two groups of three that alternate between swing and stance
    phases. This provides excellent stability with three legs always supporting
    the robot.
    
    Leg groups:
    - Group A: Legs 0, 2, 4 (Right, Left Front, Left Back)
    - Group B: Legs 1, 3, 5 (Right Front, Left, Right Back)
    """
    def __init__(self, hexapod: Hexapod,
                 step_radius: float = 30.0,
                 leg_lift_distance: float = 20.0,
                 stance_height: float = 0.0,
                 dwell_time: float = 0.5,
                 stability_threshold: float = 0.2) -> None:
        """
        Initialize tripod gait with circle-based parameters.
        
        Tripod gait divides legs into two groups of three that move alternately:
        - Group A: Legs 0, 2, 4 (Right, Left Front, Left Back) swing while Group B stance
        - Group B: Legs 1, 3, 5 (Right Front, Left, Right Back) swing while Group A stance
        
        Args:
            hexapod (Hexapod): The hexapod robot instance
            step_radius (float): Radius of circular workspace for each leg (mm)
            leg_lift_distance (float): Height legs lift during swing (mm)
            stance_height (float): Height above ground for stance (mm). 
                                 A value of 0.0 matches the reference position (starting/home position).
                                 Positive values lower legs (raise body), negative values raise legs (lower body).
            dwell_time (float): Time in each phase (seconds)
            stability_threshold (float): Maximum IMU deviation allowed
        """
        super().__init__(hexapod, step_radius, leg_lift_distance,
                        stance_height, dwell_time, stability_threshold)

    def _setup_gait_graph(self) -> None:
        """
        Set up the tripod gait graph.
        
        Tripod gait has only two phases that alternate:
        TRIPOD_A -> TRIPOD_B -> TRIPOD_A -> ...
        """
        self.gait_graph[GaitPhase.TRIPOD_A] = [GaitPhase.TRIPOD_B]
        self.gait_graph[GaitPhase.TRIPOD_B] = [GaitPhase.TRIPOD_A]

    def get_state(self, phase: GaitPhase) -> GaitState:
        """
        Get the GaitState for a given tripod phase.
        
        Args:
            phase (GaitPhase): Either TRIPOD_A or TRIPOD_B
            
        Returns:
            GaitState: State with appropriate swing/stance leg assignments
        """
        if phase == GaitPhase.TRIPOD_A:
            return GaitState(
                phase=phase,
                swing_legs=[0, 2, 4],  # Right, Left Front, Left Back
                stance_legs=[1, 3, 5],  # Right Front, Left, Right Back
                dwell_time=self.dwell_time,
                stability_threshold=self.stability_threshold
            )
        else:  # TRIPOD_B
            return GaitState(
                phase=phase,
                swing_legs=[1, 3, 5],  # Right Front, Left, Right Back
                stance_legs=[0, 2, 4],  # Right, Left Front, Left Back
                dwell_time=self.dwell_time,
                stability_threshold=self.stability_threshold
            ) 