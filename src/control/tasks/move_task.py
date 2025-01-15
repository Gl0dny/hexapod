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

class MoveTask(ControlTask):
    """
    Task to move the hexapod in a specified direction.
    """
    def __init__(self, hexapod: Hexapod, direction: str, callback: Optional[Callable] = None) -> None:
        """
        Args:
            hexapod: The hexapod object to control.
            direction: Direction to move the hexapod.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing MoveTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.direction = direction

    @override
    def execute_task(self) -> None:
        """
        Moves the hexapod in the specified direction.
        """
        logger.info("MoveTask started")
        try:
            logger.info(f"Moving {self.direction}.")
            # self.hexapod.move(direction=self.direction)
        except Exception as e:
            logger.exception(f"Move task failed: {e}")
        finally:
            logger.info("MoveTask completed")