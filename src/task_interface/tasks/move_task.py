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

class MoveTask(Task):
    """
    Task to move the hexapod in a specified direction using gait generation.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, direction: str, 
                 cycles: Optional[int] = None, duration: Optional[float] = None, 
                 callback: Optional[Callable] = None) -> None:
        """
        Args:
            hexapod: The hexapod object to control.
            lights_handler: The lights handler for visual feedback.
            direction: Direction to move the hexapod.
            cycles: Number of gait cycles to execute (optional).
            duration: Duration to move in seconds (optional).
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing MoveTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler
        self.direction = direction
        self.cycles = cycles
        self.duration = duration

    def _perform_movement(self) -> None:
        """
        Performs the movement using gait generation.
        
        The movement consists of:
        1. Moving to high profile position
        2. Creating and configuring the gait
        3. Executing movement based on cycles, duration, or infinite
        4. Handling stop events during execution
        """
        logger.info(f"Starting movement in {self.direction} direction")
        
        # Define gait parameters
        gait_params = {
            'step_radius': 20.0,
            'leg_lift_distance': 20.0,
            'stance_height': 0.0,
            'dwell_time': 0.3,
            'use_full_circle_stance': False
        }

        # Start in a stable position
        self.hexapod.move_to_position(PredefinedPosition.ZERO)
        self.hexapod.wait_until_motion_complete(self.stop_event)

        if self.stop_event.is_set():
            logger.warning("Move task interrupted during position change.")
            return
        
        self.hexapod.gait_generator.create_gait('tripod', **gait_params)
        self.hexapod.gait_generator.current_gait.set_direction(self.direction)
        
        if self.cycles is not None:
            # Execute specific number of cycles
            logger.info(f"Executing {self.cycles} gait cycles")
            cycles_completed = self.hexapod.gait_generator.execute_cycles(self.cycles)
            logger.info(f"Completed {cycles_completed} cycles")
            
        elif self.duration is not None:
            # Execute for specific duration
            logger.info(f"Executing gait for {self.duration} seconds")
            cycles_completed, elapsed_time = self.hexapod.gait_generator.run_for_duration(self.duration)
            logger.info(f"Duration-based movement completed: {cycles_completed} cycles in {elapsed_time:.2f} seconds")
            
        else:
            # Start infinite gait generation (no cycles or duration specified)
            logger.info("Starting infinite gait generation")
            self.hexapod.gait_generator.start()
            logger.warning("Infinite gait generation started - will continue until stopped externally")
            # Wait until externally stopped
            while not self.stop_event.is_set():
                time.sleep(0.1)
            logger.warning("Move task interrupted by external stop.")

        # Stop the gait generator
        self.hexapod.gait_generator.stop()

    @override
    def execute_task(self) -> None:
        """
        Performs the movement routine.

        Executes the movement using gait generation and updates lights to indicate activity.
        """
        logger.info("MoveTask started")
        try:
            logger.info(f"Performing movement in {self.direction} direction.")
            self.lights_handler.think()
            self._perform_movement()
        except Exception as e:
            logger.exception(f"Error in MoveTask: {e}")
        finally:
            self.hexapod.move_to_position(PredefinedPosition.ZERO)
            self.hexapod.wait_until_motion_complete(self.stop_event) 
            logger.info("MoveTask completed")