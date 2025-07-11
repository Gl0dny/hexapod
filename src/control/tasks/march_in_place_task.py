from __future__ import annotations
from typing import TYPE_CHECKING, override
import logging
import time

from control.tasks import ControlTask
from robot import PredefinedPosition
from gait_generator import TripodGait

if TYPE_CHECKING:
    from typing import Optional, Callable
    from robot import Hexapod
    from lights import LightsInteractionHandler

logger = logging.getLogger("control_logger")

class MarchInPlaceTask(ControlTask):
    """
    Task to perform marching in place routine with the hexapod and manage lights.

    Executes a series of movements to simulate a marching in place motion while maintaining light activity.
    Uses TripodGait for stable marching in place motion.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, duration: Optional[float] = None, callback: Optional[Callable] = None) -> None:
        """
        Initialize the MarchInPlaceTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: Manages lights on the hexapod.
            duration: Duration of marching in place in seconds (default: 10.0).
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing MarchInPlaceTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler
        self.duration = 10.0 if duration is None else float(duration)

    def _perform_march(self) -> None:
        """
        Performs the marching in place motion using TripodGait.
        The motion consists of:
        1. Alternating tripod groups lifting and lowering
        2. No forward movement (swing_distance = 0)
        3. Maintaining body height while marching in place
        """
        logger.info("Starting marching in place motion")
        
        # Start in a stable position
        self.hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
        self.hexapod.wait_until_motion_complete(self.stop_event)
        if self.stop_event.is_set():
            return
        
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
        logger.info("Starting tripod gait for marching in place")
        self.hexapod.gait_generator.start(gait, stop_event=self.stop_event)
        
        # March for specified duration
        logger.info(f"Marching in place for {self.duration} seconds")
        start_time = time.time()
        while time.time() - start_time < self.duration:
            if self.stop_event.is_set():
                logger.info("Marching task interrupted.")
                break
            time.sleep(0.1)  # Check stop event every 100ms
        
        # Stop the gait
        logger.info("Stopping marching in place motion")
        self.hexapod.gait_generator.stop()
        
        # Return to home position
        logger.info("Returning to home position")
        self.hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
        self.hexapod.wait_until_motion_complete(self.stop_event)

    @override
    def execute_task(self) -> None:
        """
        Performs the marching routine.

        Executes the predefined marching movements and updates lights to indicate activity.
        """
        logger.info("MarchTask started")
        try:
            logger.info("Performing marching routine.")
            self.lights_handler.think()
            self._perform_march()
        except Exception as e:
            logger.exception(f"Marching task failed: {e}")
        finally:
            self.hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
            self.hexapod.wait_until_motion_complete(self.stop_event)
            logger.info("MarchTask completed") 