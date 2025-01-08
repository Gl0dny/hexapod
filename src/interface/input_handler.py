import threading
import queue
import sys
import select
from typing import Optional

class InputHandler:
    def __init__(self):
        """
        Initializes the InputHandler with a queue.
        """
        self.input_queue = queue.Queue()
        self.stop_input_listener = False
    
    def start(self):
        """
        Starts the input listener thread.
        """
        if not hasattr(self, 'input_thread') or not self.input_thread.is_alive():
            self.input_thread = threading.Thread(target=self._input_listener, daemon=True)
            self.input_thread.start()

    def _input_listener(self):
        """
        Continuously listens for user input in a non-blocking manner and places it into the input queue.
        """
        while not self.stop_input_listener:
            dr, dw, de = select.select([sys.stdin], [], [], 0.1)
            if dr:
                user_input = sys.stdin.readline().strip()
                self.input_queue.put(user_input)

    def get_input(self, timeout: float = 0.1) -> Optional[str]:
        """
        Retrieves user input in a non-blocking manner by fetching it from the input queue.
        
        Args:
            timeout (float): Time in seconds to wait for user input.
        
        Returns:
            Optional[str]: The user input or None if no input is available.
        """
        try:
            return self.input_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def shutdown(self):
        """
        Shuts down the input listener thread gracefully.
        """
        print("Killing input handler")
        self.stop_input_listener = True
        self.input_thread.join()