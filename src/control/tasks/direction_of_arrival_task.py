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

class DirectionOfArrivalTask(ControlTask):
    """
    Task to calculate the direction of arrival of sounds and manage lights.

    Determines the direction from which a sound originates and updates visual indicators accordingly.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the DirectionOfArrivalTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing DirectionOfArrivalTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Calculates the direction of arrival of sounds and updates lights.

        Uses sound analysis to determine the origin direction and updates light indicators to reflect this information.
        """
        logger.info("DirectionOfArrivalTask started")
        try:
            logger.info("Calculating direction of arrival.")
            # direction = self.hexapod.calculate_direction_of_arrival()
            # logger.info(f"Sound is coming from: {direction}")
        except Exception as e:
            logger.exception(f"Direction of arrival task failed: {e}")
        finally:
            logger.info("DirectionOfArrivalTask completed")