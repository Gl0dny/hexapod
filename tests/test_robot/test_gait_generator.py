#!/usr/bin/env python3
"""
Minimal step-by-step test script for hexapod movement.
Start with basic initialization, then add movement commands one by one.
"""

import sys
import time
from pathlib import Path

# Add the src directory to the Python path
# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent.parent / 'src')
sys.path.append(src_path)

from robot.hexapod import Hexapod, PredefinedPosition

def main():
    """Basic hexapod initialization and setup."""
    print("=== Step-by-Step Hexapod Test ===")
    print("Coordinate system: +X = Right, +Y = Forward, +Z = Up")
    print("Leg numbering: 0=Right, 1=Right Front, 2=Left Front, 3=Left, 4=Left Back, 5=Right Back")
    
    # Initialize hexapod
    config_path = Path('src/robot/config/hexapod_config.yaml')
    calibration_path = Path('src/robot/config/calibration.json')
    
    print("\nInitializing hexapod...")
    hexapod = Hexapod(config_path=config_path, calibration_data_path=calibration_path)
    
    try:
        # Move to home position
        print("Moving to home position...")
        hexapod.move_to_position(PredefinedPosition.ZERO)
        hexapod.wait_until_motion_complete()
        print("✓ Moved to ZERO position")
        
        # Show current leg positions
        print("\nCurrent leg positions:")
        for i, pos in enumerate(hexapod.current_leg_positions):
            leg_names = ['Right', 'Right Front', 'Left Front', 'Left', 'Left Back', 'Right Back']
            print(f"  Leg {i} ({leg_names[i]}): ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})")
        
        print("\n✓ Basic initialization complete!")
        print("Add movement commands below this line...")

        # ========================================
        # GAIT GENERATOR EXAMPLES (MINIMAL)
        # ========================================
        
        # Example: Create tripod gait
        from robot.gait_generator import TripodGait
        gait = TripodGait(hexapod, step_radius=30.0, leg_lift_distance=10.0, dwell_time=0.1)
        print("✓ Created TripodGait")
        
        # Example: Set forward movement (+Y direction)
        # gait.set_direction((0.0, 1.0), rotation=0.0)  # Forward, no rotation
        # print("✓ Set direction: Forward")
        
        # Example: Set right movement (+X direction)
        # gait.set_direction((1.0, 0.0), rotation=0.0)  # Right, no rotation
        # print("✓ Set direction: Right")
        
        # Example: Set clockwise rotation (no translation)
        gait.set_direction((0.0, 0.0), rotation=0.66)  # No translation, clockwise rotation
        print("✓ Set direction: Clockwise rotation")
        
        # Example: Set counterclockwise rotation (no translation)
        # gait.set_direction((0.0, 0.0), rotation=-1.0)  # No translation, counterclockwise rotation
        # print("✓ Set direction: Counterclockwise rotation")
        
        # Example: Start gait movement
        print("Starting gait movement...")
        hexapod.gait_generator.start(gait)
        time.sleep(15.0)  # Run for 3 seconds
        hexapod.gait_generator.stop()
        print("✓ Stopped gait movement")
        
        # Example: Complete gait test sequence
        # from robot.gait_generator import TripodGait
        # gait = TripodGait(hexapod, step_radius=40.0, leg_lift_distance=30.0, dwell_time=0.5)
        # 
        # # Test forward movement
        # print("Testing forward movement...")
        # gait.set_direction((0.0, 1.0), rotation=0.0)
        # hexapod.gait_generator.start(gait)
        # time.sleep(2.0)
        # hexapod.gait_generator.stop()
        # print("✓ Forward movement complete")
        # 
        # time.sleep(1.0)  # Pause between tests
        # 
        # # Test rotation
        # print("Testing clockwise rotation...")
        # gait.set_direction((0.0, 0.0), rotation=1.0)
        # hexapod.gait_generator.start(gait)
        # time.sleep(2.0)
        # hexapod.gait_generator.stop()
        # print("✓ Rotation complete")
        
        # Return to home position
        print("\nReturning to home position...")
        # hexapod.move_to_position(PredefinedPosition.ZERO)
        # hexapod.wait_until_motion_complete()
        print("✓ Returned to ZERO position")
        
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt, stopping...")
        # hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
        # hexapod.wait_until_motion_complete()
    except Exception as e:
        print(f"\nError: {e}")
        # hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
        # hexapod.wait_until_motion_complete()
    finally:
        print("Deactivating servos...")
        hexapod.deactivate_all_servos()

if __name__ == "__main__":
    main() 