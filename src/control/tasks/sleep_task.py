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

class SleepTask(ControlTask):
    """
    Task to put the hexapod into sleep mode by reducing brightness, graying out lights, and deactivating servos.

    This task ensures the hexapod conserves energy and enters a low-power state.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the SleepTask.

        Args:
            hexapod (Hexapod): The hexapod instance to control.
            lights_handler (LightsInteractionHandler): Handler to manage the hexapod's lights.
            callback (Optional[Callable]): Function to execute after task completion.
        """
        logger.debug("Initializing SleepTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Reduce brightness, set lights to gray, and deactivate all servos to enter sleep mode.
        """
        logger.info("SleepTask started")
        try:
            self.lights_handler.set_brightness(5)
            self.lights_handler.set_single_color(ColorRGB.GRAY)
            self.hexapod.wait_until_motion_complete()
            self.hexapod.deactivate_all_servos(self.stop_event)
            logger.debug("Hexapod is now sleeping")
        except Exception as e:
            logger.exception(f"Error in Sleep task: {e}")
        finally:
            logger.info("SleepTask completed")