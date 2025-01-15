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

class SitUpTask(ControlTask):
    """
    Task to perform sit-up routine with the hexapod and manage lights.

    Executes a series of movements to simulate a sit-up motion while maintaining light activity.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the SitUpTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing SitUpTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Performs the sit-up routine.

        Executes the predefined sit-up movements and updates lights to indicate activity.
        """
        logger.info("SitUpTask started")
        try:
            logger.info("Performing sit-up routine.")
            # self.hexapod.perform_sit_up()
        except Exception as e:
            logger.exception(f"Sit-up task failed: {e}")
        finally:
            logger.info("SitUpTask completed")