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
    """Gamepad-based hexapod controller implementation with dual modes."""
    
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
        
        # Mode management
        self.current_mode = "body_control"  # "body_control" or "gait_steering"
        self.gait = None
        
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
        print("Press OPTIONS button to toggle between body control and gait steering modes")
    
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
        """Toggle between body control and gait steering modes."""
        if self.current_mode == "body_control":
            # Switch to gait steering mode
            self.current_mode = "gait_steering"
            print(f"\n=== SWITCHED TO GAIT STEERING MODE ===")
            print("Left Stick: Movement direction")
            print("Right Stick X: Rotation (clockwise/counterclockwise)")
            print("The hexapod will walk using its gait generator")
            
            # Initialize gait if not already done
            if self.gait is None:
                self.gait = TripodGait(
                    self.hexapod,
                    step_radius=22.0,
                    leg_lift_distance=20.0,
                    dwell_time=0.1
                )
                print("Gait initialized")
            
            # Start gait generation
            self.hexapod.gait_generator.start(self.gait)
            print("Gait generation started")
            
            # Update LED to indicate gait mode
            if self.led_controller and self.led_controller.is_available():
                self.led_controller.stop_animation()
                self.led_controller.pulse(GamepadLEDColor.INDIGO, duration=1.5, cycles=0)
                self.current_led_state = 'gait_mode'
            
        else:
            # Switch to body control mode
            self.current_mode = "body_control"
            print(f"\n=== SWITCHED TO BODY CONTROL MODE ===")
            print("Left Stick: Body translation")
            print("Right Stick: Body rotation")
            print("The hexapod will move its body using inverse kinematics")
            
            # Stop gait generation
            if self.hexapod.gait_generator.is_running:
                self.hexapod.gait_generator.stop()
                print("Gait generation stopped")
            
            # Update LED to indicate body control mode
            if self.led_controller and self.led_controller.is_available():
                self.led_controller.stop_animation()
                self.led_controller.pulse(GamepadLEDColor.BLUE, duration=2.0, cycles=0)
                self.current_led_state = 'body_mode'
    
    def get_inputs(self):
        """Get current input values from the gamepad."""
        # Get gamepad inputs
        analog_inputs = self._get_analog_inputs()
        self.button_states = self._get_button_states()
        
        # Handle mode toggle
        if self._check_button_press('options'):
            self._toggle_mode()
        
        # Process inputs based on current mode
        if self.current_mode == "body_control":
            return self._get_body_control_inputs(analog_inputs)
        else:  # gait_steering
            return self._get_gait_steering_inputs(analog_inputs)
    
    def _get_body_control_inputs(self, analog_inputs):
        """Process inputs for body control mode."""
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
        
        # Update LED based on movement activity
        if self.led_controller and self.led_controller.is_available():
            # Check if there's any movement
            movement_magnitude = abs(tx) + abs(ty) + abs(tz) + abs(roll) + abs(pitch) + abs(yaw)
            
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
                    self.led_controller.pulse(GamepadLEDColor.LIME, duration=0.8, cycles=0)  # Infinite pulse
                else:  # idle
                    # Pulse animation for idle state
                    self.led_controller.pulse(GamepadLEDColor.BLUE, duration=2.0, cycles=0)  # Infinite breathing
                
                self.current_led_state = new_led_state
        
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
    
    def _get_gait_steering_inputs(self, analog_inputs):
        """Process inputs for gait steering mode."""
        # Process analog inputs for gait steering
        # Left stick controls movement direction
        direction_x = analog_inputs['left_x']
        direction_y = -analog_inputs['left_y']  # Invert Y axis
        
        # Right stick X controls rotation
        rotation = analog_inputs['right_x'] * self.rotation_sensitivity
        
        # Process button inputs
        if self._check_button_press('triangle'):
            # Stop movement and return to home position
            if self.gait:
                self.gait.set_direction((0.0, 0.0), rotation=0.0)
            self.reset_to_start()
        elif self._check_button_press('square'):
            self.show_current_position()
        elif self._check_button_press('circle'):
            self.print_help()
        elif self._check_button_press('ps5'):
            self.running = False
        
        # Update gait direction and rotation
        if self.gait:
            # Convert analog inputs to direction vector
            if abs(direction_x) > 0.01 or abs(direction_y) > 0.01:
                # Normalize direction vector
                magnitude = (direction_x**2 + direction_y**2)**0.5
                if magnitude > 0:
                    direction_x /= magnitude
                    direction_y /= magnitude
                    # Scale by sensitivity
                    direction_x *= self.translation_sensitivity
                    direction_y *= self.translation_sensitivity
                
                self.gait.set_direction((direction_x, direction_y), rotation=rotation)
            else:
                # No movement input, just rotation
                self.gait.set_direction((0.0, 0.0), rotation=rotation)
        
        # Update LED based on movement activity
        if self.led_controller and self.led_controller.is_available():
            # Check if there's any movement
            movement_magnitude = abs(direction_x) + abs(direction_y) + abs(rotation)
            
            # Determine current LED state
            if movement_magnitude > 0.01:  # Threshold for movement detection
                new_led_state = 'gait_movement'
            else:
                new_led_state = 'gait_idle'
            
            # Only change LED if state has changed
            if new_led_state != self.current_led_state:
                # Stop any existing animation first
                self.led_controller.stop_animation()
                
                if new_led_state == 'gait_movement':
                    # Pulse animation for gait movement
                    self.led_controller.pulse(GamepadLEDColor.LIME, duration=0.8, cycles=0)  # Infinite pulse
                else:  # gait_idle
                    # Pulse animation for gait idle state
                    self.led_controller.pulse(GamepadLEDColor.INDIGO, duration=1.5, cycles=0)  # Infinite breathing
                
                self.current_led_state = new_led_state
        
        # Update button states for next frame
        self.last_button_states = self.button_states.copy()
        
        # Return zero movement for body control (gait handles movement)
        return {
            'tx': 0.0,
            'ty': 0.0,
            'tz': 0.0,
            'roll': 0.0,
            'pitch': 0.0,
            'yaw': 0.0
        }
    
    def print_help(self):
        """Print the help menu."""
        controller_type = type(self.input_mapping).__name__.replace('Mappings', '').replace('_', ' ')
        print("\n" + "="*60)
        print(f"{controller_type.upper()} GAMEPAD HEXAPOD CONTROLLER")
        print("="*60)
        print("MODE CONTROLS:")
        print("  Options Button - Toggle between Body Control and Gait Steering modes")
        print()
        print("BODY CONTROL MODE (Inverse Kinematics):")
        print("  Left Stick X    - Left/Right translation")
        print("  Left Stick Y    - Forward/Backward translation (inverted)")
        print("  Right Stick X   - Roll rotation (left/right)")
        print("  Right Stick Y   - Pitch rotation (forward/backward) (inverted)")
        print("  L2/R2 Triggers  - Down/Up translation (analog)")
        print("  L1/R1           - Yaw left/right")
        print()
        print("GAIT STEERING MODE (Walking):")
        print("  Left Stick      - Movement direction (forward/backward/left/right)")
        print("  Right Stick X   - Rotation (clockwise/counterclockwise)")
        print("  The hexapod will walk using its gait generator")
        print()
        print("COMMON BUTTON CONTROLS:")
        print("  Triangle        - Reset to start position")
        print("  Square          - Show current position")
        print("  Circle          - Show this help menu")
        print("  PS5             - Exit program")
        print()
        print("LED INDICATORS:")
        print("  Blue Pulse      - Body control mode (idle)")
        print("  Purple Pulse    - Gait steering mode (idle)")
        print("  Lime Pulse      - Movement detected (both modes)")
        print("="*60)
    
    def cleanup(self):
        """Clean up resources."""
        try:
            # Stop gait generation if running
            if hasattr(self, 'hexapod') and hasattr(self.hexapod, 'gait_generator'):
                if self.hexapod.gait_generator.is_running:
                    self.hexapod.gait_generator.stop()
                    print("Gait generation stopped")
            
            self.reset_to_start()
            self.hexapod.deactivate_all_servos()
            print("Hexapod servos deactivated")
        except Exception as e:
            print(f"Error during cleanup: {e}")
        
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