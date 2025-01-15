from __future__ import annotations
from typing import TYPE_CHECKING, override
import logging

from control.tasks import ControlTask
from robot import PredefinedPosition, PredefinedAnglePosition

if TYPE_CHECKING:
    from typing import Optional, Callable
    from robot import Hexapod
    from lights import LightsInteractionHandler

logger = logging.getLogger("control_logger")

class HelixTask(ControlTask):
    """
    Task to perform a helix maneuver with the hexapod and manage lights.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the HelixTask.
        """
        # ...existing code...
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

        helix_min_positions = []
        helix_max_positions = []
        for i in range(6):
            # Read the current angles
            _, femur_angle, tibia_angle = self.hexapod.current_leg_angles[i]
            # Use coxa min or max, keep femur/tibia from the cache
            helix_min_positions.append((self.hexapod.coxa_params['angle_min']+25, femur_angle, tibia_angle))
            helix_max_positions.append((self.hexapod.coxa_params['angle_max'], femur_angle, tibia_angle))

        self.helix_positions = {
            'helix_minimum': helix_min_positions,
            'helix_maximum': helix_max_positions,
        }

    @override
    def execute_task(self) -> None:
        """
        Performs a helix maneuver by moving to helix_minimum and then to helix_maximum positions.
        """
        try:
            self.lights_handler.think()

            for _ in range(2):

                logger.debug("Helix maneuver: Moving to 'helix_maximum'")
                self.hexapod.move_all_legs_angles(self.helix_positions['helix_maximum'])

                self.hexapod.wait_until_motion_complete(self.stop_event)
                if self.stop_event.is_set():
                    return

                logger.debug("Helix maneuver: Moving to 'helix_minimum'")
                self.hexapod.move_all_legs_angles(self.helix_positions['helix_minimum'])

                self.hexapod.wait_until_motion_complete(self.stop_event)
                if self.stop_event.is_set():
                    return

            logger.debug("Helix maneuver: Finished.")

        except Exception as e:
            logger.exception(f"Error in HelixTask: {e}")

        finally:
            logger.info("HelixTask completed")
            self.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)