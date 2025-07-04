#!/usr/bin/env python3
"""
Base manual hexapod controller implementation.

This module provides the abstract base class for all manual hexapod controllers,
defining the common interface and functionality for manual control systems.
"""

import sys
import time
from pathlib import Path
from abc import ABC, abstractmethod

# Add the src directory to the path so we can import our modules
SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = (SCRIPT_DIR.parent.parent).resolve()
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from robot import Hexapod, PredefinedPosition
from gait_generator import BaseGait, TripodGait

class ManualHexapodController(ABC):
    """Abstract base class for all manual hexapod controllers."""
    
    # Movement step parameters (easy to adjust)
    TRANSLATION_STEP = 10.0  # mm per analog unit
    ROTATION_STEP = 5.0      # degrees per analog unit (for yaw/pitch)
    ROLL_STEP = 2.0          # degrees per button press
    PITCH_STEP = 2.0         # degrees per analog unit (if you want to use a different step)
    YAW_STEP = 2.0           # degrees per analog unit (if you want to use a different step)
    Z_STEP = 10.0            # mm per analog unit (for up/down)
    
    # Supported modes
    BODY_CONTROL_MODE = "body_control"
    GAIT_CONTROL_MODE = "gait_control"
    DEFAULT_MODE = BODY_CONTROL_MODE
    
    def __init__(self):
        """Initialize the hexapod controller."""
        try:
            self.hexapod = Hexapod()
            print("Hexapod initialized successfully")
        except Exception as e:
            print(f"Failed to initialize hexapod: {e}")
            raise
        
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
        self.running = True

        # Dual-mode support
        self.current_mode = self.DEFAULT_MODE

        # Gait steering support
        self.gait = None
        self.gait_generator = self.hexapod.gait_generator
    
    @abstractmethod
    def get_inputs(self):
        """Get current input values from the interface."""
        pass
    
    @abstractmethod
    def print_help(self):
        """Print help information for the interface."""
        pass
    
    def cleanup(self):
        """Clean up common resources (gait generation, servos)."""
        try:
            # Stop gait generation if running
            if hasattr(self, 'hexapod') and hasattr(self.hexapod, 'gait_generator'):
                if self.hexapod.gait_generator.is_running:
                    self.hexapod.gait_generator.stop()
                    print("Gait generation stopped")
            
            # Reset to safe position and deactivate servos
            self.reset_position()
            self.hexapod.deactivate_all_servos()
            print("Hexapod servos deactivated")
        except Exception as e:
            print(f"Error during base cleanup: {e}")
        
        # Call subclass-specific cleanup
        self.cleanup_controller()

    @abstractmethod
    def cleanup_controller(self):
        """Clean up resources specific to this controller type."""
        pass
    
    def set_mode(self, mode_name: str):
        """Set the current control mode (e.g., 'body_control', 'gait_control')."""
        if mode_name not in (self.BODY_CONTROL_MODE, self.GAIT_CONTROL_MODE):
            raise ValueError(f"Unknown mode: {mode_name}")
        self.current_mode = mode_name
        print(f"Switched to mode: {self.current_mode}")

    def reset_position(self):
        """Reset hexapod to reset position."""
        def _get_reset_position():
            """Return the PredefinedPosition to use for reset_position. Can be mode-dependent."""
            if self.current_mode == self.GAIT_CONTROL_MODE:
                return PredefinedPosition.HIGH_PROFILE
            return PredefinedPosition.LOW_PROFILE
        
        print("Resetting to reset position...")
        try:
            reset_position = _get_reset_position()
            self.hexapod.move_to_position(reset_position)
            self.hexapod.wait_until_motion_complete()
            
            # Reset current state
            self.current_tx = 0.0
            self.current_ty = 0.0
            self.current_tz = 0.0
            self.current_roll = 0.0
            self.current_pitch = 0.0
            self.current_yaw = 0.0
            
            print("Reset position completed")
        except Exception as e:
            print(f"Reset failed: {e}")
    
    def start_gait_control(self, gait_type=None, **kwargs):
        """Start gait control with the specified gait type (default: TripodGait)."""
        if self.gait is None or gait_type is not None:
            if gait_type is None:
                gait_type = TripodGait
            self.gait = gait_type(self.hexapod, **kwargs)
        if not self.is_gait_control_active():
            self.gait_generator.start(self.gait)
            print("Gait generation started")

    def stop_gait_control(self):
        """Stop gait control if running."""
        if self.is_gait_control_active():
            self.gait_generator.stop()
            print("Gait generation stopped")

    def is_gait_control_active(self):
        """Return True if gait generator is running."""
        return getattr(self.gait_generator, 'is_running', False)
    
    def process_movement_inputs(self, inputs):
        """
        Process movement inputs and apply them based on current mode.
        
        This method handles both body control and gait control modes:
        - Body Control Mode: Applies translation and rotation to hexapod body
        - Gait Control Mode: Updates gait direction and rotation inputs
        
        Args:
            inputs (dict): Input values from get_inputs() method
        """
        def _process_body_control():
            """Process inputs for body control mode (direct IK movement)."""
            # Extract movement values
            tx = inputs.get('tx', 0.0)
            ty = inputs.get('ty', 0.0)
            tz = inputs.get('tz', 0.0)
            roll = inputs.get('roll', 0.0)
            pitch = inputs.get('pitch', 0.0)
            yaw = inputs.get('yaw', 0.0)
            
            # Apply movement if any input is non-zero
            if any(abs(val) > 0.01 for val in [tx, ty, tz, roll, pitch, yaw]):
                try:
                    # Apply movement to hexapod
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

        def _update_gait_direction(direction, rotation=0.0):
            """Update the gait direction and rotation input."""
            if self.gait:
                self.gait.set_direction(direction, rotation)
        
        def _process_gait_control():
            """Process inputs for gait control mode (walking movement)."""
            # Extract gait control values
            direction_x = inputs.get('direction_x', 0.0)
            direction_y = inputs.get('direction_y', 0.0)
            rotation = inputs.get('rotation', 0.0)
            
            # Update gait direction and rotation
            if hasattr(self, 'gait') and self.gait is not None:
                # Normalize direction if magnitude is significant
                if abs(direction_x) > 0.01 or abs(direction_y) > 0.01:
                    # Normalize direction vector
                    magnitude = (direction_x**2 + direction_y**2)**0.5
                    if magnitude > 0:
                        direction_x /= magnitude
                        direction_y /= magnitude
                        # Scale by sensitivity
                        direction_x *= self.translation_sensitivity
                        direction_y *= self.translation_sensitivity
                
                # Update gait direction and rotation
                _update_gait_direction((direction_x, direction_y), rotation=rotation)
        
        # Route to appropriate processing based on mode
        if self.current_mode == self.BODY_CONTROL_MODE:
            _process_body_control()
        elif self.current_mode == self.GAIT_CONTROL_MODE:
            _process_gait_control()
        else:
            print(f"Warning: Unknown mode '{self.current_mode}'")

    def show_gait_status(self):
        """
        Display current gait generator status in gait control mode.
        
        Shows comprehensive information about the current gait state including:
        - Gait type and current phase
        - Which legs are in swing vs stance
        - Timing parameters (dwell time, step radius)
        - Current movement inputs with human-readable names
        - All leg positions
        
        This method is called by show_current_position() when in gait control mode.
        """
        def _get_direction_name(direction_tuple):
            """Get the closest direction name from BaseGait.DIRECTION_MAP."""
            # Check if direction magnitude is very small (near center)
            magnitude = (direction_tuple[0] ** 2 + direction_tuple[1] ** 2) ** 0.5
            if magnitude < 0.05:
                return "neutral"
            
            # Find the closest non-neutral direction by computing distances
            min_dist = float('inf')
            closest_name = None
            for name, vec in BaseGait.DIRECTION_MAP.items():
                # Skip 'neutral' when searching for closest direction
                if name == "neutral":
                    continue
                # Compute Euclidean distance between current direction and named direction
                dist = ((direction_tuple[0] - vec[0]) ** 2 + (direction_tuple[1] - vec[1]) ** 2) ** 0.5
                if dist < min_dist:
                    min_dist = dist
                    closest_name = name
            return closest_name
        
        def _get_rotation_name(rotation):
            """Get a human-readable name for the rotation value."""
            # Use small threshold to determine if rotation is effectively zero
            if abs(rotation) < 0.05:
                return "none"
            elif rotation > 0:
                return "clockwise"
            else:
                return "counterclockwise"
        
        # Check if gait is active
        if not hasattr(self, 'gait') or self.gait is None:
            print("No gait is currently active.")
            return
        
        print("\nGait Control Mode Status:")
        print(f"- Gait Type: {type(self.gait).__name__}")
        
        # Try to get current phase/state information from gait generator
        current_state = getattr(self.gait_generator, 'current_state', None)
        if current_state:
            print(f"- Current Phase: {getattr(current_state, 'phase', 'N/A')}")
            print(f"- Swing Legs: {getattr(current_state, 'swing_legs', 'N/A')}")
            print(f"- Stance Legs: {getattr(current_state, 'stance_legs', 'N/A')}")
            print(f"- Dwell Time: {getattr(current_state, 'dwell_time', 'N/A')}s")
        
        # Display gait parameters
        print(f"- Step Radius: {getattr(self.gait, 'step_radius', 'N/A')} mm")
        
        # Show current direction with human-readable name
        direction = getattr(self.gait, 'direction_input', (0.0, 0.0))
        if hasattr(direction, 'to_tuple'):
            x, y = direction.to_tuple()
        else:
            x, y = direction[0], direction[1]
        direction_name = _get_direction_name((x, y))
        
        # Show current rotation with human-readable name
        rotation = getattr(self.gait, 'rotation_input', 0.0)
        rotation_name = _get_rotation_name(rotation)
        
        print(f"- Current Direction: X={x:.2f}, Y={y:.2f} ({direction_name})")
        print(f"- Current Rotation: {rotation:.2f} ({rotation_name})")
        
        # Display all leg positions
        print("- Leg Positions:")
        for i, pos in enumerate(getattr(self, 'hexapod', None).current_leg_positions):
            print(f"    Leg {i}: {tuple(round(x, 2) for x in pos)}")

    def print_current_position_details(self):
        """
        Print the current body position and orientation in a formatted way.
        
        Displays the current translation (X, Y, Z) and rotation (Roll, Pitch, Yaw)
        values in a user-friendly format with proper units and alignment.
        
        This method is called by show_current_position() when in body control mode.
        """
        print(f"\nCurrent Position:")
        print(f"  Translation: X={self.current_tx:6.1f}, Y={self.current_ty:6.1f}, Z={self.current_tz:6.1f} mm")
        print(f"  Rotation:    Roll={self.current_roll:6.1f}, Pitch={self.current_pitch:6.1f}, Yaw={self.current_yaw:6.1f}°")

    def show_current_position(self):
        """
        Display current movement state or gait status depending on mode.
        
        This method provides context-appropriate feedback:
        - In body control mode: Shows current translation and rotation values
        - In gait control mode: Shows detailed gait status with direction/rotation names
        
        Called when user presses the "show current position" button.
        """
        if self.current_mode == self.GAIT_CONTROL_MODE:
            # In gait mode, show comprehensive gait status
            self.show_gait_status()
            return
        # In body control mode, show position details
        self.print_current_position_details()
    
    def run(self):
        """Run the hexapod controller."""
        self.print_help()
        self.reset_position()
        
        print("\nHexapod controller active. Use your interface to control movement.")
        
        last_update = time.time()
        
        while self.running:
            try:
                current_time = time.time()
                
                # Update at fixed rate
                if current_time - last_update >= self.update_interval:
                    # Get inputs from the interface
                    inputs = self.get_inputs()
                    
                    # Process movement inputs
                    self.process_movement_inputs(inputs)
                    
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