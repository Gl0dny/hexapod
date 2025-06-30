#!/usr/bin/env python3
"""
Interactive test script for hexapod movement using move_body method.

This script provides an interactive interface to test the hexapod's movement
capabilities using keyboard commands.

Usage:
    python test_hexapod_interactive.py
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = (SCRIPT_DIR.parent.parent / "src").resolve()
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from robot import Hexapod, PredefinedPosition

class InteractiveHexapodController:
    """Interactive controller for hexapod movement testing."""
    
    def __init__(self):
        """Initialize the hexapod and controller parameters."""
        try:
            self.hexapod = Hexapod()
            print("Hexapod initialized successfully")
        except Exception as e:
            print(f"Failed to initialize hexapod: {e}")
            raise
        
        # Movement parameters
        self.translation_step = 10.0  # mm per key press
        self.rotation_step = 5.0      # degrees per key press
        self.running = True
        
        # Current movement state
        self.current_tx = 0.0
        self.current_ty = 0.0
        self.current_tz = 0.0
        self.current_roll = 0.0
        self.current_pitch = 0.0
        self.current_yaw = 0.0
        
        self.command_map = {
            'W': self.move_forward,
            'S': self.move_backward,
            'A': self.move_left,
            'D': self.move_right,
            'Q': self.move_up,
            'E': self.move_down,
            'I': self.pitch_forward,
            'K': self.pitch_backward,
            'J': self.roll_left,
            'L': self.roll_right,
            'U': self.yaw_left,
            'O': self.yaw_right,
            'R': self.reset_to_start,
            'C': self.show_current_position,
            'H': self.print_help,
            'X': self.exit_program,
        }
        
    def print_help(self):
        """Print the help menu."""
        print("\n" + "="*60)
        print("HEXAPOD INTERACTIVE MOVEMENT CONTROLLER")
        print("="*60)
        print("Translation Controls (X, Y, Z):")
        print("  A/D    - Left/Right (X-axis)")
        print("  W/S    - Forward/Backward (Y-axis)")
        print("  Q/E    - Up/Down (Z-axis)")
        print()
        print("Rotation Controls (Roll, Pitch, Yaw):")
        print("  J/L    - Roll left/right (X-axis rotation - bank)")
        print("  I/K    - Pitch forward/backward (Y-axis rotation - tilt)")
        print("  U/O    - Yaw left/right (Z-axis rotation)")
        print()
        print("Special Commands:")
        print("  R      - Reset to start position")
        print("  H      - Show this help menu")
        print("  X      - Exit program")
        print("  C      - Show current position")
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
            self.hexapod.wait_until_motion_complete()
            
            # Update current state
            self.current_tx += tx
            self.current_ty += ty
            self.current_tz += tz
            self.current_roll += roll
            self.current_pitch += pitch
            self.current_yaw += yaw
            
            print(f"Movement executed: tx={tx}, ty={ty}, tz={tz}, roll={roll}, pitch={pitch}, yaw={yaw}")
            
        except Exception as e:
            print(f"Movement failed: {e}")
    
    def reset_to_start(self):
        """Reset hexapod to start position."""
        print("Resetting to start position...")
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
    
    def move_forward(self):
        self.execute_movement(ty=self.translation_step)
        print(f"Forward: +{self.translation_step}mm")
    def move_backward(self):
        self.execute_movement(ty=-self.translation_step)
        print(f"Backward: -{self.translation_step}mm")
    def move_left(self):
        self.execute_movement(tx=-self.translation_step)
        print(f"Left: -{self.translation_step}mm")
    def move_right(self):
        self.execute_movement(tx=self.translation_step)
        print(f"Right: +{self.translation_step}mm")
    def move_up(self):
        self.execute_movement(tz=self.translation_step)
        print(f"Up: +{self.translation_step}mm")
    def move_down(self):
        self.execute_movement(tz=-self.translation_step)
        print(f"Down: -{self.translation_step}mm")
    def pitch_forward(self):
        self.execute_movement(pitch=self.rotation_step)
        print(f"Pitch forward: +{self.rotation_step}°")
    def pitch_backward(self):
        self.execute_movement(pitch=-self.rotation_step)
        print(f"Pitch backward: -{self.rotation_step}°")
    def roll_left(self):
        self.execute_movement(roll=-self.rotation_step)
        print(f"Roll left: -{self.rotation_step}°")
    def roll_right(self):
        self.execute_movement(roll=self.rotation_step)
        print(f"Roll right: +{self.rotation_step}°")
    def yaw_left(self):
        self.execute_movement(yaw=self.rotation_step)
        print(f"Yaw left: +{self.rotation_step}°")
    def yaw_right(self):
        self.execute_movement(yaw=-self.rotation_step)
        print(f"Yaw right: -{self.rotation_step}°")
    def exit_program(self):
        self.running = False
        print("Exiting...")

    def handle_input(self, key):
        """Handle keyboard input and execute corresponding movement."""
        key = key.upper()
        handler = self.command_map.get(key)
        if handler:
            handler()
        else:
            print(f"Unknown key: {key}. Press 'H' for help.")
    
    def run(self):
        """Run the interactive controller."""
        self.print_help()
        self.reset_to_start()
        
        print("\nReady for input. Press 'H' for help, 'X' to exit.")
        
        while self.running:
            try:
                # Get single character input
                key = input("\nEnter command: ").strip()
                if key:
                    self.handle_input(key[0])
                    
            except KeyboardInterrupt:
                print("\nInterrupted by user")
                break
            except EOFError:
                print("\nEnd of input")
                break
            except Exception as e:
                print(f"Input error: {e}")
        
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

def main():
    """Main function to run the interactive controller."""
    controller = None
    try:
        controller = InteractiveHexapodController()
        controller.run()
    except Exception as e:
        print(f"Controller execution failed: {e}")
        if controller:
            controller.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main() 