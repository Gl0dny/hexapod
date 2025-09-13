from __future__ import annotations
from typing import TYPE_CHECKING, override
import logging
import threading
import time

from hexapod.task_interface.tasks import Task

if TYPE_CHECKING:
    from typing import Optional, Callable
    from hexapod.robot import Hexapod
    from hexapod.lights import LightsInteractionHandler
    from hexapod.odas import ODASDoASSLProcessor

logger = logging.getLogger("task_interface_logger")

class SoundSourceLocalizationTask(Task):
    """
    Task to analyze sound sources and manage related lights.

    Processes incoming sound data to determine source directions and updates lights based on analysis.
    """
    def __init__(
            self, 
            hexapod: Hexapod, 
            lights_handler: LightsInteractionHandler, 
            odas_processor: ODASDoASSLProcessor, 
            external_control_paused_event: threading.Event, 
            callback: Optional[Callable] = None
            ) -> None:
        """
        Initialize the SoundSourceLocalizationTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            odas_processor: The ODAS processor for sound source localization.
            external_control_paused_event: Event to manage external control state.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing SoundSourceLocalizationTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler
        self.odas_processor = odas_processor
        self.external_control_paused_event = external_control_paused_event
        self.odas_processor.stop_event = self.stop_event

    @override
    def execute_task(self) -> None:
        """
        Analyzes sound sources and updates lights accordingly.

        Processes sound input to identify directions of incoming sounds and adjusts lights to indicate sources.
        """
        logger.info("SoundSourceLocalizationTask started")
        try:
            self.lights_handler.think()

            time.sleep(4)  # Wait for Voice Control to pause and release resources

            self.lights_handler.off()
            
            # Start ODAS processor
            self.odas_processor.start()
            
            # Wait for the task to complete or be stopped
            while not self.stop_event.is_set():
                self.stop_event.wait(0.1)
                
        except Exception as e:
            logger.exception(f"Sound source localization task failed: {e}")
        finally:
            # Ensure ODAS processor is closed
            if hasattr(self, 'odas_processor'):
                self.odas_processor.close()
            logger.info("SoundSourceLocalizationTask completed")