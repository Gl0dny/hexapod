import RPi.GPIO as GPIO
import threading
import time
import logging
from typing import Tuple, Optional

logger = logging.getLogger("button_logger")

class ButtonHandler:
    def __init__(self, pin=26, long_press_time=3.0):
        self.pin = pin
        self.is_running = True
        self.lock = threading.Lock()
        self.long_press_time = long_press_time
        self.press_start_time = 0
        self.is_pressed = False
        self.long_press_detected = False
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
    def get_state(self):
        return not GPIO.input(self.pin)  # Returns True when button is pressed
        
    def toggle_state(self):
        with self.lock:
            self.is_running = not self.is_running
            return self.is_running
            
    def check_button(self) -> Tuple[Optional[str], bool]:
        """
        Check button state and return action and system state.
        Returns:
            Tuple[Optional[str], bool]: (action, is_running)
            - action: 'long_press', 'toggle', or None
            - is_running: current system state (only valid for 'toggle' action)
        """
        current_time = time.time()
        button_state = GPIO.input(self.pin)
        
        # Button is pressed
        if button_state == GPIO.LOW:
            if not self.is_pressed:
                self.is_pressed = True
                self.press_start_time = current_time
                self.long_press_detected = False
            elif not self.long_press_detected and (current_time - self.press_start_time) >= self.long_press_time:
                self.long_press_detected = True
                return 'long_press', self.is_running
        
        # Button is released
        elif self.is_pressed:
            self.is_pressed = False
            # Only handle as toggle if it wasn't a long press
            if not self.long_press_detected:
                self.is_running = not self.is_running
                return 'toggle', self.is_running
            # Reset long press flag after handling the release
            self.long_press_detected = False
        
        return None, self.is_running
            
    def cleanup(self):
        GPIO.cleanup(self.pin) 