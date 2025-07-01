from .base_gait import BaseGait, GaitPhase, GaitState

class WaveGait(BaseGait):
    """
    Wave gait pattern where one leg moves at a time with circle-based targeting.
    """
    def __init__(self, hexapod, step_radius: float = 30.0, leg_lift_distance: float = 10.0, leg_lift_incline: float = 2.0, stance_height: float = 0.0, dwell_time: float = 0.5, stability_threshold: float = 0.2) -> None:
        super().__init__(hexapod, step_radius, leg_lift_distance, leg_lift_incline, stance_height, dwell_time, stability_threshold)

    def _setup_gait_graph(self) -> None:
        self.gait_graph[GaitPhase.WAVE_1] = [GaitPhase.WAVE_2]
        self.gait_graph[GaitPhase.WAVE_2] = [GaitPhase.WAVE_3]
        self.gait_graph[GaitPhase.WAVE_3] = [GaitPhase.WAVE_4]
        self.gait_graph[GaitPhase.WAVE_4] = [GaitPhase.WAVE_5]
        self.gait_graph[GaitPhase.WAVE_5] = [GaitPhase.WAVE_6]
        self.gait_graph[GaitPhase.WAVE_6] = [GaitPhase.WAVE_1]

    def get_state(self, phase: GaitPhase) -> GaitState:
        swing_leg = {
            GaitPhase.WAVE_1: 0,
            GaitPhase.WAVE_2: 1,
            GaitPhase.WAVE_3: 2,
            GaitPhase.WAVE_4: 3,
            GaitPhase.WAVE_5: 4,
            GaitPhase.WAVE_6: 5
        }[phase]
        stance_legs = [i for i in range(6) if i != swing_leg]
        return GaitState(
            phase=phase,
            swing_legs=[swing_leg],
            stance_legs=stance_legs,
            dwell_time=self.dwell_time,
            stability_threshold=self.stability_threshold
        ) 