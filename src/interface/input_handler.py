import logging
import threading
import queue
import sys
import select
from typing import Optional

logger = logging.getLogger("interface_logger")

class InputHandler:
    def __init__(self):
        """
        Initializes the InputHandler with a queue.
        """
        logger.debug("Initializing InputHandler")
        self.input_queue = queue.Queue()
        self.stop_input_listener = False
        logger.debug("InputHandler initialized successfully.")
    
    def start(self):
        """
        Starts the input listener thread.
        """
        logger.debug("Starting input listener thread.")
        if not hasattr(self, 'input_thread') or not self.input_thread.is_alive():
            self.input_thread = threading.Thread(target=self._input_listener, daemon=True)
            self.input_thread.start()
        logger.info("Input listener thread started.")

    def _input_listener(self):
        """
        Continuously listens for user input in a non-blocking manner and places it into the input queue.
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
        Shuts down the input listener thread gracefully.
        """
        logger.debug("Shutting down input listener thread.")
        self.stop_input_listener = True
        self.input_thread.join()
        logger.info("Input listener thread shut down.")