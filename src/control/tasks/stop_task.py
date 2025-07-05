from __future__ import annotations
from typing import TYPE_CHECKING, override
import logging

from control.tasks import ControlTask
from robot import PredefinedPosition

if TYPE_CHECKING:
    from typing import Optional, Callable
    from robot import Hexapod
    from lights import LightsInteractionHandler

logger = logging.getLogger("control_logger")

class StopTask(ControlTask):
    """
    Task to stop all ongoing tasks and deactivate the hexapod.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the StopTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing StopTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Stops all ongoing tasks, deactivates servos, and turns off lights.
        """
        logger.info("StopTask started")
        try:
            logger.info("Executing StopTask: Stopping all ongoing tasks.")
            if self.control_task and self.control_task.is_alive():
                self.control_task.stop_task()
            
            if self.hexapod:
                self.hexapod.deactivate_all_servos()
                logger.info("Hexapod servos deactivated.")
            
            if self.lights_handler:
                self.lights_handler.off()
                logger.info("Lights turned off.")
            
            print("StopTask: All tasks have been stopped.")
        except Exception as e:
            logger.exception(f"StopTask failed: {e}")
        finally:
            logger.info("StopTask completed")
            self.stop_task()