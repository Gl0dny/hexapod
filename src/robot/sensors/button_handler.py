"""
Button handler for Raspberry Pi GPIO-based system control.

This module provides GPIO button handling functionality for the hexapod robot,
including short press, long press detection, and external control pause management.
It interfaces with the physical button connected to GPIO pin 26 for system control.
"""

import RPi.GPIO as GPIO
import threading
import time
from typing import Tuple, Optional

class ButtonHandler:
    def __init__(self, pin=26, long_press_time=3.0, external_control_paused_event=None):
        self.pin = pin
        self.is_running = True
        self.lock = threading.Lock()
        self.long_press_time = long_press_time
        self.press_start_time = 0
        self.is_pressed = False
        self.long_press_detected = False
        self.external_control_paused_event = external_control_paused_event
        
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
            - action: 'long_press', 'toggle', 'stop_task', or None
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
                # Long press only works when external control is not paused
                if not (self.external_control_paused_event and self.external_control_paused_event.is_set()):
                    return 'long_press', self.is_running
        
        # Button is released
        elif self.is_pressed:
            self.is_pressed = False
            # Only handle as toggle if it wasn't a long press
            if not self.long_press_detected:
                # If external control is paused, treat short press as stop_task instead of toggle
                if self.external_control_paused_event and self.external_control_paused_event.is_set():
                    return 'stop_task', self.is_running
                else:
                    self.is_running = not self.is_running
                    return 'toggle', self.is_running
            # Reset long press flag after handling the release
            self.long_press_detected = False
        
        return None, self.is_running
            
    def cleanup(self):
        GPIO.cleanup(self.pin) 