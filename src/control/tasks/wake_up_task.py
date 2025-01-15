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

class WakeUpTask(ControlTask):
    """
    Task to wake up the hexapod, adjust lighting, and move to the HOME position.

    This task ramps up brightness, plays a rainbow lighting effect, and moves the hexapod to its home position.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the WakeUpTask.

        Args:
            hexapod (Hexapod): The hexapod instance to control.
            lights_handler (LightsInteractionHandler): Handler to manage the hexapod's lights.
            callback (Optional[Callable]): Function to execute after task completion.
        """
        logger.debug("Initializing WakeUpTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Ramp up brightness, activate rainbow lighting, and move the hexapod to the HOME position.
        """
        logger.info("WakeUpTask started")
        try:
            self.lights_handler.set_brightness(50)
            self.lights_handler.rainbow()
            self.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)
            self.hexapod.wait_until_motion_complete(self.stop_event)
            logger.debug("Hexapod woke up")
        except Exception as e:
            logger.exception(f"Error in Wake up task: {e}")
        finally:
            logger.info("WakeUpTask completed")