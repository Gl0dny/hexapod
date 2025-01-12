import logging
import threading
import queue
import sys
import select
from typing import Optional

logger = logging.getLogger("interface_logger")

class InputHandler(threading.Thread):
    """
    Handles user input by running a listener in a separate thread.
    
    Inherits from `threading.Thread` to allow non-blocking input listening.
    
    Attributes:
        input_queue (queue.Queue): Queue to store user inputs.
        stop_input_listener (bool): Flag to stop the input listener thread.
    """

    def __init__(self):
        super().__init__(daemon=True)
        """
        Initializes the InputHandler thread and sets up the input queue.
        """
        logger.debug("Initializing InputHandler")
        self.input_queue = queue.Queue()
        self.stop_input_listener = False
        logger.debug("InputHandler initialized successfully.")
    
    def start(self):
        """
        Starts the input listener thread by invoking the parent `Thread` start method.
        """
        logger.debug("Starting input listener thread.")
        super().start()
        logger.info("Input listener thread started.")

    def run(self):
        """
        Overrides the `run` method of `threading.Thread` to continuously listen for user input 
        and enqueue it.
        """
        logger.debug("Input listener thread running.")
        while not self.stop_input_listener:
            dr, dw, de = select.select([sys.stdin], [], [], 0.1)
            if dr:
                user_input = sys.stdin.readline().strip()
                logger.debug(f"Received user input: {user_input}")
                self.input_queue.put(user_input)
        logger.debug("Input listener thread stopping.")

    def get_input(self, timeout: float = 0.1) -> Optional[str]:
        """
        Retrieves user input in a non-blocking manner by fetching it from the input queue.
        
        Args:
            timeout (float): Time in seconds to wait for user input.
        
        Returns:
            Optional[str]: The user input or None if no input is available.
        """
        logger.debug(f"Attempting to get input with timeout={timeout}")
        try:
            input_data = self.input_queue.get(timeout=timeout)
            logger.debug(f"Retrieved input: {input_data}")
            return input_data
        except queue.Empty:
            logger.debug("No input available.")
            return None

    def shutdown(self):
        """
        Gracefully shuts down the input listener thread by setting the stop flag and joining the thread.
        """
        logger.debug("Shutting down input listener thread.")
        self.stop_input_listener = True
        self.join()
        logger.info("Input listener thread shut down.")