from __future__ import annotations
from typing import TYPE_CHECKING, override
import logging
import threading
import time

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
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, odas_processor: ODASDoASSLProcessor, maintenance_mode_event: threading.Event, callback: Optional[Callable] = None) -> None:
        """
        Initialize the SoundSourceLocalizationTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            odas_processor: The ODAS processor for sound source localization.
            maintenance_mode_event: Event to manage maintenance mode state.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing SoundSourceLocalizationTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler
        self.odas_processor = odas_processor
        self.maintenance_mode_event = maintenance_mode_event

    @override
    def execute_task(self) -> None:
        """
        Execute the sound source localization task.
        """
        logger.info("SoundSourceLocalizationTask started")
        try:
            self.lights_handler.off()

            # Set maintenance mode to pause voice control
            self.maintenance_mode_event.set()

            time.sleep(3)  # Wait for Voice Control to pause ~2.5 seconds to release resources by PvRecorder
            
            # Start ODAS processor
            self.odas_processor.start()
            
            # Wait for the task to complete or be stopped
            while not self.stop_event.is_set():
                time.sleep(0.1)
                
        except Exception as e:
            logger.exception(f"Sound source localization task failed: {e}")
        finally:
            # Ensure ODAS processor is closed
            if hasattr(self, 'odas_processor'):
                self.odas_processor.close()
            # Clear maintenance mode to resume voice control
            self.maintenance_mode_event.clear()
            logger.info("SoundSourceLocalizationTask completed")