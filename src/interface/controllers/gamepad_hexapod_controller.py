#!/usr/bin/env python3
"""
Gamepad-based hexapod controller implementation.

This script provides a gamepad-based interface to test the hexapod's movement
capabilities using various game controllers.

Usage:
    python gamepad_hexapod_controller.py
"""

import sys
import time
import os
import warnings
from pathlib import Path

# Silence pygame warnings and welcome message BEFORE importing pygame
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

warnings.filterwarnings("ignore", category=RuntimeWarning, module="pygame")
warnings.filterwarnings("ignore", category=UserWarning, module="pygame")
warnings.filterwarnings("ignore", message=".*pkg_resources.*")
warnings.filterwarnings("ignore", message=".*neon capable.*")
warnings.filterwarnings("ignore", message=".*pygame.*")

# Add the src directory to the path so we can import our modules
SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = (SCRIPT_DIR.parent.parent).resolve()
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Import base classes and mappings
from interface.controllers.base_manual_controller import ManualHexapodController
from interface.input_mappings import InputMapping, PS5DualSenseMappings

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("pygame not available. Install with: pip install pygame")

class GamepadHexapodController(ManualHexapodController):
    """Gamepad-based hexapod controller implementation."""
    
    def __init__(self, input_mapping: InputMapping):
        """Initialize the gamepad controller."""
        super().__init__()
        
        if not PYGAME_AVAILABLE:
            raise ImportError("pygame is required for gamepad support")
        
        self.input_mapping = input_mapping
        
        # Set display environment for headless systems
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
        
        # Initialize pygame for gamepad support
        pygame.init()
        pygame.joystick.init()
        
        # Find and initialize gamepad
        self.gamepad = self._find_gamepad()
        if not self.gamepad:
            raise RuntimeError(f"Gamepad not found. This script only supports: {', '.join(input_mapping.get_interface_names())}")
        
        # Sensitivity and deadzone
        self.translation_sensitivity = 0.3
        self.rotation_sensitivity = 0.5
        self.deadzone = 0.1
        
        # Button states
        self.button_states = {}
        self.last_button_states = {}
        
        print(f"Gamepad '{self.gamepad.get_name()}' initialized successfully")
    
    def _find_gamepad(self):
        """Find and initialize a gamepad that matches the mapping."""
        joystick_count = pygame.joystick.get_count()
        print(f"Found {joystick_count} gamepad(s)")
        
        for i in range(joystick_count):
            joystick = pygame.joystick.Joystick(i)
            name = joystick.get_name().lower()
            print(f"Gamepad {i}: {name}")
            
            # Check if this gamepad matches our mapping
            if any(keyword in name for keyword in self.input_mapping.get_interface_names()):
                print(f"Compatible gamepad found: {name}")
                joystick.init()
                return joystick
        
        # If no compatible gamepad found, print proper message and return None
        if joystick_count > 0:
            print("\n" + "="*60)
            print(f"ERROR: Only {type(self.input_mapping).__name__} gamepads are supported")
            print("="*60)
            print(f"This script is specifically designed for {type(self.input_mapping).__name__} gamepads.")
            print("Other gamepads are not implemented.")
            print(f"\nSupported gamepads: {', '.join(self.input_mapping.get_interface_names())}")
            print("\nPlease connect a compatible gamepad and try again.")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("ERROR: No gamepads found")
            print("="*60)
            print(f"Please connect a {type(self.input_mapping).__name__} gamepad and try again.")
            print("="*60)
        
        return None
    
    def _apply_deadzone(self, value):
        """Apply deadzone to analog stick values."""
        if abs(value) < self.deadzone:
            return 0.0
        # Normalize the value after deadzone
        sign = 1 if value > 0 else -1
        normalized = (abs(value) - self.deadzone) / (1.0 - self.deadzone)
        return sign * normalized
    
    def _get_analog_inputs(self):
        """Get analog stick inputs with deadzone applied."""
        # Process events to update gamepad state
        for event in pygame.event.get():
            pass
        
        # Get axes using input mapping
        axis_mappings = self.input_mapping.get_axis_mappings()
        left_x = self._apply_deadzone(self.gamepad.get_axis(axis_mappings['left_x']))
        left_y = self._apply_deadzone(self.gamepad.get_axis(axis_mappings['left_y']))
        right_x = self._apply_deadzone(self.gamepad.get_axis(axis_mappings['right_x']))
        l2 = self._apply_deadzone(self.gamepad.get_axis(axis_mappings['l2']))
        r2 = self._apply_deadzone(self.gamepad.get_axis(axis_mappings['r2']))
        right_y = self._apply_deadzone(self.gamepad.get_axis(axis_mappings['right_y']))
        
        return {
            'left_x': left_x,
            'left_y': left_y,
            'right_x': right_x,
            'right_y': right_y,
            'l2': l2,
            'r2': r2
        }
    
    def _get_button_states(self):
        """Get current button states."""
        # Process events to update gamepad state
        for event in pygame.event.get():
            pass
        
        # Get buttons using input mapping
        button_mappings = self.input_mapping.get_button_mappings()
        buttons = {
            'square': self.gamepad.get_button(button_mappings['square']),
            'x': self.gamepad.get_button(button_mappings['x']),
            'circle': self.gamepad.get_button(button_mappings['circle']),
            'triangle': self.gamepad.get_button(button_mappings['triangle']),
            'l1': self.gamepad.get_button(button_mappings['l1']),
            'r1': self.gamepad.get_button(button_mappings['r1']),
            'l2_digital': self.gamepad.get_button(button_mappings['l2_digital']),
            'r2_digital': self.gamepad.get_button(button_mappings['r2_digital']),
            'create': self.gamepad.get_button(button_mappings['create']),
            'options': self.gamepad.get_button(button_mappings['options']),
            'l3': self.gamepad.get_button(button_mappings['l3']),
            'r3': self.gamepad.get_button(button_mappings['r3']),
            'ps5': self.gamepad.get_button(button_mappings['ps5']),
            'touchpad': self.gamepad.get_button(button_mappings['touchpad'])
        }
        
        return buttons
    
    def _check_button_press(self, button_name):
        """Check if a button was just pressed (not held)."""
        current = self.button_states.get(button_name, False)
        last = self.last_button_states.get(button_name, False)
        return current and not last
    
    def get_inputs(self):
        """Get current input values from the gamepad."""
        # Get gamepad inputs
        analog_inputs = self._get_analog_inputs()
        self.button_states = self._get_button_states()
        
        # Process analog inputs for movement
        tx = analog_inputs['left_x'] * self.translation_sensitivity * self.TRANSLATION_STEP
        ty = -analog_inputs['left_y'] * self.translation_sensitivity * self.TRANSLATION_STEP
        roll = analog_inputs['right_x'] * self.rotation_sensitivity * self.ROLL_STEP
        pitch = -analog_inputs['right_y'] * self.rotation_sensitivity * self.ROTATION_STEP
        tz = (analog_inputs['r2'] - analog_inputs['l2']) * self.translation_sensitivity * self.Z_STEP
        yaw = 0.0
        
        # Process button inputs
        if self._check_button_press('triangle'):
            self.reset_to_start()
        elif self._check_button_press('square'):
            self.show_current_position()
        elif self._check_button_press('circle'):
            self.print_help()
        elif self._check_button_press('ps5'):
            self.running = False
        
        # Continuous yaw while holding L1/R1
        if self.button_states.get('l1', False):
            yaw = -self.YAW_STEP
        if self.button_states.get('r1', False):
            yaw = self.YAW_STEP
        
        # Update button states for next frame
        self.last_button_states = self.button_states.copy()
        
        return {
            'tx': tx,
            'ty': ty,
            'tz': tz,
            'roll': roll,
            'pitch': pitch,
            'yaw': yaw
        }
    
    def print_help(self):
        """Print the help menu."""
        controller_type = type(self.input_mapping).__name__.replace('Mappings', '').replace('_', ' ')
        print("\n" + "="*60)
        print(f"{controller_type.upper()} GAMEPAD HEXAPOD MOVEMENT CONTROLLER")
        print("="*60)
        print("Analog Stick Controls:")
        print("  Left Stick X    - Left/Right translation")
        print("  Left Stick Y    - Forward/Backward translation (inverted)")
        print("  Right Stick X   - Roll rotation (left/right)")
        print("  Right Stick Y   - Pitch rotation (forward/backward) (inverted)")
        print("  L2/R2 Triggers  - Down/Up translation (analog)")
        print()
        print("Button Controls:")
        print("  Triangle        - Reset to start position")
        print("  Square          - Show current position")
        print("  Circle          - Show this help menu")
        print("  L1/R1           - Yaw left/right")
        print("  PS5             - Exit program")
        print()
        print("Special Features:")
        print("  - Analog sticks provide continuous movement")
        print("  - Movement speed varies with stick deflection")
        print("  - Deadzone prevents drift from stick center")
        print("  - Y-axes are inverted (up=-1, down=+1)")
        print("  - Triggers provide analog Z-axis control")
        print("="*60)
    
    def cleanup(self):
        """Clean up resources."""
        try:
            self.reset_to_start()
            self.hexapod.deactivate_all_servos()
            print("Hexapod servos deactivated")
        except Exception as e:
            print(f"Error during cleanup: {e}")
        
        # Cleanup pygame
        if PYGAME_AVAILABLE:
            pygame.quit()

def main():
    """Main function to run the hexapod movement controller."""
    controller = None
    try:
        # Choose your input interface mapping here:
        # For PS5 DualSense controller:
        input_mapping = PS5DualSenseMappings()
        
        # For other interfaces, create a new mapping class that inherits from InputMapping
        
        controller = GamepadHexapodController(input_mapping)
        controller.run()
    except Exception as e:
        print(f"Movement controller execution failed: {e}")
        if controller:
            controller.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main() 