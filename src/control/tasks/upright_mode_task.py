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

class UprightModeTask(ControlTask):
    """
    Task to set the hexapod to an upright mode and manage related lights.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing UprightModeTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Sets the hexapod to an upright mode position.
        Positions not defined yet, placeholders only.
        """
        logger.info("UprightModeTask started")
        try:
            self.lights_handler.think()
            self.hexapod.move_to_angles_position(PredefinedAnglePosition.UPRIGHT_MODE)
            self.hexapod.wait_until_motion_complete(self.stop_event)
            logger.debug("Hexapod set to upright mode")

        except Exception as e:
            logger.exception(f"Error in UprightModeTask: {e}")
            
        finally:
            logger.info("UprightModeTask completed")