from __future__ import annotations
from typing import TYPE_CHECKING, override
import logging
import threading
import time
import math

from hexapod.task_interface.tasks import Task
from hexapod.robot import PredefinedPosition
from hexapod.interface import get_custom_logger

if TYPE_CHECKING:
    from typing import Optional, Callable
    from hexapod.robot import Hexapod
    from hexapod.lights import LightsInteractionHandler
    from hexapod.odas import ODASDoASSLProcessor

logger = get_custom_logger("task_interface_logger")


class FollowTask(Task):
    """
    Task to make the hexapod follow a target and manage related lights.

    Processes incoming target data to determine follow directions and updates lights based on analysis.
    Uses ODAS output to determine movement direction and controls hexapod movement via gait generator.
    """

    def __init__(
        self,
        hexapod: Hexapod,
        lights_handler: LightsInteractionHandler,
        odas_processor: ODASDoASSLProcessor,
        external_control_paused_event: threading.Event,
        callback: Optional[Callable] = None,
    ) -> None:
        """
        Initialize the FollowTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            odas_processor: The ODAS processor for sound source localization.
            external_control_paused_event: Event to manage external control state.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing FollowTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler
        self.odas_processor = odas_processor
        self.external_control_paused_event = external_control_paused_event
        self.odas_processor.stop_event = self.stop_event

    def _get_movement_direction_from_odas(self) -> str:
        """
        Get movement direction from ODAS processor output using azimuths.

        Returns:
            str: Direction name from BaseGait.DIRECTION_MAP
        """
        # Get the most recent azimuths from ODAS
        azimuths = self.odas_processor.get_tracked_sources_azimuths()
        if not azimuths:
            return "neutral"  # No movement if no sources
        # Use the first azimuth as the target to follow
        azimuth = list(azimuths.values())[0]
        # Normalize to 0-360 range
        azimuth_degrees = azimuth % 360

        # Centered sector mapping
        if azimuth_degrees >= 330 or azimuth_degrees < 30:
            return "right"
        elif azimuth_degrees < 75:
            return "forward right"
        elif azimuth_degrees < 105:
            return "forward"
        elif azimuth_degrees < 150:
            return "forward left"
        elif azimuth_degrees < 210:
            return "left"
        elif azimuth_degrees < 255:
            return "backward left"
        elif azimuth_degrees < 285:
            return "backward"
        elif azimuth_degrees < 330:
            return "backward right"
        else:
            return "neutral"

    def _move_hexapod_in_direction(self, direction_name: str) -> None:
        """
        Move the hexapod in the specified direction using gait generator.

        Args:
            direction_name: Direction name from BaseGait.DIRECTION_MAP
        """
        if not self.hexapod.gait_generator.current_gait:
            # Create a gait if none exists
            gait_params = self.hexapod.gait_params.get("translation", {})
            self.hexapod.gait_generator.create_gait("tripod", **gait_params)
        # Queue the movement direction on the current gait using direction name
        self.hexapod.gait_generator.queue_direction(direction_name)

        # Start gait generation if not already running
        if not self.hexapod.gait_generator.is_running:
            self.hexapod.gait_generator.start()

    @override
    def execute_task(self) -> None:
        """
        Starts following a target and manages lights accordingly.

        Processes target input to identify directions to follow and adjusts lights to indicate following activity.
        Uses ODAS output to determine movement direction and controls hexapod movement.
        """
        logger.info("FollowTask started")
        self._odas_thread = None
        try:
            time.sleep(4)  # Wait for Voice Control to pause and release resources

            # self.lights_handler.off()

            # Start ODAS processor in a background thread
            def _odas_bg() -> None:
                self.odas_processor.start()

            self._odas_thread = threading.Thread(
                target=_odas_bg, name="ODASProcessorThread", daemon=True
            )
            self._odas_thread.start()

            self.hexapod.move_to_position(PredefinedPosition.ZERO)
            self.hexapod.wait_until_motion_complete(stop_event=self.stop_event)

            # Follow loop - continuously move towards tracked sources
            while not self.stop_event.is_set():
                try:
                    # Get movement direction from ODAS
                    direction_name = self._get_movement_direction_from_odas()

                    # Check if we have a valid direction (not neutral)
                    if direction_name != "neutral":
                        logger.debug(f"Moving in direction: {direction_name}")
                        self._move_hexapod_in_direction(direction_name)
                    else:
                        # Stop movement if no clear direction
                        if self.hexapod.gait_generator.is_running:
                            logger.debug("No clear direction, stopping movement")
                            self.hexapod.gait_generator.stop()

                    # Wait before next update
                    self.stop_event.wait(0.5)  # Update direction every 500ms

                except Exception as e:
                    logger.error(f"Error in follow loop: {e}")
                    self.stop_event.wait(1.0)  # Wait longer on error

        except Exception as e:
            logger.exception(f"Follow task failed: {e}")
        finally:
            # Stop gait generation
            if self.hexapod.gait_generator.is_running:
                self.hexapod.gait_generator.stop()

            # Ensure ODAS processor is closed
            if hasattr(self, "odas_processor"):
                self.odas_processor.close()
            # Wait for ODAS thread to finish
            if self._odas_thread is not None:
                self._odas_thread.join(timeout=5)

            logger.info("FollowTask completed")
