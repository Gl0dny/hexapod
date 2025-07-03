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
    GAIT_STEERING_MODE = "gait_steering"
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
    
    @abstractmethod
    def cleanup(self):
        """Clean up resources."""
        pass
    
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
    
    def set_mode(self, mode_name: str):
        """Set the current control mode (e.g., 'body_control', 'gait_steering')."""
        if mode_name not in (self.BODY_CONTROL_MODE, self.GAIT_STEERING_MODE):
            raise ValueError(f"Unknown mode: {mode_name}")
        self.current_mode = mode_name
        print(f"Switched to mode: {self.current_mode}")

    def get_start_position(self):
        """Return the PredefinedPosition to use for reset_to_start. Can be mode-dependent."""
        if self.current_mode == self.GAIT_STEERING_MODE:
            return PredefinedPosition.HIGH_PROFILE
        return PredefinedPosition.LOW_PROFILE
    
    def reset_to_start(self):
        """Reset hexapod to start position."""
        print("Resetting to start position...")
        try:
            start_position = self.get_start_position()
            self.hexapod.move_to_position(start_position)
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
    
    def start_gait_steering(self, gait_type=None, **kwargs):
        """Start gait steering with the specified gait type (default: TripodGait)."""
        if self.gait is None or gait_type is not None:
            if gait_type is None:
                gait_type = TripodGait
            self.gait = gait_type(self.hexapod, **kwargs)
        if not self.is_gait_steering_active():
            self.gait_generator.start(self.gait)
            print("Gait generation started")

    def stop_gait_steering(self):
        """Stop gait steering if running."""
        if self.is_gait_steering_active():
            self.gait_generator.stop()
            print("Gait generation stopped")

    def update_gait_direction(self, direction, rotation=0.0):
        """Update the gait direction and rotation input."""
        if self.gait:
            self.gait.set_direction(direction, rotation)

    def is_gait_steering_active(self):
        """Return True if gait generator is running."""
        return getattr(self.gait_generator, 'is_running', False)

    def _get_direction_name(self, direction_tuple):
        magnitude = (direction_tuple[0] ** 2 + direction_tuple[1] ** 2) ** 0.5
        if magnitude < 0.05:
            return "neutral"
        # Exclude 'neutral' from search for closest direction
        min_dist = float('inf')
        closest_name = None
        for name, vec in BaseGait.DIRECTION_MAP.items():
            if name == "neutral":
                continue
            dist = ((direction_tuple[0] - vec[0]) ** 2 + (direction_tuple[1] - vec[1]) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                closest_name = name
        return closest_name

    def _get_rotation_name(self, rotation):
        if abs(rotation) < 0.05:
            return "none"
        elif rotation > 0:
            return "clockwise"
        else:
            return "counterclockwise"

    def show_gait_status(self):
        """Display current gait generator status in gait steering mode."""
        if not hasattr(self, 'gait') or self.gait is None:
            print("No gait is currently active.")
            return
        print("\nGait Steering Mode Status:")
        print(f"- Gait Type: {type(self.gait).__name__}")
        # Try to get current phase/state if available
        current_state = getattr(self.gait_generator, 'current_state', None)
        if current_state:
            print(f"- Current Phase: {getattr(current_state, 'phase', 'N/A')}")
            print(f"- Swing Legs: {getattr(current_state, 'swing_legs', 'N/A')}")
            print(f"- Stance Legs: {getattr(current_state, 'stance_legs', 'N/A')}")
            print(f"- Dwell Time: {getattr(current_state, 'dwell_time', 'N/A')}s")
        print(f"- Step Radius: {getattr(self.gait, 'step_radius', 'N/A')} mm")
        # Show current direction and rotation
        direction = getattr(self.gait, 'direction_input', (0.0, 0.0))
        if hasattr(direction, 'to_tuple'):
            x, y = direction.to_tuple()
        else:
            x, y = direction[0], direction[1]
        direction_name = self._get_direction_name((x, y))
        rotation = getattr(self.gait, 'rotation_input', 0.0)
        rotation_name = self._get_rotation_name(rotation)
        print(f"- Current Direction: X={x:.2f}, Y={y:.2f} ({direction_name})")
        print(f"- Current Rotation: {rotation:.2f} ({rotation_name})")
        print("- Leg Positions:")
        for i, pos in enumerate(getattr(self, 'hexapod', None).current_leg_positions):
            print(f"    Leg {i}: {tuple(round(x, 2) for x in pos)}")

    def print_current_position_details(self):
        print(f"\nCurrent Position:")
        print(f"  Translation: X={self.current_tx:6.1f}, Y={self.current_ty:6.1f}, Z={self.current_tz:6.1f} mm")
        print(f"  Rotation:    Roll={self.current_roll:6.1f}, Pitch={self.current_pitch:6.1f}, Yaw={self.current_yaw:6.1f}°")

    def show_current_position(self):
        """Display current movement state or gait status depending on mode."""
        if self.current_mode == self.GAIT_STEERING_MODE:
            self.show_gait_status()
            return
        self.print_current_position_details()
    
    def process_movement_inputs(self, inputs):
        """Process movement inputs and execute hexapod movement."""
        # Extract movement values from inputs
        tx = inputs.get('tx', 0.0)
        ty = inputs.get('ty', 0.0)
        tz = inputs.get('tz', 0.0)
        roll = inputs.get('roll', 0.0)
        pitch = inputs.get('pitch', 0.0)
        yaw = inputs.get('yaw', 0.0)
        
        # Execute movement if any input is non-zero
        if any(abs(val) > 0.01 for val in [tx, ty, tz, roll, pitch, yaw]):
            self.execute_movement(tx=tx, ty=ty, tz=tz, roll=roll, pitch=pitch, yaw=yaw)
    
    def run(self):
        """Run the hexapod controller."""
        self.print_help()
        self.reset_to_start()
        
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