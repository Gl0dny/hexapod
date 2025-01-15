from __future__ import annotations
from typing import TYPE_CHECKING, override
import logging

from control.tasks import ControlTask
from robot import PredefinedPosition, PredefinedAnglePosition

if TYPE_CHECKING:
    from typing import Optional, Callable
    from robot import Hexapod
    from lights import LightsInteractionHandler

logger = logging.getLogger("control_logger")

class RunSequenceTask(ControlTask):
    """
    Executes a predefined sequence of tasks.
    """
    def __init__(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, sequence_name: str, callback: Optional[Callable] = None) -> None:
        """
        Args:
            hexapod: Hexapod object to control.
            lights_handler: Handles lights activity.
            sequence_name: Name of the sequence to run.
            callback: Function to call upon task completion.
        """
        logger.debug("Initializing RunSequenceTask")
        super().__init__(callback)
        self.hexapod = hexapod
        self.lights_handler = lights_handler
        self.sequence_name = sequence_name
        # self.sequence_mapping = {
        #     'startup': [WakeUpTask, MoveTask],
        #     'shutdown': [StopTask, SleepTask],
        #     'dance_sequence': [DanceTask, SitUpTask, ShowOffTask],
            # Add more sequences as needed
        # }

    @override
    def execute_task(self) -> None:
        """
        Runs the tasks associated with the selected sequence.
        """
        logger.info(f"RunSequenceTask started: {self.sequence_name}")
        try:
            logger.info(f"Starting sequence: {self.sequence_name}")
            tasks = self.sequence_mapping.get(self.sequence_name, [])
            for task_class in tasks:
                if self.stop_event.is_set():
                    logger.info("RunSequenceTask interrupted.")
                    break
                task = task_class(self.hexapod, self.lights_handler)
                task.start()
                task.join()
        except Exception as e:
            logger.exception(f"RunSequenceTask '{self.sequence_name}' failed: {e}")
        finally:
            logger.info(f"Sequence '{self.sequence_name}' completed.")
            self.stop_task()