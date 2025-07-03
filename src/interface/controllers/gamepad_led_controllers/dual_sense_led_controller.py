#!/usr/bin/env python3
"""
DualSense LED controller implementation.

This module provides LED control functionality specifically for the PS5 DualSense controller.
"""

from .gamepad_led_controller import BaseGamepadLEDController

class DualSenseLEDController(BaseGamepadLEDController):
    """LED controller implementation for PS5 DualSense controller."""
    
    def __init__(self):
        """Initialize the DualSense LED controller."""
        super().__init__()
        
        try:
            from dualsense_controller import DualSenseController
            self.DualSenseController = DualSenseController
        except ImportError:
            print("dualsense-controller library not available. Install with: pip install dualsense-controller")
            self.DualSenseController = None
            return
        
        self.dualsense_controller = None
        self._connect_controller()
    
    def _connect_controller(self) -> bool:
        """Connect to the DualSense controller."""
        if self.DualSenseController is None:
            return False
        
        try:
            # Check if devices are available first
            device_infos = self.DualSenseController.enumerate_devices()
            if len(device_infos) < 1:
                print("No DualSense devices found. Make sure the controller is connected via USB or Bluetooth")
                return False
            
            self.dualsense_controller = self.DualSenseController(
                microphone_invert_led=True,
                microphone_initially_muted=True
            )
            
            # Activate without the microphone not properly initialized workaround warning
            self.dualsense_controller._core.init()
            self.dualsense_controller._properties.microphone.set_muted()
            self.dualsense_controller.wait_until_updated()
            
            self.is_connected = True
            print("Connected to DualSense controller for LED control")
            
            # Set initial color
            self.set_color(self.current_color)
            return True
            
        except Exception as e:
            print(f"Failed to connect to DualSense controller: {e}")
            print("Make sure the controller is connected via USB or Bluetooth")
            return False
    
    def _set_color_internal(self, r: int, g: int, b: int) -> bool:
        """Set the LED color on the DualSense controller."""
        try:
            self.dualsense_controller.lightbar.set_color(r, g, b)
            return True
        except Exception as e:
            print(f"Failed to set DualSense LED color: {e}")
            return False
    
    def _cleanup_internal(self):
        """Clean up DualSense controller resources."""
        if self.dualsense_controller:
            try:
                self.dualsense_controller.deactivate()
            except Exception as e:
                print(f"Error deactivating DualSense controller: {e}") 