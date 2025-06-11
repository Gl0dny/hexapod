from __future__ import annotations
from typing import TYPE_CHECKING, override
import logging

from control.tasks import ControlTask

if TYPE_CHECKING:
    from typing import Optional, Callable
    from robot import Hexapod
    from lights import LightsInteractionHandler
    from odas import ODASDoASSLProcessor

logger = logging.getLogger("control_logger")

class SoundSourceLocalizationTask(ControlTask):
    """
    Task to analyze sound sources and manage related lights.

    Processes incoming sound data to determine source directions and updates lights based on analysis.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, odas_processor: ODASDoASSLProcessor, callback: Optional[Callable] = None) -> None:
        """
        Initialize the SoundSourceLocalizationTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            odas_processor: The ODAS processor for sound source localization.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing SoundSourceLocalizationTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler
        self.odas_processor = odas_processor

    @override
    def execute_task(self) -> None:
        """
        Analyzes sound sources and updates lights accordingly.

        Processes sound input to identify directions of incoming sounds and adjusts lights to indicate sources.
        """
        logger.info("SoundSourceLocalizationTask started")
        try:
            logger.info("Starting sound source localization.")
            self.odas_processor.start()
            
            # Wait for the stop event
            while not self.stop_event.is_set():
                self.stop_event.wait(0.1)
                
        except Exception as e:
            logger.exception(f"Sound source localization task failed: {e}")
        finally:
            logger.info("Stopping sound source localization.")
            self.odas_processor.close()
            logger.info("SoundSourceLocalizationTask completed")