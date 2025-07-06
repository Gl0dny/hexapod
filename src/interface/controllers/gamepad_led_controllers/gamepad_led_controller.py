#!/usr/bin/env python3
"""
Abstract gamepad LED controller implementation.

This module provides LED control functionality for various gamepad controllers
using inheritance to support different controller types.
"""

import logging
import time
import threading
import math
from typing import Optional, Tuple, Dict, Any
from enum import Enum
from abc import ABC, abstractmethod
from utils import rename_thread

logger = logging.getLogger("gamepad_logger")

class GamepadLEDColor(Enum):
    """Enumeration of LED colors for the gamepad."""
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 215, 0)
    CYAN = (0, 255, 255)
    MAGENTA = (255, 0, 255)
    WHITE = (255, 255, 255)
    ORANGE = (255, 50, 0)
    PURPLE = (128, 0, 128)
    PINK = (255, 51, 183)
    LIME = (75, 180, 0) 
    TEAL = (0, 128, 128)
    INDIGO = (75, 0, 130)
    BLACK = (0, 0, 0)  # Off
    
    @property
    def rgb(self) -> Tuple[int, int, int]:
        """Get the RGB values for this color."""
        return self.value

class BaseGamepadLEDController(ABC):
    """Abstract base class for gamepad LED controllers."""
    
    def __init__(self):
        """Initialize the base LED controller."""
        self.is_connected = False
        self.current_color = GamepadLEDColor.BLUE
        self.brightness = 1.0  # 0.0 to 1.0
        self.animation_thread: Optional[threading.Thread] = None
        self.animation_running = False
    
    @abstractmethod
    def _connect_controller(self) -> bool:
        """Connect to the specific controller type. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _set_color_internal(self, r: int, g: int, b: int) -> bool:
        """Set the LED color on the specific controller. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _cleanup_internal(self):
        """Clean up controller-specific resources. Must be implemented by subclasses."""
        pass
    
    def set_color(self, color: GamepadLEDColor, brightness: Optional[float] = None) -> bool:
        """
        Set the LED color on the gamepad.
        
        Args:
            color: The color to set
            brightness: Brightness level (0.0 to 1.0, optional)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            return False
        
        try:
            self.current_color = color
            if brightness is not None:
                self.brightness = max(0.0, min(1.0, brightness))
            
            # Apply brightness to RGB values and clamp to valid range
            r, g, b = color.rgb
            r = max(0, min(255, int(r * self.brightness)))
            g = max(0, min(255, int(g * self.brightness)))
            b = max(0, min(255, int(b * self.brightness)))
            
            success = self._set_color_internal(r, g, b)

            return success
            
        except Exception as e:
            print(f"Failed to set LED color: {e}")
            return False
    
    def set_color_rgb(self, rgb: Tuple[int, int, int], brightness: Optional[float] = None) -> bool:
        """
        Set the LED color using RGB values.
        
        Args:
            rgb: RGB tuple (r, g, b) with values 0-255
            brightness: Brightness level (0.0 to 1.0, optional)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            return False
        
        try:
            if brightness is not None:
                self.brightness = max(0.0, min(1.0, brightness))
            
            # Apply brightness to RGB values and clamp to valid range
            r, g, b = rgb
            r = max(0, min(255, int(r * self.brightness)))
            g = max(0, min(255, int(g * self.brightness)))
            b = max(0, min(255, int(b * self.brightness)))
            
            success = self._set_color_internal(r, g, b)

            return success
            
        except Exception as e:
            print(f"Failed to set LED color: {e}")
            return False
    
    def set_brightness(self, brightness: float) -> bool:
        """
        Set the LED brightness.
        
        Args:
            brightness: Brightness level (0.0 to 1.0)
            
        Returns:
            True if successful, False otherwise
        """
        self.brightness = max(0.0, min(1.0, brightness))
        return self.set_color(self.current_color)
    
    def turn_off(self) -> bool:
        """
        Turn off the LED.
        
        Returns:
            True if successful, False otherwise
        """
        self.stop_animation()
        return self.set_color(GamepadLEDColor.BLACK)
    
    def pulse(self, color: GamepadLEDColor, duration: float = 1.0, cycles: int = 1) -> bool:
        """
        Create a pulsing animation effect.
        
        Args:
            color: The color to pulse
            duration: Duration of each pulse cycle in seconds
            cycles: Number of pulse cycles (0 for infinite)
            
        Returns:
            True if animation started successfully, False otherwise
        """
        if not self.is_connected:
            return False
        
        if self.animation_running:
            self.stop_animation()
        
        self.animation_running = True
        self.animation_thread = threading.Thread(
            target=self._pulse_animation,
            args=(color, duration, cycles),
            daemon=True
        )
        self.animation_thread.start()
        return True
    
    def _pulse_animation(self, color: GamepadLEDColor, duration: float, cycles: int):
        """Internal method for pulse animation."""
        rename_thread(threading.current_thread(), "GamepadLEDPulseAnimation")
        cycle_count = 0
        
        while self.animation_running and (cycles == 0 or cycle_count < cycles):
            # Use sine wave for smooth pulse effect
            # One complete sine wave cycle for fade in and out
            steps = 60  # Much more steps for smoother animation
            
            for i in range(steps):
                if not self.animation_running:
                    break
                # Use sine wave: 0 to π for fade in, π to 2π for fade out
                angle = (i / steps) * 2 * math.pi
                # Convert sine wave to brightness (0 to 1)
                brightness = (1 + math.sin(angle)) / 2
                self.set_color(color, brightness)
                time.sleep(duration / steps)
            
            cycle_count += 1
    
    def pulse_two_colors(self, color1: GamepadLEDColor, color2: GamepadLEDColor, duration: float = 2.0, cycles: int = 0) -> bool:
        """
        Create a pulsing animation effect that transitions between two colors.
        
        Args:
            color1: The first color to pulse from
            color2: The second color to pulse to
            duration: Duration of each pulse cycle in seconds
            cycles: Number of pulse cycles (0 for infinite)
            
        Returns:
            True if animation started successfully, False otherwise
        """
        if not self.is_connected:
            return False
        
        if self.animation_running:
            self.stop_animation()
        
        self.animation_running = True
        self.animation_thread = threading.Thread(
            target=self._pulse_two_colors_animation,
            args=(color1, color2, duration, cycles),
            daemon=True
        )
        self.animation_thread.start()
        return True
    
    def _pulse_two_colors_animation(self, color1: GamepadLEDColor, color2: GamepadLEDColor, duration: float, cycles: int):
        """Internal method for two-color pulse animation."""
        rename_thread(threading.current_thread(), "GamepadLEDTwoColorPulseAnimation")
        cycle_count = 0
        
        # Get RGB values for both colors
        rgb1 = color1.rgb
        rgb2 = color2.rgb
        
        while self.animation_running and (cycles == 0 or cycle_count < cycles):
            # Use sine wave for smooth transition between colors
            # One complete sine wave cycle for color1 -> color2 -> color1
            steps = 60  # Much more steps for smoother animation
            
            for i in range(steps):
                if not self.animation_running:
                    break
                # Use sine wave: 0 to 2π for complete color transition cycle
                angle = (i / steps) * 2 * math.pi
                # Convert sine wave to interpolation factor (0 to 1)
                # This creates a smooth transition: color1 -> color2 -> color1
                factor = (1 + math.sin(angle)) / 2
                
                # Interpolate between the two colors
                interp_rgb = (
                    int(rgb1[0] + (rgb2[0] - rgb1[0]) * factor),
                    int(rgb1[1] + (rgb2[1] - rgb1[1]) * factor),
                    int(rgb1[2] + (rgb2[2] - rgb1[2]) * factor)
                )
                
                self.set_color_rgb(interp_rgb)
                time.sleep(duration / steps)
            
            cycle_count += 1
    
    def breathing_animation(self, color: GamepadLEDColor, duration: float = 2.0, cycles: int = 1) -> bool:
        """
        Create a breathing LED animation effect.
        
        Args:
            color: The color to breathe
            duration: Duration of each breath cycle in seconds
            cycles: Number of breath cycles (0 for infinite)
            
        Returns:
            True if animation started successfully, False otherwise
        """
        if not self.is_connected:
            return False
        
        if self.animation_running:
            self.stop_animation()
        
        self.animation_running = True
        self.animation_thread = threading.Thread(
            target=self._breathing_animation,
            args=(color, duration, cycles),
            daemon=True
        )
        self.animation_thread.start()
        return True
    
    def _breathing_animation(self, color: GamepadLEDColor, duration: float, cycles: int):
        """Internal method for breathing animation."""
        cycle_count = 0
        
        while self.animation_running and (cycles == 0 or cycle_count < cycles):
            # Use sine wave for smooth breathing effect
            # One complete sine wave cycle for breathe in and out
            steps = 80  # More steps for even smoother breathing
            
            for i in range(steps):
                if not self.animation_running:
                    break
                # Use sine wave: 0 to 2π for complete breath cycle
                angle = (i / steps) * 2 * math.pi
                # Convert sine wave to brightness (0 to 1)
                brightness = (1 + math.sin(angle)) / 2
                self.set_color(color, brightness)
                time.sleep(duration / steps)
            
            cycle_count += 1
    
    def stop_animation(self):
        """Stop any running animation."""
        self.animation_running = False
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(timeout=1.0)
    
    def get_available_colors(self) -> Dict[str, Tuple[int, int, int]]:
        """
        Get a dictionary of available colors.
        
        Returns:
            Dictionary mapping color names to RGB values
        """
        return {color.name: color.rgb for color in GamepadLEDColor}
    
    def is_available(self) -> bool:
        """
        Check if LED control is available.
        
        Returns:
            True if LED control is available, False otherwise
        """
        return self.is_connected
    
    def get_control_method(self) -> str:
        """
        Get the current control method being used.
        
        Returns:
            The control method name (implemented by subclasses)
        """
        return self.__class__.__name__
    
    def cleanup(self):
        """Clean up resources."""
        self.stop_animation()
        if self.is_connected:
            try:
                self.turn_off()
                self._cleanup_internal()
                print(f"{self.get_control_method()} LED controller cleaned up")
            except Exception as e:
                print(f"Error during LED controller cleanup: {e}")
            finally:
                self.is_connected = False