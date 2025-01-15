from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import threading
import abc

from utils import rename_thread

if TYPE_CHECKING:
    from typing import Optional, Callable

logger = logging.getLogger("control_logger")

class ControlTask(threading.Thread, abc.ABC):
    """
    Abstract base class for control tasks executed by the hexapod.

    Attributes:
        stop_event (threading.Event): Event to signal the task to stop.
        callback (Optional[Callable]): Function to call upon task completion.
    """

    def __init__(self, callback: Optional[Callable] = None) -> None:
        """
        Initializes the ControlTask with threading.Thread.

        Args:
            callback (Optional[Callable]): Function to execute after task completion.
        """
        super().__init__(daemon=True)
        rename_thread(self, self.__class__.__name__)

        self.stop_event: threading.Event = threading.Event()
        self.callback = callback
        logger.debug(f"{self.__class__.__name__} initialized successfully.")

    def start(self) -> None:
        """
        Start the control task in a separate thread.

        Clears the stop event and initiates the thread's run method.
        """
        logger.debug(f"Starting task: {self.__class__.__name__}")
        self.stop_event.clear()
        super().start()

    def run(self) -> None:
        """
        Execute the task and invoke the callback upon completion.
        """
        logger.debug(f"Running task: {self.__class__.__name__}")
        self.execute_task()
        if self.callback:
            self.callback()

    @abc.abstractmethod
    def execute_task(self) -> None:
        """
        Execute the task and invoke the callback upon completion.

        This method should be overridden by subclasses to define specific task behaviors.
        """
        pass

    def stop_task(self) -> None:
        """
        Signals the task to stop and joins the thread.

        Sets the stop_event to notify the thread to terminate.
        If the thread is alive, it forcefully stops the thread and invokes the callback if provided.
        """
        logger.info(f"Stopping task: {self.__class__.__name__}")
        self.stop_event.set()
        if self.is_alive():
            logger.info(f"Task {self.__class__.__name__} forcefully stopping.")
            self.join()

