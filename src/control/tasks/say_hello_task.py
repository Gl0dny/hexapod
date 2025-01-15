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

class SayHelloTask(ControlTask):
    """
    Task for the hexapod to say hello and manage lights.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the SayHelloTask.
        """
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Makes the hexapod say hello.
        """
        logger.info("SayHelloTask started")
        try:
            logger.info("Saying hello.")
            # self.hexapod.say_hello()
        except Exception as e:
            logger.exception(f"Say hello task failed: {e}")
        finally:
            logger.info("SayHelloTask completed")