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

class SoundSourceAnalysisTask(ControlTask):
    """
    Task to analyze sound sources and manage related lights.

    Processes incoming sound data to determine source directions and updates lights based on analysis.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the SoundSourceAnalysisTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing SoundSourceAnalysisTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    @override
    def execute_task(self) -> None:
        """
        Analyzes sound sources and updates lights accordingly.

        Processes sound input to identify directions of incoming sounds and adjusts lights to indicate sources.
        """
        logger.info("SoundSourceAnalysisTask started")
        try:
            logger.info("Starting sound source analysis.")
            # self.hexapod.analyze_sound_sources()
        except Exception as e:
            logger.exception(f"Sound source analysis task failed: {e}")
        finally:
            logger.info("SoundSourceAnalysisTask completed")