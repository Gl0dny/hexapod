
import threading
import queue
from typing import Optional

class InputHandler:
    def __init__(self):
        """
        Initializes the InputHandler with a queue and starts the input listener thread.
        """
        self.input_queue = queue.Queue()
        self.stop_input_listener = False
        self.input_thread = threading.Thread(target=self._input_listener, daemon=True)
        self.input_thread.start()

    def _input_listener(self):
        """
        Continuously listens for user input and places it into the input queue.
        """
        while not self.stop_input_listener:
            try:
                user_input = input()
                self.input_queue.put(user_input)
            except EOFError:
                # Handle end-of-file condition if needed
                self.input_queue.put(None)
            except Exception:
                self.input_queue.put(None)

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
        self.stop_input_listener = True