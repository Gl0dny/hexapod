"""
Button handler for Raspberry Pi GPIO-based system control.

This module provides GPIO button handling functionality for the hexapod robot,
including short press, long press detection, and external control pause management.
It interfaces with the physical button connected to GPIO pin 26 for system control.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import RPi.GPIO as GPIO
import threading
import time

if TYPE_CHECKING:
    from typing import Tuple, Optional


class ButtonHandler:
    """
    GPIO button handler for hexapod robot system control.
    
    Handles physical button input via Raspberry Pi GPIO, providing functionality for:
    - Short press detection (toggle system state or stop current task)
    - Long press detection (system shutdown)
    - External control pause management
    - Thread-safe state management
    
    Attributes:
        pin (int): GPIO pin number for button input
        is_running (bool): Current system running state
        lock (threading.Lock): Thread lock for safe state access
        long_press_time (float): Duration in seconds to detect long press
        press_start_time (float): Timestamp when current press started
        is_pressed (bool): Current button press state
        long_press_detected (bool): Whether current press is detected as long
        external_control_paused_event (Optional[threading.Event]): Event indicating
            if external control is paused
    """
    
    def __init__(
        self,
        pin: int = 26,
        long_press_time: float = 3.0,
        external_control_paused_event: Optional[threading.Event] = None,
    ) -> None:
        """
        Initialize button handler with GPIO configuration.
        
        Args:
            pin (int, optional): GPIO pin number for button input. Defaults to 26.
            long_press_time (float, optional): Duration in seconds to detect long press.
                                             Defaults to 3.0.
            external_control_paused_event (Optional[threading.Event], optional): Event
                indicating if external control is paused. When set, short press
                becomes stop_task instead of toggle. Defaults to None.
        """
        self.pin: int = pin
        self.is_running: bool = True
        self.lock = threading.Lock()
        self.long_press_time: float = long_press_time
        self.press_start_time: float = 0
        self.is_pressed: bool = False
        self.long_press_detected: bool = False
        self.external_control_paused_event: Optional[threading.Event] = (
            external_control_paused_event
        )

        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def get_state(self) -> bool:
        """
        Get current button state.
        
        Returns:
            bool: True if button is currently pressed, False otherwise
        """
        return not GPIO.input(self.pin)  # Returns True when button is pressed

    def toggle_state(self) -> bool:
        """
        Toggle the system running state.
        
        Returns:
            bool: The new running state after toggle
        """
        with self.lock:
            self.is_running = not self.is_running
            return self.is_running

    def check_button(self) -> Tuple[Optional[str], bool]:
        """
        Check button state and return action and system state.
        
        Monitors button press/release events and determines appropriate actions:
        - Short press: toggles system state (or stops current task if external control paused)
        - Long press: triggers system shutdown (only when external control not paused)
        
        Returns:
            Tuple[Optional[str], bool]: A tuple containing:
                - action (Optional[str]): Action triggered by button press:
                    - 'long_press': Long press detected (system shutdown)
                    - 'toggle': Short press detected (toggle system state)
                    - 'stop_task': Short press when external control paused
                    - None: No action triggered
                - is_running (bool): Current system running state
        """
        current_time = time.time()
        button_state = GPIO.input(self.pin)

        # Button is pressed
        if button_state == GPIO.LOW:
            if not self.is_pressed:
                self.is_pressed = True
                self.press_start_time = current_time
                self.long_press_detected = False
            elif (
                not self.long_press_detected
                and (current_time - self.press_start_time) >= self.long_press_time
            ):
                self.long_press_detected = True
                # Long press only works when external control is not paused
                if not (
                    self.external_control_paused_event
                    and self.external_control_paused_event.is_set()
                ):
                    return "long_press", self.is_running

        # Button is released
        elif self.is_pressed:
            self.is_pressed = False
            # Only handle as toggle if it wasn't a long press
            if not self.long_press_detected:
                # If external control is paused, treat short press as stop_task instead of toggle
                if (
                    self.external_control_paused_event
                    and self.external_control_paused_event.is_set()
                ):
                    return "stop_task", self.is_running
                else:
                    self.is_running = not self.is_running
                    return "toggle", self.is_running
            # Reset long press flag after handling the release
            self.long_press_detected = False

        return None, self.is_running

    def cleanup(self) -> None:
        """
        Clean up GPIO resources.
        
        Releases the GPIO pin and cleans up any GPIO-related resources.
        Should be called when the button handler is no longer needed.
        """
        GPIO.cleanup(self.pin)
