#!/usr/bin/env python3
"""
Gamepad-based hexapod controller implementation.

This script provides a gamepad-based interface to test the hexapod's movement
capabilities using various game controllers.

Usage:
    python gamepad_hexapod_controller.py
"""
from __future__ import annotations
from typing import TYPE_CHECKING
import sys
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
from interface.input_mappings import InputMapping, DualSenseMapping
from interface.controllers.gamepad_led_controllers.gamepad_led_controller import BaseGamepadLEDController, GamepadLEDColor
from interface.controllers.gamepad_led_controllers.dual_sense_led_controller import DualSenseLEDController
from gait_generator import TripodGait

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("pygame not available. Install with: pip install pygame")

if TYPE_CHECKING:
    from typing import Optional

class GamepadHexapodController(ManualHexapodController):
    """Gamepad-based hexapod controller implementation."""
    
    def __init__(self, input_mapping: InputMapping, led_controller: Optional[BaseGamepadLEDController] = None):
        """
        Initialize the gamepad controller.
        
        Args:
            input_mapping: The input mapping for the gamepad
            led_controller: Optional LED controller for visual feedback
        """
        super().__init__()
        
        if not PYGAME_AVAILABLE:
            raise ImportError("pygame is required for gamepad support")
        
        self.input_mapping = input_mapping
        self.led_controller = led_controller
        
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
        
        # Deadzone for analog sticks (specific to gamepad hardware)
        self.deadzone = 0.1
        
        # Button states
        self.button_states = {}
        self.last_button_states = {}
        
        # Analog inputs
        self.analog_inputs = {}
        
        # LED state tracking
        self.current_led_state = None
        
        # Initialize LED controller if provided
        if self.led_controller is not None:
            if self.led_controller.is_available():
                # Set initial LED animation based on controller type
                print(self.gamepad.get_name().lower())
                if "dualsense" or "ps5" in self.gamepad.get_name().lower():
                    self.led_controller.pulse(GamepadLEDColor.BLUE, duration=2.0, cycles=0)  # Infinite blue pulse
                    print("Gamepad LED initialized with blue pulse animation")
                else:
                    self.led_controller.pulse(GamepadLEDColor.GREEN, duration=2.0, cycles=0)  # Infinite green pulse
                    print("Gamepad LED initialized with green pulse animation")
            else:
                print("Gamepad LED control not available")
                print("Make sure:")
                print("1. PS5 DualSense controller is connected")
                print("2. dualsense-controller library is installed")
        else:
            print("Gamepad LED control disabled")
        
        print(f"Gamepad '{self.gamepad.get_name()}' initialized successfully")
        print(f"Current mode: {self.current_mode}")
        print("Press OPTIONS button to toggle between body control and gait control modes")
    
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
        # Process events to clear pygame event queue, update gamepad state - prevents button stuck issue
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
            'create': self.gamepad.get_button(button_mappings['create']),
            'options': self.gamepad.get_button(button_mappings['options']),
            'l3': self.gamepad.get_button(button_mappings['l3']),
            'r3': self.gamepad.get_button(button_mappings['r3']),
            'ps5': self.gamepad.get_button(button_mappings['ps5']),
            'touchpad': self.gamepad.get_button(button_mappings['touchpad']),
            'dpad_up': self.gamepad.get_button(button_mappings['dpad_up']),
            'dpad_down': self.gamepad.get_button(button_mappings['dpad_down']),
            'dpad_left': self.gamepad.get_button(button_mappings['dpad_left']),
            'dpad_right': self.gamepad.get_button(button_mappings['dpad_right'])
        }
        
        return buttons
    
    def _check_button_press(self, button_name):
        """Check if a button was just pressed (not held)."""
        current = self.button_states.get(button_name, False)
        last = self.last_button_states.get(button_name, False)
        return current and not last
    
    def _toggle_mode(self):
        """Toggle between body control and gait control modes using base class set_mode and gait methods."""
        if self.current_mode == self.BODY_CONTROL_MODE:
            # Switch to gait control mode
            self.set_mode(self.GAIT_CONTROL_MODE)
            print(f"\n=== SWITCHED TO GAIT CONTROL MODE ===")
            print("Left Stick: Movement direction")
            print("Right Stick X: Rotation (clockwise/counterclockwise)")
            print("The hexapod will walk using its gait generator")
            
            # Start gait control with separate parameters for translation and rotation
            translation_params = {
                'step_radius': 22.0,
                'leg_lift_distance': 20.0,
                'dwell_time': 0.1
            }
            rotation_params = {
                'step_radius': 30.0,
                'leg_lift_distance': 10.0,
                'dwell_time': 0.1
            }
            self.start_gait_control(
                gait_type=TripodGait,
                translation_params=translation_params,
                rotation_params=rotation_params
            )
            
            # Update LED to indicate gait mode
            if self.led_controller and self.led_controller.is_available():
                self.led_controller.stop_animation()
                self.led_controller.pulse(GamepadLEDColor.INDIGO, duration=1.5, cycles=0)
                self.current_led_state = 'gait_mode'
            
        else:
            # Switch to body control mode
            self.set_mode(self.BODY_CONTROL_MODE)
            print(f"\n=== SWITCHED TO BODY CONTROL MODE ===")
            print("Left Stick: Body translation")
            print("Right Stick: Body rotation")
            print("The hexapod will move its body using inverse kinematics")
            self.stop_gait_control()
            # Update LED to indicate body control mode
            if self.led_controller and self.led_controller.is_available():
                self.led_controller.stop_animation()
                self.led_controller.pulse(GamepadLEDColor.BLUE, duration=2.0, cycles=0)
                self.current_led_state = 'body_mode'
    
    def _update_led_state(self, movement_magnitude, idle_color, movement_color):
        """
        Update LED state based on movement magnitude.
        
        Args:
            movement_magnitude (float): Magnitude of movement input
            idle_color (GamepadLEDColor): Color for idle state
            movement_color (GamepadLEDColor): Color for movement state
        """
        if not (self.led_controller and self.led_controller.is_available()):
            return
        
        # Determine current LED state
        if movement_magnitude > 0.01:  # Threshold for movement detection
            new_led_state = 'movement'
        else:
            new_led_state = 'idle'
        
        # Only change LED if state has changed
        if new_led_state != self.current_led_state:
            # Stop any existing animation first
            self.led_controller.stop_animation()
            
            if new_led_state == 'movement':
                # Pulse animation for movement
                self.led_controller.pulse(movement_color, duration=0.8, cycles=0)
            else:  # idle
                # Pulse animation for idle state
                self.led_controller.pulse(idle_color, duration=2.0, cycles=0)
            
            self.current_led_state = new_led_state
    
    def get_inputs(self):
        """Get current input values from the gamepad."""
        # Get gamepad inputs
        self.analog_inputs = self._get_analog_inputs()
        self.button_states = self._get_button_states()
        
        # Handle mode toggle
        if self._check_button_press('options'):
            self._toggle_mode()
        
        # Process inputs based on current mode
        if self.current_mode == self.BODY_CONTROL_MODE:
            return self._get_body_control_inputs()
        elif self.current_mode == self.GAIT_CONTROL_MODE:
            return self._get_gait_control_inputs()
    
    def _get_body_control_inputs(self):
        """Process inputs for body control mode."""
        # Process analog inputs for movement (raw values, sensitivity applied in base class)
        tx = self.analog_inputs['left_x']
        ty = -self.analog_inputs['left_y']  # Invert Y axis
        roll = self.analog_inputs['right_x']
        pitch = -self.analog_inputs['right_y']  # Invert Y axis
        tz = (self.analog_inputs['r2'] - self.analog_inputs['l2'])
        yaw = 0.0
        
        # Process button inputs
        if self._check_button_press('triangle'):
            self.reset_position()
        elif self._check_button_press('square'):
            self.show_current_position()
        elif self._check_button_press('circle'):
            self.print_help()
        elif self._check_button_press('ps5'):
            self.running = False
        
        # Continuous yaw while holding L1/R1
        if self.button_states.get('l1', False):
            yaw = -1.0  # Raw value, sensitivity applied in base class
        if self.button_states.get('r1', False):
            yaw = 1.0   # Raw value, sensitivity applied in base class
        
        # Handle D-pad sensitivity adjustments
        sensitivity_deltas = {
            'translation_delta': 0.0,
            'rotation_delta': 0.0
        }
        
        # D-pad left/right: Adjust translation sensitivity (only on press)
        if self._check_button_press('dpad_left'):
            sensitivity_deltas['translation_delta'] = -self.SENSITIVITY_ADJUSTMENT_STEP
        
        if self._check_button_press('dpad_right'):
            sensitivity_deltas['translation_delta'] = self.SENSITIVITY_ADJUSTMENT_STEP
        
        # D-pad down/up: Adjust rotation sensitivity (only on press)
        if self._check_button_press('dpad_down'):
            sensitivity_deltas['rotation_delta'] = -self.SENSITIVITY_ADJUSTMENT_STEP
        
        if self._check_button_press('dpad_up'):
            sensitivity_deltas['rotation_delta'] = self.SENSITIVITY_ADJUSTMENT_STEP
        
        # Update LED based on movement activity
        movement_magnitude = abs(tx) + abs(ty) + abs(tz) + abs(roll) + abs(pitch) + abs(yaw)
        self._update_led_state(movement_magnitude, GamepadLEDColor.BLUE, GamepadLEDColor.LIME)
        
        # Update button states for next frame
        self.last_button_states = self.button_states.copy()
        
        return {
            'tx': tx,
            'ty': ty,
            'tz': tz,
            'roll': roll,
            'pitch': pitch,
            'yaw': yaw,
            'sensitivity_deltas': sensitivity_deltas
        }
    
    def _get_gait_control_inputs(self):
        """Process inputs for gait control mode - returns raw input values."""
        # Process analog inputs for gait control (raw values, sensitivity applied in base class)
        # Left stick controls movement direction
        direction_x = self.analog_inputs['left_x']
        direction_y = -self.analog_inputs['left_y']  # Invert Y axis
        
        # Right stick X controls rotation
        rotation = self.analog_inputs['right_x']
        
        # Process button inputs
        if self._check_button_press('triangle'):
            # Stop movement and return to home position
            self.reset_position()
        elif self._check_button_press('square'):
            self.show_current_position()
        elif self._check_button_press('circle'):
            self.print_help()
        elif self._check_button_press('ps5'):
            self.running = False
        
        # Handle D-pad sensitivity adjustments
        sensitivity_deltas = {
            'translation_delta': 0.0,
            'rotation_delta': 0.0
        }
        
        # D-pad left/right: Adjust gait direction sensitivity (only on press)
        if self._check_button_press('dpad_left'):
            sensitivity_deltas['translation_delta'] = -self.SENSITIVITY_ADJUSTMENT_STEP
        
        if self._check_button_press('dpad_right'):
            sensitivity_deltas['translation_delta'] = self.SENSITIVITY_ADJUSTMENT_STEP
        
        # D-pad down/up: Adjust gait rotation sensitivity (only on press)
        if self._check_button_press('dpad_down'):
            sensitivity_deltas['rotation_delta'] = -self.SENSITIVITY_ADJUSTMENT_STEP
        
        if self._check_button_press('dpad_up'):
            sensitivity_deltas['rotation_delta'] = self.SENSITIVITY_ADJUSTMENT_STEP
        
        # Update LED based on movement activity
        movement_magnitude = abs(direction_x) + abs(direction_y) + abs(rotation)
        self._update_led_state(movement_magnitude, GamepadLEDColor.INDIGO, GamepadLEDColor.LIME)
        
        # Update button states for next frame
        self.last_button_states = self.button_states.copy()
        
        # Return raw input values for base class to process
        return {
            'direction_x': direction_x,
            'direction_y': direction_y,
            'rotation': rotation,
            'sensitivity_deltas': sensitivity_deltas
        }

    def print_help(self):
        """Print the help menu."""
        controller_type = type(self.input_mapping).__name__.replace('Mappings', '').replace('_', ' ')
        print("\n" + "="*60)
        print(f"{controller_type.upper()} GAMEPAD HEXAPOD CONTROLLER")
        print("="*60)
        print("MODE CONTROLS:")
        print("  Options Button - Toggle between Body Control and Gait Control modes")
        print()
        print("BODY CONTROL MODE (Inverse Kinematics):")
        print("  Left Stick X    - Left/Right translation")
        print("  Left Stick Y    - Forward/Backward translation")
        print("  L2/R2 Triggers  - Down/Up translation")
        print("  Right Stick X   - Roll rotation (left/right)")
        print("  Right Stick Y   - Pitch rotation (forward/backward)")
        print("  L1/R1           - Yaw left/right")
        print()
        print("GAIT CONTROL MODE (Walking):")
        print("  Left Stick      - Movement direction (forward/backward/left/right/diagonal directions)")
        print("  Right Stick X   - Rotation (clockwise/counterclockwise)")
        print("  The hexapod will walk using its gait generator")
        print("  Different gait parameters are used for translation vs rotation movements")
        print()
        print("COMMON BUTTON CONTROLS:")
        print("  Triangle        - Reset to start position")
        print("  Square          - Show current position")
        print("  Circle          - Show this help menu")
        print("  PS5             - Exit program")
        print()
        print("SENSITIVITY CONTROLS (D-Pad):")
        print("  D-Pad Left/Right - Decrease/Increase translation/gait direction sensitivity")
        print("  D-Pad Down/Up   - Decrease/Increase rotation/gait rotation sensitivity")
        print("  (Sensitivity type depends on current mode)")
        print()
        print("LED INDICATORS:")
        print("  Blue Pulse      - Body control mode (idle)")
        print("  Purple Pulse    - Gait control mode (idle)")
        print("  Lime Pulse      - Movement detected (both modes)")
        print("="*60)
    
    def cleanup_controller(self):
        """Clean up gamepad-specific resources."""
        # Cleanup LED controller
        if hasattr(self, 'led_controller') and self.led_controller:
            try:
                self.led_controller.turn_off()
                self.led_controller.cleanup()
                print("Gamepad LED turned off")
            except Exception as e:
                print(f"Error during LED cleanup: {e}")
        
        # Cleanup pygame
        if PYGAME_AVAILABLE:
            pygame.quit()

def main():
    """Main function to run the hexapod movement controller."""
    controller = None
    try:
        # Choose your input interface mapping here:
        # For PS5 DualSense controller:
        input_mapping = DualSenseMapping()
        # For other interfaces, create a new mapping class that inherits from InputMapping

        # Optional: Create LED controller for visual feedback
        led_controller = DualSenseLEDController()  # Create DualSense LED controller
        
        # controller = GamepadHexapodController(input_mapping)  # No LED controller
        controller = GamepadHexapodController(input_mapping, led_controller)  # With LED controller
        controller.run()
    except Exception as e:
        print(f"Movement controller execution failed: {e}")
        if controller:
            controller.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main() 