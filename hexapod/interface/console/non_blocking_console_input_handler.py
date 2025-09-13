"""
Non-blocking console input handler for real-time user interaction.

This module provides a NonBlockingConsoleInputHandler class that allows
the hexapod system to receive user input from the console without blocking
the main execution thread. It uses threading and select to achieve non-blocking
input processing.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import threading
import queue
import sys
import select

if TYPE_CHECKING:
    from typing import Optional

logger = logging.getLogger("interface_logger")

class NonBlockingConsoleInputHandler(threading.Thread):
    """
    Handles non-blocking console user input by running a listener in a separate thread.
    
    Inherits from `threading.Thread` to allow non-blocking input listening.
    
    Attributes:
        input_queue (queue.Queue): Queue to store user inputs.
        stop_input_listener (bool): Flag to stop the input listener thread.
    """

    def __init__(self):
        """
        Initializes the NonBlockingConsoleInputHandler thread and sets up the input queue.
        """
        super().__init__(daemon=True)
        self.input_queue = queue.Queue()
        self.stop_input_listener = False
        logger.debug("NonBlockingConsoleInputHandler initialized successfully.")
    
    def start(self):
        """
        Starts the input listener thread by invoking the parent `Thread` start method.
        """
        super().start()
        logger.debug("Non-blocking console input listener thread started.")

    def run(self):
        """
        Overrides the `run` method of `threading.Thread` to continuously listen for user input 
        and enqueue it.
        """
        logger.debug("Non-blocking console input listener thread running.")
        while not self.stop_input_listener:
            dr, dw, de = select.select([sys.stdin], [], [], 0.1)
            if dr:
                user_input = sys.stdin.readline().strip()
                logger.debug(f"Received user input: {user_input}")
                self.input_queue.put(user_input)
        logger.debug("Non-blocking console input listener thread stopping.")

    def get_input(self, timeout: float = 0.1) -> Optional[str]:
        """
        Retrieves user input in a non-blocking manner by fetching it from the input queue.
        
        Args:
            timeout (float): Time in seconds to wait for user input.
        
        Returns:
            Optional[str]: The user input or None if no input is available.
        """
        try:
            input_data = self.input_queue.get(timeout=timeout)
            logger.debug(f"Retrieved input: {input_data}")
            return input_data
        except queue.Empty:
            return None

    def shutdown(self):
        """
        Gracefully shuts down the input listener thread by setting the stop flag and joining the thread.
        """
        self.stop_input_listener = True
        self.join()
        logger.debug("Non-blocking console input listener thread shut down.")