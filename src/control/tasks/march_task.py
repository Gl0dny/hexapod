from __future__ import annotations
from typing import TYPE_CHECKING, override
import logging
import time

from control.tasks import ControlTask
from robot import PredefinedPosition, PredefinedAnglePosition
from robot import TripodGait

if TYPE_CHECKING:
    from typing import Optional, Callable
    from robot import Hexapod
    from lights import LightsInteractionHandler

logger = logging.getLogger("control_logger")

class MarchTask(ControlTask):
    """
    Task to perform marching in place routine with the hexapod and manage lights.

    Executes a series of movements to simulate a marching motion while maintaining light activity.
    Uses TripodGait for stable marching motion.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, duration: float = 10.0, callback: Optional[Callable] = None) -> None:
        """
        Initialize the MarchTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            duration: Duration of marching in seconds (default: 5.0).
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing MarchTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler
        self.duration = duration

    def perform_march(self) -> None:
        """
        Performs the marching in place motion using TripodGait.
        The motion consists of:
        1. Alternating tripod groups lifting and lowering
        2. No forward movement (swing_distance = 0)
        3. Maintaining body height while marching
        """
        logger.info("Starting marching motion")
        
        try:
            # Start in a stable position
            self.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)
            self.hexapod.wait_until_motion_complete()
            
            # Configure tripod gait for marching in place
            gait_params = {
                'swing_distance': 0.0,      # No forward movement
                'swing_height': 30.0,       # Lift legs 30mm
                'stance_distance': 0.0,     # No backward movement
                'dwell_time': 1.0,         # One second per step
                'stability_threshold': 0.2  # Standard stability threshold
            }
            
            # Create and start the tripod gait
            gait = TripodGait(self.hexapod, **gait_params)
            logger.info("Starting tripod gait for marching")
            self.hexapod.gait_generator.start(gait)
            
            # March for specified duration
            logger.info(f"Marching for {self.duration} seconds")
            time.sleep(self.duration)
            
            # Stop the gait
            logger.info("Stopping marching motion")
            self.hexapod.gait_generator.stop()
            
            # Return to home position
            logger.info("Returning to home position")
            self.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)
            self.hexapod.wait_until_motion_complete()
            
        except Exception as e:
            logger.error(f"Error during marching motion: {e}")
            # Attempt to stop gait and return to home position in case of error
            try:
                self.hexapod.gait_generator.stop()
                self.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)
            except:
                pass
            raise

    @override
    def execute_task(self) -> None:
        """
        Performs the marching routine.

        Executes the predefined marching movements and updates lights to indicate activity.
        """
        logger.info("MarchTask started")
        try:
            logger.info("Performing marching routine.")
            self.perform_march()
        except Exception as e:
            logger.exception(f"Marching task failed: {e}")
        finally:
            logger.info("MarchTask completed") 