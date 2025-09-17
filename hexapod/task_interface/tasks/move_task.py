from __future__ import annotations
from typing import TYPE_CHECKING, override
import logging
import time

from hexapod.task_interface.tasks import Task
from hexapod.robot import PredefinedPosition
from hexapod.interface import get_custom_logger

if TYPE_CHECKING:
    from typing import Optional, Callable
    from hexapod.robot import Hexapod
    from hexapod.lights import LightsInteractionHandler

logger = get_custom_logger("task_interface_logger")


class MoveTask(Task):
    """
    Task to move the hexapod in a specified direction using gait generation.
    """

    def __init__(
        self,
        hexapod: Hexapod,
        lights_handler: LightsInteractionHandler,
        direction: str,
        cycles: Optional[int] = None,
        duration: Optional[float] = None,
        callback: Optional[Callable] = None,
    ) -> None:
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
        gait_params = self.hexapod.gait_params.get("translation", {})

        # Start in a stable position
        self.hexapod.move_to_position(PredefinedPosition.ZERO)
        self.hexapod.wait_until_motion_complete(self.stop_event)

        if self.stop_event.is_set():
            logger.warning("Move task interrupted during position change.")
            return

        self.hexapod.gait_generator.create_gait("tripod", **gait_params)
        if self.hexapod.gait_generator.current_gait is not None:
            self.hexapod.gait_generator.current_gait.set_direction(self.direction)

        if self.cycles is not None:
            # Execute specific number of cycles
            logger.info(f"Executing {self.cycles} gait cycles")
            self.hexapod.gait_generator.execute_cycles(self.cycles)
            logger.info(
                f"Started execution of {self.cycles} cycles in background thread"
            )
            # Wait for the gait generator thread to finish
            if self.hexapod.gait_generator.thread:
                self.hexapod.gait_generator.thread.join()
            logger.info(f"Completed {self.cycles} cycles")

        elif self.duration is not None:
            # Execute for specific duration
            logger.info(f"Executing gait for {self.duration} seconds")
            self.hexapod.gait_generator.run_for_duration(self.duration)
            logger.info(
                f"Started duration-based movement for {self.duration} seconds in background thread"
            )
            # Wait for the gait generator thread to finish
            if self.hexapod.gait_generator.thread:
                self.hexapod.gait_generator.thread.join()
            logger.info(f"Completed duration-based movement")

        else:
            # Start infinite gait generation (no cycles or duration specified)
            logger.info("Starting infinite gait generation")
            self.hexapod.gait_generator.start()
            logger.warning(
                "Infinite gait generation started - will continue until stopped externally"
            )
            # Wait for the gait generator thread to finish
            if self.hexapod.gait_generator.thread:
                self.hexapod.gait_generator.thread.join()
            logger.info("Infinite gait generation completed")

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
