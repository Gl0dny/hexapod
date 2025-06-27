#!/usr/bin/env python3
"""
Interactive test script for hexapod movement using PS5 controller.

This script provides an interactive interface to test the hexapod's movement
capabilities using a PS5 controller (or other gamepad).

Usage:
    python test_hexapod_move_body_ps5_controller.py
"""

import sys
import time
import os
import warnings
from pathlib import Path

# Silence pygame warnings BEFORE importing pygame
warnings.filterwarnings("ignore", category=RuntimeWarning, module="pygame")
warnings.filterwarnings("ignore", category=UserWarning, module="pygame")
warnings.filterwarnings("ignore", message=".*pkg_resources.*")
warnings.filterwarnings("ignore", message=".*neon capable.*")
warnings.filterwarnings("ignore", message=".*pygame.*")

# Add the src directory to the path so we can import our modules
SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = (SCRIPT_DIR.parent.parent / "src").resolve()
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from robot import Hexapod, PredefinedPosition

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("pygame not available. Install with: pip install pygame")

class PS5DualSenseMappings:
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
    
    # Button names for easy reference
    BUTTON_NAMES = {
        BUTTON_SQUARE: "Square",
        BUTTON_X: "X",
        BUTTON_CIRCLE: "Circle", 
        BUTTON_TRIANGLE: "Triangle",
        BUTTON_L1: "L1",
        BUTTON_R1: "R1",
        BUTTON_L2_DIGITAL: "L2 (digital)",
        BUTTON_R2_DIGITAL: "R2 (digital)",
        BUTTON_CREATE: "Create",
        BUTTON_OPTIONS: "Options",
        BUTTON_L3: "L3",
        BUTTON_R3: "R3",
        BUTTON_PS5: "PS5",
        BUTTON_TOUCHPAD: "Touchpad"
    }
    
    # Axis names for easy reference
    AXIS_NAMES = {
        AXIS_LEFT_X: "Left X",
        AXIS_LEFT_Y: "Left Y (inverted)",
        AXIS_RIGHT_X: "Right X",
        AXIS_L2: "L2 (analog)",
        AXIS_R2: "R2 (analog)", 
        AXIS_RIGHT_Y: "Right Y (inverted)"
    }
    
    @classmethod
    def get_axis_name(cls, axis_index):
        """Get the name of an axis by its index."""
        return cls.AXIS_NAMES.get(axis_index, f"Unknown Axis {axis_index}")
    
    @classmethod
    def get_button_name(cls, button_index):
        """Get the name of a button by its index."""
        return cls.BUTTON_NAMES.get(button_index, f"Unknown Button {button_index}")
    
    @classmethod
    def print_mappings_info(cls):
        """Print information about the controller mappings."""
        print("\nPS5 DualSense Controller Mappings:")
        print("=" * 40)
        print("Axes:")
        for axis_id, name in cls.AXIS_NAMES.items():
            print(f"  [{axis_id}] {name}")
        print("\nButtons:")
        for button_id, name in cls.BUTTON_NAMES.items():
            print(f"  [{button_id}] {name}")
        print("=" * 40)

