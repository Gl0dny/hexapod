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

class DanceTask(ControlTask):
    """
    Task to perform dance routine with the hexapod and manage lights.

    Coordinates a sequence of movements to perform a dance routine, syncing with light patterns.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the DanceTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing DanceTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Performs the dance routine.

        Executes a series of dance moves and updates lights to enhance visual effects.
        """
        logger.info("DanceTask started")
        try:
            logger.info("Starting dance routine.")
            # self.hexapod.perform_dance()
        except Exception as e:
            logger.exception(f"Dance task failed: {e}")
        finally:
            logger.info("DanceTask completed")