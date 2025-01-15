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

class RotateTask(ControlTask):
    """
    Task to rotate the hexapod by a certain angle or direction.
    """
    def __init__(self, hexapod: Hexapod, angle: Optional[float] = None, direction: Optional[str] = None, callback: Optional[Callable] = None) -> None:
        """
        Initialize the RotateTask.

        Args:
            hexapod: The hexapod object to control.
            angle: Angle in degrees to rotate.
            direction: Direction to rotate the hexapod.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing RotateTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.angle = angle
        self.direction = direction

    @override
    def execute_task(self) -> None:
        """
        Rotates the hexapod based on the provided angle or direction.
        """
        logger.info("RotateTask started")
        try:
            if self.angle:
                logger.info(f"Rotating {self.angle} degrees.")
                self.hexapod.rotate(angle=self.angle)
            elif self.direction:
                logger.info(f"Rotating to the {self.direction}.")
                # self.hexapod.rotate(direction=self.direction)
            else:
                logger.error("No angle or direction provided for rotation.")
        except Exception as e:
            logger.exception(f"Rotate task failed: {e}")
        finally:
            logger.info("RotateTask completed")