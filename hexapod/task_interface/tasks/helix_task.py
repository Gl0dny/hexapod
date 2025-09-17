from __future__ import annotations
from typing import TYPE_CHECKING, override
import logging
import time

from hexapod.task_interface.tasks import Task
from hexapod.robot import PredefinedPosition, PredefinedAnglePosition
from hexapod.interface import get_custom_logger

if TYPE_CHECKING:
    from typing import Optional, Callable
    from hexapod.robot import Hexapod
    from hexapod.lights import LightsInteractionHandler

logger = get_custom_logger("task_interface_logger")


class HelixTask(Task):
    """
    Task to perform a helix maneuver with the hexapod and manage lights.
    """

    def __init__(
        self,
        hexapod: Hexapod,
        lights_handler: LightsInteractionHandler,
        callback: Optional[Callable] = None,
    ) -> None:
        """
        Initialize the HelixTask.
        """
        # ...existing code...
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def _perform_helix(self) -> None:
        """
        Performs the helix maneuver by moving to helix_minimum and then to helix_maximum positions.
        The motion consists of:
        1. Moving to helix_maximum position
        2. Moving to helix_minimum position
        3. Repeating the cycle

        This creates a twisting motion that resembles a helix pattern.
        """
        logger.info("Starting helix maneuver")

        self.hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
        self.hexapod.wait_until_motion_complete(self.stop_event)

        helix_min_positions = []
        helix_max_positions = []
        for i in range(6):
            # Read the current angles
            _, femur_angle, tibia_angle = self.hexapod.current_leg_angles[i]
            # Use coxa min or max, keep femur/tibia from the cache
            helix_min_positions.append(
                (self.hexapod.coxa_params["angle_min"] + 25, femur_angle, tibia_angle)
            )
            helix_max_positions.append(
                (self.hexapod.coxa_params["angle_max"], femur_angle, tibia_angle)
            )

        self.helix_positions = {
            "helix_minimum": helix_min_positions,
            "helix_maximum": helix_max_positions,
        }

        # Parameters for the helix motion
        repetitions = 2  # number of helix cycles to perform

        for rep in range(repetitions):
            if self.stop_event.is_set():
                logger.info("Helix task interrupted.")
                return

            logger.info(f"Performing helix repetition {rep + 1}/{repetitions}")

            logger.debug("Helix maneuver: Moving to 'helix_maximum'")
            self.hexapod.move_all_legs_angles(self.helix_positions["helix_maximum"])

            self.hexapod.wait_until_motion_complete(self.stop_event)
            if self.stop_event.is_set():
                return

            logger.debug("Helix maneuver: Moving to 'helix_minimum'")
            self.hexapod.move_all_legs_angles(self.helix_positions["helix_minimum"])

            self.hexapod.wait_until_motion_complete(self.stop_event)
            if self.stop_event.is_set():
                return

        logger.debug("Helix maneuver: Finished.")

    @override
    def execute_task(self) -> None:
        """
        Performs the helix routine.

        Executes the predefined helix movements and updates lights to indicate activity.
        """
        logger.info("HelixTask started")
        try:
            logger.info("Performing helix routine.")
            self.lights_handler.think()
            self._perform_helix()
        except Exception as e:
            logger.exception(f"Error in HelixTask: {e}")
        finally:
            logger.info("HelixTask completed")
            self.hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
            self.hexapod.wait_until_motion_complete(self.stop_event)
