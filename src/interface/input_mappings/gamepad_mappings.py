#!/usr/bin/env python3
"""
Gamepad input mappings for hexapod controllers.

This module provides input mapping implementations for various gamepad controllers.
"""

from .base_input_mapping import InputMapping

class PS5DualSenseMappings(InputMapping):
    """Mappings for PS5 DualSense Controller."""
    
    # Axis mappings
    AXIS_LEFT_X = 0      # Left stick X: -1 (left) to +1 (right)
    AXIS_LEFT_Y = 1      # Left stick Y: -1 (up) to +1 (down) - INVERTED
    AXIS_RIGHT_X = 2     # Right stick X: -1 (left) to +1 (right)
    AXIS_L2 = 3          # L2 trigger: -1 (not pressed) to +1 (fully pressed)
    AXIS_R2 = 4          # R2 trigger: -1 (not pressed) to +1 (fully pressed)
    AXIS_RIGHT_Y = 5     # Right stick Y: -1 (up) to +1 (down) - INVERTED
    
    # Button mappings
    BUTTON_SQUARE = 0    # Square
    BUTTON_X = 1         # X (Cross)
    BUTTON_CIRCLE = 2    # Circle
    BUTTON_TRIANGLE = 3  # Triangle
    BUTTON_L1 = 4        # L1
    BUTTON_R1 = 5        # R1
    BUTTON_L2_DIGITAL = 6  # L2 (digital)
    BUTTON_R2_DIGITAL = 7  # R2 (digital)
    BUTTON_CREATE = 8    # Create/Broadcast
    BUTTON_OPTIONS = 9   # Options
    BUTTON_L3 = 10       # L3
    BUTTON_R3 = 11       # R3
    BUTTON_PS5 = 12      # PS5 (avoid in robot control)
    BUTTON_TOUCHPAD = 13 # Touchpad
    
    def get_axis_mappings(self):
        """Return a dictionary of axis mappings."""
        return {
            'left_x': self.AXIS_LEFT_X,
            'left_y': self.AXIS_LEFT_Y,
            'right_x': self.AXIS_RIGHT_X,
            'right_y': self.AXIS_RIGHT_Y,
            'l2': self.AXIS_L2,
            'r2': self.AXIS_R2
        }
    
    def get_button_mappings(self):
        """Return a dictionary of button mappings."""
        return {
            'square': self.BUTTON_SQUARE,
            'x': self.BUTTON_X,
            'circle': self.BUTTON_CIRCLE,
            'triangle': self.BUTTON_TRIANGLE,
            'l1': self.BUTTON_L1,
            'r1': self.BUTTON_R1,
            'l2_digital': self.BUTTON_L2_DIGITAL,
            'r2_digital': self.BUTTON_R2_DIGITAL,
            'create': self.BUTTON_CREATE,
            'options': self.BUTTON_OPTIONS,
            'l3': self.BUTTON_L3,
            'r3': self.BUTTON_R3,
            'ps5': self.BUTTON_PS5,
            'touchpad': self.BUTTON_TOUCHPAD
        }
    
    def get_interface_names(self):
        """Return a list of interface names this mapping supports."""
        return ['dualsense', 'ps5', 'playstation 5', 'wireless controller']
    
    def get_axis_name(self, axis_index):
        """Get the name of an axis by its index."""
        axis_names = {
            self.AXIS_LEFT_X: "Left X",
            self.AXIS_LEFT_Y: "Left Y (inverted)",
            self.AXIS_RIGHT_X: "Right X",
            self.AXIS_L2: "L2 (analog)",
            self.AXIS_R2: "R2 (analog)", 
            self.AXIS_RIGHT_Y: "Right Y (inverted)"
        }
        return axis_names.get(axis_index, f"Unknown Axis {axis_index}")
    
    def get_button_name(self, button_index):
        """Get the name of a button by its index."""
        button_names = {
            self.BUTTON_SQUARE: "Square",
            self.BUTTON_X: "X",
            self.BUTTON_CIRCLE: "Circle", 
            self.BUTTON_TRIANGLE: "Triangle",
            self.BUTTON_L1: "L1",
            self.BUTTON_R1: "R1",
            self.BUTTON_L2_DIGITAL: "L2 (digital)",
            self.BUTTON_R2_DIGITAL: "R2 (digital)",
            self.BUTTON_CREATE: "Create",
            self.BUTTON_OPTIONS: "Options",
            self.BUTTON_L3: "L3",
            self.BUTTON_R3: "R3",
            self.BUTTON_PS5: "PS5",
            self.BUTTON_TOUCHPAD: "Touchpad"
        }
        return button_names.get(button_index, f"Unknown Button {button_index}")
    
    def print_mappings_info(self):
        """Print information about the controller mappings."""
        print("\nPS5 DualSense Controller Mappings:")
        print("=" * 40)
        print("Axes:")
        for axis_id, name in {
            self.AXIS_LEFT_X: "Left X",
            self.AXIS_LEFT_Y: "Left Y (inverted)",
            self.AXIS_RIGHT_X: "Right X",
            self.AXIS_L2: "L2 (analog)",
            self.AXIS_R2: "R2 (analog)", 
            self.AXIS_RIGHT_Y: "Right Y (inverted)"
        }.items():
            print(f"  [{axis_id}] {name}")
        print("\nButtons:")
        for button_id, name in {
            self.BUTTON_SQUARE: "Square",
            self.BUTTON_X: "X",
            self.BUTTON_CIRCLE: "Circle", 
            self.BUTTON_TRIANGLE: "Triangle",
            self.BUTTON_L1: "L1",
            self.BUTTON_R1: "R1",
            self.BUTTON_L2_DIGITAL: "L2 (digital)",
            self.BUTTON_R2_DIGITAL: "R2 (digital)",
            self.BUTTON_CREATE: "Create",
            self.BUTTON_OPTIONS: "Options",
            self.BUTTON_L3: "L3",
            self.BUTTON_R3: "R3",
            self.BUTTON_PS5: "PS5",
            self.BUTTON_TOUCHPAD: "Touchpad"
        }.items():
            print(f"  [{button_id}] {name}")
        print("=" * 40) 