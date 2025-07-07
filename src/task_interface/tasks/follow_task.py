from __future__ import annotations
from typing import TYPE_CHECKING, override
import logging

from task_interface.tasks import Task
from robot import PredefinedPosition

if TYPE_CHECKING:
    from typing import Optional, Callable
    from robot import Hexapod
    from lights import LightsInteractionHandler

logger = logging.getLogger("task_interface_logger")

class FollowTask(Task):
    """
    Task to make the hexapod follow a target and manage related lights.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the FollowTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing FollowTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Starts following a target and manages lights accordingly.
        """
        logger.info("FollowTask started")
        try:
            logger.info("Starting follow task.")
            # self.hexapod.start_following()
        except Exception as e:
            logger.exception(f"Follow task failed: {e}")
        finally:
            logger.info("FollowTask completed")