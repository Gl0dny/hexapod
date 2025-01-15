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

class EmergencyStopTask(ControlTask):
    """
    Task to perform an emergency stop, deactivating all servos and turning off lights.

    This task ensures that the hexapod halts all activities immediately for safety.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the EmergencyStopTask.

        Args:
            hexapod (Hexapod): The hexapod instance to control.
            lights_handler (LightsInteractionHandler): Handler to manage the hexapod's lights.
            callback (Optional[Callable]): Function to execute after task completion.
        """
        logger.debug("Initializing EmergencyStopTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Deactivate all servos and turn off lights to perform an emergency stop.
        """
        logger.info("EmergencyStopTask started")
        try:
            logger.info("Executing emergency stop.")
            self.hexapod.deactivate_all_servos()
            logger.debug("All servos deactivated")
            self.lights_handler.off()
            logger.debug("All lights turned off")
        except Exception as e:
            logger.exception(f"Emergency stop failed: {e}")
        finally:
            logger.info("EmergencyStopTask completed")
            self.stop_task()