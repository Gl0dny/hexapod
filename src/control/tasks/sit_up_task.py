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

    def perform_sit_up(self) -> None:
        """
        Performs the sit-up motion by moving the body up and down along the Z-axis.
        The motion consists of:
        1. Moving up (raising the body)
        2. Holding the position briefly
        3. Moving down (lowering the body)
        4. Holding the position briefly
        """
        logger.info("Starting sit-up motion")
        
        # Parameters for the sit-up motion
        up_height = 30.0    # mm to raise the body
        down_height = 30.0  # mm to lower the body (more than up_height for more pronounced motion)
        hold_time = 0.5     # seconds to hold each position
        repetitions = 5     # number of sit-ups to perform
        
        try:
            # Start in a stable position
            self.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)
            self.hexapod.wait_until_motion_complete()
            
            for rep in range(repetitions):
                logger.info(f"Performing sit-up repetition {rep + 1}/{repetitions}")
                
                # Move up
                logger.info("Moving body up")
                self.hexapod.move_body(tz=up_height)
                self.hexapod.wait_until_motion_complete()
                
                # Hold up position
                logger.info("Holding up position")
                time.sleep(hold_time)
                
                # Move down (lower than the up position)
                logger.info("Moving body down")
                self.hexapod.move_body(tz=-down_height)
                self.hexapod.wait_until_motion_complete()
                
                # Hold down position
                logger.info("Holding down position")
                time.sleep(hold_time)
                
                # Update lights to indicate progress
                # if self.lights_handler:
                #     self.lights_handler.update_progress((rep + 1) / repetitions)
            
            # Return to home position
            logger.info("Returning to home position")
            self.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)
            self.hexapod.wait_until_motion_complete()
            
        except Exception as e:
            logger.error(f"Error during sit-up motion: {e}")
            # Attempt to return to home position in case of error
            try:
                self.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)
            except:
                pass
            raise

    @override
    def execute_task(self) -> None:
        """
        Performs the sit-up routine.

        Executes the predefined sit-up movements and updates lights to indicate activity.
        """
        logger.info("SitUpTask started")
        try:
            logger.info("Performing sit-up routine.")
            self.perform_sit_up()
        except Exception as e:
            logger.exception(f"Sit-up task failed: {e}")
        finally:
            logger.info("SitUpTask completed")