from .base_gait import BaseGait, GaitPhase, GaitState

class TripodGait(BaseGait):
    """
    Tripod gait pattern where three legs move at a time with circle-based targeting.
    """
    def __init__(self, hexapod, step_radius: float = 30.0, leg_lift_distance: float = 10.0, leg_lift_incline: float = 2.0, stance_height: float = 0.0, dwell_time: float = 0.5, stability_threshold: float = 0.2) -> None:
        super().__init__(hexapod, step_radius, leg_lift_distance, leg_lift_incline, stance_height, dwell_time, stability_threshold)

    def _setup_gait_graph(self) -> None:
        self.gait_graph[GaitPhase.TRIPOD_A] = [GaitPhase.TRIPOD_B]
        self.gait_graph[GaitPhase.TRIPOD_B] = [GaitPhase.TRIPOD_A]

    def get_state(self, phase: GaitPhase) -> GaitState:
        if phase == GaitPhase.TRIPOD_A:
            return GaitState(
                phase=phase,
                swing_legs=[0, 2, 4],
                stance_legs=[1, 3, 5],
                dwell_time=self.dwell_time,
                stability_threshold=self.stability_threshold
            )
        else:
            return GaitState(
                phase=phase,
                swing_legs=[1, 3, 5],
                stance_legs=[0, 2, 4],
                dwell_time=self.dwell_time,
                stability_threshold=self.stability_threshold
            ) 