from __future__ import annotations
from typing import TYPE_CHECKING, override
import logging
import time

from control.tasks import ControlTask
from robot import PredefinedPosition, PredefinedAnglePosition

if TYPE_CHECKING:
    from typing import Optional, Callable
    from robot import Hexapod
    from lights import LightsInteractionHandler

logger = logging.getLogger("control_logger")

class SitUpTask(ControlTask):
    """
    Task to perform sit-up routine with the hexapod and manage lights.

    Executes a series of movements to simulate a sit-up motion while maintaining light activity.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, callback: Optional[Callable] = None) -> None:
        """
        Initialize the SitUpTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing SitUpTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler

    def _perform_sit_up(self) -> None:
        """
        Performs the sit-up motion by moving the body up and down along the Z-axis.
        The motion consists of:
        1. Moving up (raising the body)
        2. Holding the position briefly
        3. Moving down (lowering the body)
        4. Holding the position briefly
        
        All movements are calculated relative to the starting reference position (low profile).
        """
        logger.info("Starting sit-up motion")
        
        # Parameters for the sit-up motion
        up_height = 50.0    # mm to raise the body above reference
        down_height = 0.0  # mm to lower the body below reference
        hold_time = 0.5     # seconds to hold each position
        repetitions = 5     # number of sit-ups to perform
        
        # Start in a stable position and store reference
        self.hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
        self.hexapod.wait_until_motion_complete(self.stop_event)
        if self.stop_event.is_set():
            return
        
        # Store the reference position (low profile)
        reference_positions = self.hexapod.current_leg_positions.copy()
        logger.info(f"Reference positions stored: {reference_positions}")
        
        for rep in range(repetitions):
            if self.stop_event.is_set():
                logger.info("Sit-up task interrupted.")
                return
                
            logger.info(f"Performing sit-up repetition {rep + 1}/{repetitions}")
            
            # Move up relative to reference position
            logger.info("Moving body up")
            self.hexapod.move_body(tz=up_height)
            self.hexapod.wait_until_motion_complete(self.stop_event)
            if self.stop_event.is_set():
                return
                
            # Hold up position
            logger.info("Holding up position")
            time.sleep(hold_time)
            
            # Move down relative to reference position
            # Calculate the total movement needed: from up_height to -down_height
            total_down_movement = -(up_height + down_height)
            logger.info("Moving body down")
            self.hexapod.move_body(tz=total_down_movement)
            self.hexapod.wait_until_motion_complete(self.stop_event)
            if self.stop_event.is_set():
                return
            
            # Hold down position
            logger.info("Holding down position")
            time.sleep(hold_time)
            
            # Return to reference position
            # Calculate the movement needed: from -down_height back to 0 (reference)
            return_to_reference = down_height
            logger.info("Returning to reference position")
            self.hexapod.move_body(tz=return_to_reference)
            self.hexapod.wait_until_motion_complete(self.stop_event)
            if self.stop_event.is_set():
                return

    @override
    def execute_task(self) -> None:
        """
        Performs the sit-up routine.

        Executes the predefined sit-up movements and updates lights to indicate activity.
        """
        logger.info("SitUpTask started")
        try:
            logger.info("Performing sit-up routine.")
            self.lights_handler.think()
            self._perform_sit_up()
        except Exception as e:
            logger.exception(f"Sit-up task failed: {e}")
        finally:
            self.hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
            self.hexapod.wait_until_motion_complete(self.stop_event)
            logger.info("SitUpTask completed")