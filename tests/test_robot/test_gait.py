#!/usr/bin/env python3
import sys
import os
import time
import argparse
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from robot.hexapod import Hexapod, PredefinedPosition, PredefinedAnglePosition
from robot.gait_generator import GaitGenerator, TripodGait, WaveGait

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test different gait patterns for the hexapod robot.')
    parser.add_argument('--gait', type=str, choices=['tripod', 'wave'], default='tripod',
                      help='Type of gait to test (tripod or wave)')
    parser.add_argument('--duration', type=float, default=10.0,
                      help='Duration to run the gait in seconds')
    parser.add_argument('--swing-distance', type=float, default=0.0,
                      help='Distance to move forward during swing phase (mm)')
    parser.add_argument('--swing-height', type=float, default=30.0,
                      help='Height to lift leg during swing phase (mm)')
    parser.add_argument('--stance-distance', type=float, default=0.0,
                      help='Distance to move backward during stance phase (mm)')
    parser.add_argument('--dwell-time', type=float, default=1.0,
                      help='Time to spend in each phase (seconds)')
    parser.add_argument('--stability-threshold', type=float, default=0.2,
                      help='Maximum allowed IMU deviation for stability check')
    args = parser.parse_args()

    # Initialize the hexapod
    config_path = Path('src/robot/config/hexapod_config.yaml')
    calibration_path = Path('src/robot/config/calibration.json')
    
    print(f"Initializing hexapod...")
    hexapod = Hexapod(config_path=config_path, calibration_data_path=calibration_path)
    
    try:
        # Move to home position
        print("Moving to home position...")
        hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
        hexapod.wait_until_motion_complete()
        
        # Create the appropriate gait instance with configured parameters
        gait_params = {
            'swing_distance': args.swing_distance,
            'swing_height': args.swing_height,
            'stance_distance': args.stance_distance,
            'stability_threshold': args.stability_threshold
        }
        
        # Use default dwell time if not specified
        if args.dwell_time is not None:
            gait_params['dwell_time'] = args.dwell_time
        
        if args.gait == "tripod":
            gait = TripodGait(hexapod, **gait_params)
            print("Created TripodGait instance with parameters:")
        else:  # wave
            gait = WaveGait(hexapod, **gait_params)
            print("Created WaveGait instance with parameters:")
        
        # Print the configured parameters
        print(f"  Swing distance: {gait.swing_distance}mm")
        print(f"  Swing height: {gait.swing_height}mm")
        print(f"  Stance distance: {gait.stance_distance}mm")
        print(f"  Dwell time: {gait.dwell_time}s")
        print(f"  Stability threshold: {gait.stability_threshold}")
        
        # Start the gait generator with the selected gait
        print(f"\nStarting {args.gait} gait...")
        hexapod.gait_generator.start(gait)
        
        # Let it run for specified duration
        print(f"Running gait for {args.duration} seconds...")
        time.sleep(args.duration)
        
        # Stop the gait generator
        print("Stopping gait...")
        hexapod.gait_generator.stop()
        
        # Move back to home position
        print("Moving back to home position...")
        hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
        hexapod.wait_until_motion_complete()
        
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt, stopping...")
        hexapod.gait_generator.stop()
        hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
        hexapod.wait_until_motion_complete()
    except Exception as e:
        print(f"\nError: {e}")
        hexapod.gait_generator.stop()
        hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
        hexapod.wait_until_motion_complete()
    finally:
        # Deactivate all servos
        print("Deactivating servos...")
        hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
        hexapod.wait_until_motion_complete()
        hexapod.deactivate_all_servos()

if __name__ == "__main__":
    main() 