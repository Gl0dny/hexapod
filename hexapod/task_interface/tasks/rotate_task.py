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

class RotateTask(Task):
    """
    Task to rotate the hexapod by a certain angle, direction, cycles, or duration using gait generation.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, angle: Optional[float] = None, turn_direction: Optional[str] = None, cycles: Optional[int] = None, duration: Optional[float] = None, callback: Optional[Callable] = None) -> None:
        """
        Initialize the RotateTask.

        Args:
            hexapod: The hexapod object to control.
            lights_handler: The lights handler for visual feedback.
            angle: Angle in degrees to rotate (optional).
            turn_direction: Direction to rotate the hexapod (optional).
            cycles: Number of gait cycles to execute (optional).
            duration: Duration to rotate in seconds (optional).
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing RotateTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler
        self.angle = angle
        self.turn_direction = turn_direction
        self.cycles = cycles
        self.duration = duration

    def _perform_rotation(self) -> None:
        """
        Performs the rotation using gait generation.
        
        The rotation consists of:
        1. Creating and configuring the gait
        2. Setting rotation direction
        3. Executing rotation based on angle, cycles, duration, or infinite
        4. Handling stop events during execution
        """
        logger.info(f"Starting rotation with direction: {self.turn_direction}")
        
        # Define gait parameters for rotation
        gait_params = self.hexapod.gait_params.get('rotation', {})

        # Start in a stable position
        self.hexapod.move_to_position(PredefinedPosition.ZERO)
        self.hexapod.wait_until_motion_complete(self.stop_event)
                
        # Determine rotation direction
        rotation_direction = 1.0  # Default clockwise
        if self.turn_direction:
            if self.turn_direction in ("clockwise", "right"):
                rotation_direction = 1.0
            elif self.turn_direction in ("counterclockwise", "left"):
                rotation_direction = -1.0

        self.hexapod.gait_generator.create_gait('tripod', **gait_params)
        self.hexapod.gait_generator.current_gait.set_direction('neutral', rotation=rotation_direction)

        if self.angle is not None:
            # Use the gait generator's angle-based rotation method
            logger.info(f"Rotating {self.angle} degrees using angle-based rotation")
            self.hexapod.gait_generator.execute_rotation_by_angle(
                angle_degrees=self.angle,
                rotation_direction=rotation_direction,
                step_radius=gait_params['step_radius']
            )
            logger.info(f"Started rotation execution for {self.angle} degrees in background thread")
            # Wait for the gait generator thread to finish
            if self.hexapod.gait_generator.thread:
                self.hexapod.gait_generator.thread.join()
            logger.info(f"Completed rotation for {self.angle} degrees")
            
        elif self.cycles is not None:
            # Execute specific number of cycles
            logger.info(f"Executing {self.cycles} rotation cycles")
            self.hexapod.gait_generator.execute_cycles(self.cycles)
            logger.info(f"Started execution of {self.cycles} rotation cycles in background thread")
            # Wait for the gait generator thread to finish
            if self.hexapod.gait_generator.thread:
                self.hexapod.gait_generator.thread.join()
            logger.info(f"Completed {self.cycles} rotation cycles")
            
        elif self.duration is not None:
            # Execute for specific duration
            logger.info(f"Executing rotation for {self.duration} seconds")
            self.hexapod.gait_generator.run_for_duration(self.duration)
            logger.info(f"Started duration-based rotation for {self.duration} seconds in background thread")
            # Wait for the gait generator thread to finish
            if self.hexapod.gait_generator.thread:
                self.hexapod.gait_generator.thread.join()
            logger.info(f"Completed duration-based rotation")
            
        else:
            # Start infinite gait generation (no angle or cycles or duration specified)
            logger.info("Starting infinite gait generation")
            self.hexapod.gait_generator.start()
            logger.warning("Infinite gait generation started - will continue until stopped externally")
            # Wait for the gait generator thread to finish
            if self.hexapod.gait_generator.thread:
                self.hexapod.gait_generator.thread.join()
            logger.info("Infinite gait generation completed")

    @override
    def execute_task(self) -> None:
        """
        Performs the rotation routine.

        Executes the rotation using gait generation and updates lights to indicate activity.
        """
        logger.info("RotateTask started")
        try:
            logger.info(f"Performing rotation with direction: {self.turn_direction}.")
            self.lights_handler.think()
            self._perform_rotation()
        except Exception as e:
            logger.exception(f"Error in RotateTask: {e}")
        finally:
            logger.info("RotateTask completed")
            self.hexapod.move_to_position(PredefinedPosition.ZERO)
            self.hexapod.wait_until_motion_complete(self.stop_event)