class PS5ControllerHexapodController:
    """PS5 controller-based interactive controller for hexapod movement testing."""
    
    # Movement step parameters (easy to adjust)
    TRANSLATION_STEP = 10.0  # mm per analog unit
    ROTATION_STEP = 5.0      # degrees per analog unit (for yaw/pitch)
    ROLL_STEP = 2.0          # degrees per button press
    PITCH_STEP = 2.0         # degrees per analog unit (if you want to use a different step)
    YAW_STEP = 2.0           # degrees per analog unit (if you want to use a different step)
    Z_STEP = 10.0            # mm per analog unit (for up/down)
    
    def __init__(self):
        """Initialize the hexapod and controller parameters."""
        if not PYGAME_AVAILABLE:
            raise ImportError("pygame is required for PS5 controller support")
        
        try:
            self.hexapod = Hexapod()
            print("Hexapod initialized successfully")
        except Exception as e:
            print(f"Failed to initialize hexapod: {e}")
            raise
        
        # Set display environment for headless systems
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
        
        # Initialize pygame for controller support
        pygame.init()
        pygame.joystick.init()
        
        # Find and initialize PS5 controller
        self.controller = self._find_ps5_controller()
        if not self.controller:
            raise RuntimeError("No PS5 controller found. Please connect a controller and try again.")
        
        # Sensitivity and deadzone
        self.translation_sensitivity = 0.3
        self.rotation_sensitivity = 0.5
        self.deadzone = 0.1
        self.running = True
        
        # Current movement state
        self.current_tx = 0.0
        self.current_ty = 0.0
        self.current_tz = 0.0
        self.current_roll = 0.0
        self.current_pitch = 0.0
        self.current_yaw = 0.0
        
        # Movement update rate
        self.update_rate = 20  # Hz
        self.update_interval = 1.0 / self.update_rate
        
        # Button states
        self.button_states = {}
        self.last_button_states = {}
        
        print(f"PS5 Controller '{self.controller.get_name()}' initialized successfully")
    
    def _find_ps5_controller(self):
        """Find and initialize a PS5 controller."""
        joystick_count = pygame.joystick.get_count()
        print(f"Found {joystick_count} joystick(s)")
        
        for i in range(joystick_count):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            name = joystick.get_name().lower()
            print(f"Joystick {i}: {name}")
            
            # Check for PS5 controller (common names)
            if any(keyword in name for keyword in ['dualsense', 'ps5', 'playstation 5', 'wireless controller']):
                print(f"PS5 controller found: {name}")
                return joystick
        
        # If no PS5 controller found, use the first available controller
        if joystick_count > 0:
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
            print(f"Using controller: {joystick.get_name()}")
            return joystick
        
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
        # Process events to update controller state
        for event in pygame.event.get():
            pass
        
        # Get axes using PS5DualSenseMappings
        left_x = self._apply_deadzone(self.controller.get_axis(PS5DualSenseMappings.AXIS_LEFT_X))
        left_y = self._apply_deadzone(self.controller.get_axis(PS5DualSenseMappings.AXIS_LEFT_Y))
        right_x = self._apply_deadzone(self.controller.get_axis(PS5DualSenseMappings.AXIS_RIGHT_X))
        l2 = self._apply_deadzone(self.controller.get_axis(PS5DualSenseMappings.AXIS_L2))
        r2 = self._apply_deadzone(self.controller.get_axis(PS5DualSenseMappings.AXIS_R2))
        right_y = self._apply_deadzone(self.controller.get_axis(PS5DualSenseMappings.AXIS_RIGHT_Y))
        
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
        # Process events to update controller state
        for event in pygame.event.get():
            pass
        
        # Get buttons using PS5DualSenseMappings
        buttons = {
            'square': self.controller.get_button(PS5DualSenseMappings.BUTTON_SQUARE),
            'x': self.controller.get_button(PS5DualSenseMappings.BUTTON_X),
            'circle': self.controller.get_button(PS5DualSenseMappings.BUTTON_CIRCLE),
            'triangle': self.controller.get_button(PS5DualSenseMappings.BUTTON_TRIANGLE),
            'l1': self.controller.get_button(PS5DualSenseMappings.BUTTON_L1),
            'r1': self.controller.get_button(PS5DualSenseMappings.BUTTON_R1),
            'l2_digital': self.controller.get_button(PS5DualSenseMappings.BUTTON_L2_DIGITAL),
            'r2_digital': self.controller.get_button(PS5DualSenseMappings.BUTTON_R2_DIGITAL),
            'create': self.controller.get_button(PS5DualSenseMappings.BUTTON_CREATE),
            'options': self.controller.get_button(PS5DualSenseMappings.BUTTON_OPTIONS),
            'l3': self.controller.get_button(PS5DualSenseMappings.BUTTON_L3),
            'r3': self.controller.get_button(PS5DualSenseMappings.BUTTON_R3),
            'ps5': self.controller.get_button(PS5DualSenseMappings.BUTTON_PS5),
            'touchpad': self.controller.get_button(PS5DualSenseMappings.BUTTON_TOUCHPAD)
        }
        
        return buttons
    
    def _check_button_press(self, button_name):
        """Check if a button was just pressed (not held)."""
        current = self.button_states.get(button_name, False)
        last = self.last_button_states.get(button_name, False)
        return current and not last
    
    def print_help(self):
        """Print the help menu."""
        print("\n" + "="*60)
        print("PS5 DUAL SENSE CONTROLLER HEXAPOD MOVEMENT CONTROLLER")
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
        print("  X               - Additional function")
        print("  L1/R1           - Yaw left/right")
        print("  L3/R3           - Fine control mode toggle")
        print("  Create          - Additional function")
        print("  Options         - Additional function")
        print("  PS5             - Exit program")
        print("  Touchpad        - Additional function")
        print()
        print("Special Features:")
        print("  - Analog sticks provide continuous movement")
        print("  - Movement speed varies with stick deflection")
        print("  - Deadzone prevents drift from stick center")
        print("  - Y-axes are inverted (up=-1, down=+1)")
        print("  - Triggers provide analog Z-axis control")
        print("="*60)
    
    def show_current_position(self):
        """Display current movement state."""
        print(f"\nCurrent Position:")
        print(f"  Translation: X={self.current_tx:6.1f}, Y={self.current_ty:6.1f}, Z={self.current_tz:6.1f} mm")
        print(f"  Rotation:    Roll={self.current_roll:6.1f}, Pitch={self.current_pitch:6.1f}, Yaw={self.current_yaw:6.1f}°")
    
    def execute_movement(self, tx=0.0, ty=0.0, tz=0.0, roll=0.0, pitch=0.0, yaw=0.0):
        """Execute a movement command."""
        try:
            self.hexapod.move_body(tx=tx, ty=ty, tz=tz, roll=roll, pitch=pitch, yaw=yaw)
            
            # Update current state
            self.current_tx += tx
            self.current_ty += ty
            self.current_tz += tz
            self.current_roll += roll
            self.current_pitch += pitch
            self.current_yaw += yaw
            
        except Exception as e:
            print(f"Movement failed: {e}")
    
    def reset_to_start(self):
        """Reset hexapod to start position."""
        print("Resetting to start position...")
        try:
            self.hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
            self.hexapod.wait_until_motion_complete()
            
            # Reset current state
            self.current_tx = 0.0
            self.current_ty = 0.0
            self.current_tz = 0.0
            self.current_roll = 0.0
            self.current_pitch = 0.0
            self.current_yaw = 0.0
            
            print("Reset to start position completed")
        except Exception as e:
            print(f"Reset failed: {e}")
    
    def process_analog_inputs(self, analog_inputs):
        """Process analog stick inputs for continuous movement."""
        # Use class step parameters
        tx = analog_inputs['left_x'] * self.translation_sensitivity * self.TRANSLATION_STEP
        ty = -analog_inputs['left_y'] * self.translation_sensitivity * self.TRANSLATION_STEP
        roll = analog_inputs['right_x'] * self.rotation_sensitivity * self.ROLL_STEP  # fixed: right stick X now controls roll, correct direction
        pitch = -analog_inputs['right_y'] * self.rotation_sensitivity * self.ROTATION_STEP
        tz = (analog_inputs['r2'] - analog_inputs['l2']) * self.translation_sensitivity * self.Z_STEP
        # Yaw is now only controlled by buttons
        yaw = 0.0
        if any(abs(val) > 0.01 for val in [tx, ty, tz, roll, pitch]):
            self.execute_movement(tx=tx, ty=ty, tz=tz, roll=roll, pitch=pitch, yaw=yaw)
    
    def process_button_inputs(self):
        """Process button inputs for discrete actions and continuous yaw with L1/R1."""
        if self._check_button_press('triangle'):
            self.reset_to_start()
        elif self._check_button_press('square'):
            self.show_current_position()
        elif self._check_button_press('circle'):
            self.print_help()
        elif self._check_button_press('x'):
            pass  # X button pressed (no action)
        # Continuous yaw while holding L1/R1
        if self.button_states.get('l1', False):
            self.execute_movement(yaw=-self.YAW_STEP)
        if self.button_states.get('r1', False):
            self.execute_movement(yaw=self.YAW_STEP)
        if self._check_button_press('l3'):
            pass  # L3 pressed - Fine control mode toggle (no action)
        if self._check_button_press('r3'):
            pass  # R3 pressed - Fine control mode toggle (no action)
        if self._check_button_press('create'):
            pass  # Create button pressed (no action)
        if self._check_button_press('options'):
            pass  # Options button pressed (no action)
        if self._check_button_press('ps5'):
            self.exit_program()
        if self._check_button_press('touchpad'):
            pass  # Touchpad pressed (no action)
    
    def exit_program(self):
        """Exit the program."""
        self.running = False
        print("Exiting...")
    
    def run(self):
        """Run the interactive controller."""
        # Show controller mappings info
        PS5DualSenseMappings.print_mappings_info()
        
        self.print_help()
        self.reset_to_start()
        
        print("\nController active. Press Circle for help, PS5 to exit.")
        print("Move the analog sticks to control the hexapod.")
        
        last_update = time.time()
        
        while self.running:
            try:
                current_time = time.time()
                
                # Update at fixed rate
                if current_time - last_update >= self.update_interval:
                    # Get controller inputs
                    analog_inputs = self._get_analog_inputs()
                    self.button_states = self._get_button_states()
                    
                    # Process inputs
                    self.process_analog_inputs(analog_inputs)
                    self.process_button_inputs()
                    
                    # Update button states for next frame
                    self.last_button_states = self.button_states.copy()
                    
                    last_update = current_time
                
                # Small sleep to prevent high CPU usage
                time.sleep(0.01)
                
            except KeyboardInterrupt:
                print("\nInterrupted by user")
                break
            except Exception as e:
                print(f"Error during controller loop: {e}")
                break
        
        # Cleanup
        self.cleanup()
    
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
    """Main function to run the PS5 controller interactive controller."""
    controller = None
    try:
        controller = PS5ControllerHexapodController()
        controller.run()
    except Exception as e:
        print(f"Controller execution failed: {e}")
        if controller:
            controller.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main() 