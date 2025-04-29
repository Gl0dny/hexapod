#!/usr/bin/env python3
import sys
import os
import time
import argparse
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from robot.hexapod import Hexapod, PredefinedPosition
from robot.gait_generator import GaitGenerator, TripodGait, WaveGait

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test different gait patterns for the hexapod robot.')
    parser.add_argument('--gait', type=str, choices=['tripod', 'wave'], default='tripod',
                      help='Type of gait to test (tripod or wave)')
    parser.add_argument('--duration', type=float, default=10.0,
                      help='Duration to run the gait in seconds')
    args = parser.parse_args()

    # Initialize the hexapod
    config_path = Path('src/robot/config/hexapod_config.yaml')
    calibration_path = Path('src/robot/config/calibration.json')
    
    print(f"Initializing hexapod...")
    hexapod = Hexapod(config_path=config_path, calibration_data_path=calibration_path)
    
    try:
        # Move to home position
        print("Moving to home position...")
        hexapod.move_to_position(PredefinedPosition.ZERO)
        hexapod.wait_until_motion_complete()
        
        # Create the appropriate gait instance
        if args.gait == "tripod":
            gait = TripodGait(hexapod)
            print("Created TripodGait instance")
        else:  # wave
            gait = WaveGait(hexapod)
            print("Created WaveGait instance")
        
        # Start the gait generator with the selected gait
        print(f"Starting {args.gait} gait...")
        hexapod.gait_generator.start(gait)
        
        # Let it run for specified duration
        print(f"Running gait for {args.duration} seconds...")
        time.sleep(args.duration)
        
        # Stop the gait generator
        print("Stopping gait...")
        hexapod.gait_generator.stop()
        
        # Move back to home position
        print("Moving back to home position...")
        hexapod.move_to_position(PredefinedPosition.ZERO)
        hexapod.wait_until_motion_complete()
        
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt, stopping...")
        hexapod.gait_generator.stop()
        hexapod.move_to_position(PredefinedPosition.ZERO)
        hexapod.wait_until_motion_complete()
    except Exception as e:
        print(f"\nError: {e}")
        hexapod.gait_generator.stop()
        hexapod.move_to_position(PredefinedPosition.ZERO)
        hexapod.wait_until_motion_complete()
    finally:
        # Deactivate all servos
        print("Deactivating servos...")
        hexapod.deactivate_all_servos()

if __name__ == "__main__":
    main() 