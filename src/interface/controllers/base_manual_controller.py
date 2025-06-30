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

class ManualHexapodController(ABC):
    """Abstract base class for all manual hexapod controllers."""
    
    # Movement step parameters (easy to adjust)
    TRANSLATION_STEP = 10.0  # mm per analog unit
    ROTATION_STEP = 5.0      # degrees per analog unit (for yaw/pitch)
    ROLL_STEP = 2.0          # degrees per button press
    PITCH_STEP = 2.0         # degrees per analog unit (if you want to use a different step)
    YAW_STEP = 2.0           # degrees per analog unit (if you want to use a different step)
    Z_STEP = 10.0            # mm per analog unit (for up/down)
    
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
    
    def show_current_position(self):
        """Display current movement state."""
        print(f"\nCurrent Position:")
        print(f"  Translation: X={self.current_tx:6.1f}, Y={self.current_ty:6.1f}, Z={self.current_tz:6.1f} mm")
        print(f"  Rotation:    Roll={self.current_roll:6.1f}, Pitch={self.current_pitch:6.1f}, Yaw={self.current_yaw:6.1f}°")
    
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