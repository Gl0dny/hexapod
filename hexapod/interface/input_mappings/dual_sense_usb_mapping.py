"""
DualSense USB input mapping implementation.

This module provides input mapping for PS5 DualSense Controller in USB mode.
"""

from typing import TYPE_CHECKING

from hexapod.interface.input_mappings import InputMapping

if TYPE_CHECKING:
    from typing import Dict, List, Any


class DualSenseUSBMapping(InputMapping):
    """Mappings for PS5 DualSense Controller in USB mode."""

    # Axis mappings
    AXIS_LEFT_X = 0  # Left stick X: -1 (left) to +1 (right)
    AXIS_LEFT_Y = 1  # Left stick Y: -1 (up) to +1 (down) - INVERTED
    AXIS_RIGHT_X = 2  # Right stick X: -1 (left) to +1 (right)
    AXIS_RIGHT_Y = 3  # Right stick Y: -1 (up) to +1 (down) - INVERTED
    AXIS_L2 = 4  # L2 trigger: -1 (not pressed) to +1 (fully pressed)
    AXIS_R2 = 5  # R2 trigger: -1 (not pressed) to +1 (fully pressed)

    # Button mappings
    BUTTON_X = 0  # X (Cross)
    BUTTON_CIRCLE = 1  # Circle
    BUTTON_SQUARE = 2  # Square
    BUTTON_TRIANGLE = 3  # Triangle
    BUTTON_CREATE = 4  # Create/Broadcast
    BUTTON_PS5 = 5  # PS5 (avoid in robot control)
    BUTTON_OPTIONS = 6  # Options
    BUTTON_L3 = 7  # L3
    BUTTON_R3 = 8  # R3
    BUTTON_L1 = 9  # L1
    BUTTON_R1 = 10  # R1
    BUTTON_MUTE = 15  # Mute
    BUTTON_TOUCHPAD = 16  # Touchpad

    # D-pad buttons (detected as buttons, not hat)
    BUTTON_DPAD_UP = 11  # D-pad Up
    BUTTON_DPAD_DOWN = 12  # D-pad Down
    BUTTON_DPAD_LEFT = 13  # D-pad Left
    BUTTON_DPAD_RIGHT = 14  # D-pad Right

    def get_axis_mappings(self) -> Dict[str, int]:
        """Return a dictionary of axis mappings."""
        return {
            "left_x": self.AXIS_LEFT_X,
            "left_y": self.AXIS_LEFT_Y,
            "right_x": self.AXIS_RIGHT_X,
            "right_y": self.AXIS_RIGHT_Y,
            "l2": self.AXIS_L2,
            "r2": self.AXIS_R2,
        }

    def get_button_mappings(self) -> Dict[str, int]:
        """Return a dictionary of button mappings."""
        return {
            "square": self.BUTTON_SQUARE,
            "x": self.BUTTON_X,
            "circle": self.BUTTON_CIRCLE,
            "triangle": self.BUTTON_TRIANGLE,
            "l1": self.BUTTON_L1,
            "r1": self.BUTTON_R1,
            "create": self.BUTTON_CREATE,
            "options": self.BUTTON_OPTIONS,
            "l3": self.BUTTON_L3,
            "r3": self.BUTTON_R3,
            "ps5": self.BUTTON_PS5,
            "touchpad": self.BUTTON_TOUCHPAD,
            "mute": self.BUTTON_MUTE,
            "dpad_up": self.BUTTON_DPAD_UP,
            "dpad_down": self.BUTTON_DPAD_DOWN,
            "dpad_left": self.BUTTON_DPAD_LEFT,
            "dpad_right": self.BUTTON_DPAD_RIGHT,
        }

    def get_hat_mappings(self) -> Dict[str, str]:
        """Return a dictionary of hat mappings."""
        return {
            "dpad": "buttons"  # USB uses buttons for D-pad, but still uses hat interface
        }

    def get_interface_names(self) -> List[str]:
        """Return a list of interface names this mapping supports."""
        return ["dualsense", "ps5", "playstation 5"]

    def get_axis_name(self, axis_index: int) -> str:
        """Get the name of an axis by its index."""
        axis_names = {
            self.AXIS_LEFT_X: "Left X",
            self.AXIS_LEFT_Y: "Left Y (inverted)",
            self.AXIS_RIGHT_X: "Right X",
            self.AXIS_L2: "L2 (analog)",
            self.AXIS_R2: "R2 (analog)",
            self.AXIS_RIGHT_Y: "Right Y (inverted)",
        }
        return axis_names.get(axis_index, f"Unknown Axis {axis_index}")

    def get_button_name(self, button_index: int) -> str:
        """Get the name of a button by its index."""
        button_names = {
            self.BUTTON_SQUARE: "Square",
            self.BUTTON_X: "X",
            self.BUTTON_CIRCLE: "Circle",
            self.BUTTON_TRIANGLE: "Triangle",
            self.BUTTON_L1: "L1",
            self.BUTTON_R1: "R1",
            self.BUTTON_CREATE: "Create",
            self.BUTTON_OPTIONS: "Options",
            self.BUTTON_L3: "L3",
            self.BUTTON_R3: "R3",
            self.BUTTON_PS5: "PS5",
            self.BUTTON_TOUCHPAD: "Touchpad",
            self.BUTTON_MUTE: "Mute",
            self.BUTTON_DPAD_UP: "D-pad Up",
            self.BUTTON_DPAD_DOWN: "D-pad Down",
            self.BUTTON_DPAD_LEFT: "D-pad Left",
            self.BUTTON_DPAD_RIGHT: "D-pad Right",
        }
        return button_names.get(button_index, f"Unknown Button {button_index}")

    def print_mappings_info(self) -> None:
        """Print information about the controller mappings."""
        print("\nPS5 DualSense Controller Mappings (USB):")
        print("=" * 40)
        print("Axes:")
        for axis_id, name in {
            self.AXIS_LEFT_X: "Left X",
            self.AXIS_LEFT_Y: "Left Y (inverted)",
            self.AXIS_RIGHT_X: "Right X",
            self.AXIS_L2: "L2 (analog)",
            self.AXIS_R2: "R2 (analog)",
            self.AXIS_RIGHT_Y: "Right Y (inverted)",
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
            self.BUTTON_CREATE: "Create",
            self.BUTTON_OPTIONS: "Options",
            self.BUTTON_L3: "L3",
            self.BUTTON_R3: "R3",
            self.BUTTON_PS5: "PS5",
            self.BUTTON_TOUCHPAD: "Touchpad",
            self.BUTTON_MUTE: "Mute",
            self.BUTTON_DPAD_UP: "D-pad Up",
            self.BUTTON_DPAD_DOWN: "D-pad Down",
            self.BUTTON_DPAD_LEFT: "D-pad Left",
            self.BUTTON_DPAD_RIGHT: "D-pad Right",
        }.items():
            print(f"  [{button_id}] {name}")
        print("\nHats:")
        print("  [dpad] D-pad (implemented as buttons)")
        print("=" * 40)
