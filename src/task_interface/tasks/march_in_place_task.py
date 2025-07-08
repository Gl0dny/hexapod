from __future__ import annotations
from typing import TYPE_CHECKING, override
import logging
import time

from task_interface.tasks import Task
from robot import PredefinedPosition

if TYPE_CHECKING:
    from typing import Optional, Callable
    from robot import Hexapod
    from lights import LightsInteractionHandler

logger = logging.getLogger("task_interface_logger")

class MarchInPlaceTask(Task):
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
        self.duration = duration

    def _perform_march(self) -> None:
        """
        Performs the marching in place motion using TripodGait.
        
        The motion consists of:
        1. Moving to low profile position
        2. Creating and configuring tripod gait for marching
        3. Executing marching based on duration or infinite
        4. Handling stop events during execution
        """
        logger.info("Starting marching in place motion")
        
        # Start in a stable position
        self.hexapod.move_to_position(PredefinedPosition.ZERO)
        self.hexapod.wait_until_motion_complete(self.stop_event)
        if self.stop_event.is_set():
            logger.warning("March task interrupted during position change.")
            return
        
        # Configure tripod gait for marching in place
        gait_params = {
            'step_radius': 0.0,      # No forward movement
            'leg_lift_distance': 30.0,       # Lift legs 30mm
            'leg_lift_incline': 2.0,         # Default incline
            'stance_height': 0.0,            # Default stance
            'dwell_time': 0.3,               # Fast stepping for marching
            'use_full_circle_stance': False
        }
        
        self.hexapod.gait_generator.create_gait('tripod', **gait_params)
        
        if self.duration is not None:
            # March for specified duration
            logger.info(f"Marching in place for {self.duration} seconds")
            cycles_completed, elapsed_time = self.hexapod.gait_generator.run_for_duration(self.duration)
            logger.info(f"Marching completed: {cycles_completed} cycles in {elapsed_time:.2f} seconds")
        else:
            # Start infinite marching
            logger.info("Starting infinite marching in place")
            self.hexapod.gait_generator.start()
            logger.warning("Infinite marching started - will continue until stopped externally")
            # Wait until externally stopped
            while not self.stop_event.is_set():
                time.sleep(0.1)
            logger.warning("Marching task interrupted by external stop.")
        
        # Stop the gait generator
        self.hexapod.gait_generator.stop()

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
            logger.exception(f"Error in MarchTask: {e}")
        finally:
            logger.info("MarchTask completed")
            self.hexapod.move_to_position(PredefinedPosition.ZERO)
            self.hexapod.wait_until_motion_complete(self.stop_event) 