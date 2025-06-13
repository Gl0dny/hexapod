#!/usr/bin/env python3

"""
StreamODASAudioTask

This module defines the StreamODASAudioTask class, which is responsible for
streaming audio from ODAS in real-time.
"""

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

class StreamODASAudioTask(ControlTask):
    """
    Task for streaming audio from ODAS in real-time.
    Extends sound source localization functionality to include audio streaming.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, odas_processor: ODASDoASSLProcessor, external_control_paused_event: threading.Event, callback: Optional[Callable] = None) -> None:
        """
        Initialize the StreamODASAudioTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            odas_processor: The ODAS processor for sound source localization.
            external_control_paused_event: Event to manage external control state.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing StreamODASAudioTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler
        self.odas_processor = odas_processor
        self.external_control_paused_event = external_control_paused_event
        self.odas_processor.stop_event = self.stop_event

    @override
    def execute_task(self) -> None:
        """
        Streams audio from ODAS while maintaining sound source localization functionality.
        """
        logger.info("StreamODASAudioTask started")
        try:
            self.lights_handler.think()

            # Set external control paused to pause voice control
            self.external_control_paused_event.set()

            time.sleep(4)  # Wait for Voice Control to pause and release resources by PvRecorder

            self.lights_handler.off()
            
            # Start ODAS processor
            self.odas_processor.start()
            
            # Wait for the task to complete or be stopped
            while not self.stop_event.is_set():
                self.stop_event.wait(0.1)
                
        except Exception as e:
            logger.exception(f"ODAS audio streaming task failed: {e}")
        finally:
            # Ensure ODAS processor is closed
            if hasattr(self, 'odas_processor'):
                self.odas_processor.close()
            # Clear external control paused to resume voice control
            self.external_control_paused_event.clear()
            logger.info("StreamODASAudioTask completed") 