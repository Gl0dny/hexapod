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

class ShowOffTask(ControlTask):
    """
    Task to perform show-off routine with the hexapod and manage lights.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the ShowOffTask.
        """
        # ...existing code...
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Performs the show-off routine.
        """
        logger.info("ShowOffTask started")
        try:
            logger.info("Performing show-off routine.")
            # self.hexapod.show_off()
        except Exception as e:
            logger.exception(f"Show-off task failed: {e}")
        finally:
            logger.info("ShowOffTask completed")