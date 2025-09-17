"""
Base task class for hexapod robot operations.

This module defines the abstract Task class which serves as the base class
for all robot tasks and behaviors. It provides common functionality for
task execution, threading, and lifecycle management.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import threading
import abc

from hexapod.utils import rename_thread
from hexapod.interface import get_custom_logger

if TYPE_CHECKING:
    from typing import Optional, Callable

logger = get_custom_logger("task_interface_logger")


class Task(threading.Thread, abc.ABC):
    """
    Abstract base class for tasks executed by the hexapod.

    Attributes:
        stop_event (threading.Event): Event to signal the task to stop.
        callback (Optional[Callable]): Function to call upon task completion.
    """

    def __init__(self, callback: Optional[Callable] = None) -> None:
        """
        Initializes the Task with threading.Thread.

        Args:
            callback (Optional[Callable]): Function to execute after task completion.
        """
        super().__init__(daemon=True)
        rename_thread(self, self.__class__.__name__)

        self.stop_event: threading.Event = threading.Event()
        self.callback = callback
        self._callback_called = False
        logger.debug(f"{self.__class__.__name__} initialized successfully.")

    def start(self) -> None:
        """
        Start the task in a separate thread.

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
        if self.callback and not self._callback_called:
            self._callback_called = True
            self.callback()

    @abc.abstractmethod
    def execute_task(self) -> None:
        """
        Execute the task and invoke the callback upon completion.

        This method should be overridden by subclasses to define specific task behaviors.
        """
        pass

    def stop_task(self, timeout: float = 5.0) -> None:
        """
        Signals the task to stop and joins the thread.

        Args:
            timeout (float): Maximum time to wait for the task to stop in seconds.

        Sets the stop_event to notify the thread to terminate.
        If the thread is alive, it forcefully stops the thread and invokes the callback if provided.
        """
        logger.info(f"Stopping task: {self.__class__.__name__}")
        self.stop_event.set()
        if self.is_alive():
            try:
                logger.info(
                    f"Waiting for task {self.__class__.__name__} to stop (timeout: {timeout} seconds)"
                )
                self.join(timeout=timeout)
                if self.is_alive():
                    logger.error(
                        f"Task {self.__class__.__name__} did not stop within {timeout}s timeout"
                    )
            except Exception as e:
                logger.error(
                    f"Error while stopping task {self.__class__.__name__}: {e}"
                )
        if self.callback and not self._callback_called:
            self._callback_called = True
            self.callback()
