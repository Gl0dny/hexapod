#!/usr/bin/env python3
import sys
import os
import time
import argparse
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from robot.hexapod import Hexapod, PredefinedPosition, PredefinedAnglePosition
from robot.gait_generator import TripodGait, WaveGait

def main(args):
    # Initialize the hexapod
    config_path = Path('src/robot/config/hexapod_config.yaml')
    calibration_path = Path('src/robot/config/calibration.json')
    
    print(f"Initializing hexapod...")
    hexapod = Hexapod(config_path=config_path, calibration_data_path=calibration_path)
    
    try:
        # Move to home position
        print("Moving to home position...")
        hexapod.move_to_position(PredefinedPosition.UPRIGHT)
        hexapod.wait_until_motion_complete()
        
        # Create the appropriate gait instance with circle-based parameters
        gait_params = {
            'step_radius': args.step_radius,
            'leg_lift_distance': args.leg_lift_distance,
            'leg_lift_incline': args.leg_lift_incline,
            'stance_height': args.stance_height,
            'dwell_time': args.dwell_time,
            'stability_threshold': args.stability_threshold
        }
        
        if args.gait == "tripod":
            gait = TripodGait(hexapod, **gait_params)
            print("Created TripodGait instance with circle-based parameters:")
        else:  # wave
            gait = WaveGait(hexapod, **gait_params)
            print("Created WaveGait instance with circle-based parameters:")
        
        # Print the configured parameters
        print(f"  Step radius: {gait.step_radius}mm")
        print(f"  Leg lift distance: {gait.leg_lift_distance}mm")
        print(f"  Leg lift incline: {gait.leg_lift_incline}")
        print(f"  Stance height: {gait.stance_height}mm")
        print(f"  Dwell time: {gait.dwell_time}s")
        print(f"  Stability threshold: {gait.stability_threshold}")
        print(f"  Movement pattern: {args.movement_pattern}")
        print(f"  Movement speed: {args.movement_speed}")
        print(f"  Rotation speed: {args.rotation_speed}")
        
        # Set movement based on pattern
        movement_direction = (0.0, 0.0)
        rotation_speed = 0.0
        
        if args.movement_pattern == 'forward':
            base_direction = gait.DIRECTION_MAP['forward']
            movement_direction = (base_direction[0] * args.movement_speed, base_direction[1] * args.movement_speed)
            print(f"  Movement direction: Forward ({movement_direction[0]:.1f}, {movement_direction[1]:.1f})")
        elif args.movement_pattern == 'backward':
            base_direction = gait.DIRECTION_MAP['backward']
            movement_direction = (base_direction[0] * args.movement_speed, base_direction[1] * args.movement_speed)
            print(f"  Movement direction: Backward ({movement_direction[0]:.1f}, {movement_direction[1]:.1f})")
        elif args.movement_pattern == 'left':
            base_direction = gait.DIRECTION_MAP['left']
            movement_direction = (base_direction[0] * args.movement_speed, base_direction[1] * args.movement_speed)
            print(f"  Movement direction: Left ({movement_direction[0]:.1f}, {movement_direction[1]:.1f})")
        elif args.movement_pattern == 'right':
            base_direction = gait.DIRECTION_MAP['right']
            movement_direction = (base_direction[0] * args.movement_speed, base_direction[1] * args.movement_speed)
            print(f"  Movement direction: Right ({movement_direction[0]:.1f}, {movement_direction[1]:.1f})")
        elif args.movement_pattern == 'diagonal-fr':
            base_direction = gait.DIRECTION_MAP['diagonal-fr']
            movement_direction = (base_direction[0] * args.movement_speed, base_direction[1] * args.movement_speed)
            print(f"  Movement direction: Diagonal FR ({movement_direction[0]:.1f}, {movement_direction[1]:.1f})")
        elif args.movement_pattern == 'diagonal-fl':
            base_direction = gait.DIRECTION_MAP['diagonal-fl']
            movement_direction = (base_direction[0] * args.movement_speed, base_direction[1] * args.movement_speed)
            print(f"  Movement direction: Diagonal FL ({movement_direction[0]:.1f}, {movement_direction[1]:.1f})")
        elif args.movement_pattern == 'diagonal-br':
            base_direction = gait.DIRECTION_MAP['diagonal-br']
            movement_direction = (base_direction[0] * args.movement_speed, base_direction[1] * args.movement_speed)
            print(f"  Movement direction: Diagonal BR ({movement_direction[0]:.1f}, {movement_direction[1]:.1f})")
        elif args.movement_pattern == 'diagonal-bl':
            base_direction = gait.DIRECTION_MAP['diagonal-bl']
            movement_direction = (base_direction[0] * args.movement_speed, base_direction[1] * args.movement_speed)
            print(f"  Movement direction: Diagonal BL ({movement_direction[0]:.1f}, {movement_direction[1]:.1f})")
        elif args.movement_pattern == 'rotation':
            rotation_speed = args.rotation_speed
            print(f"  Rotation speed: {rotation_speed:.1f}")
        
        # Set the movement direction and rotation
        gait.set_direction(movement_direction, rotation_speed)
        
        # Start the gait generator with the selected gait
        print(f"\nStarting {args.gait} gait with circle-based targeting...")
        hexapod.gait_generator.start(gait)
        
        # Let it run for specified duration
        print(f"Running gait for {args.duration} seconds...")
        time.sleep(args.duration)
        
        # Stop the gait generator
        print("Stopping gait...")
        hexapod.gait_generator.stop()
        
        # Move back to home position
        print("Moving back to home position...")
        hexapod.move_to_position(PredefinedPosition.UPRIGHT)
        hexapod.wait_until_motion_complete()
        
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt, stopping...")
        hexapod.gait_generator.stop()
        hexapod.move_to_position(PredefinedPosition.UPRIGHT)
        hexapod.wait_until_motion_complete()
    except Exception as e:
        print(f"\nError: {e}")
        hexapod.gait_generator.stop()
        hexapod.move_to_position(PredefinedPosition.UPRIGHT)
        hexapod.wait_until_motion_complete()
    finally:
        # Deactivate all servos
        print("Deactivating servos...")
        hexapod.move_to_position(PredefinedPosition.UPRIGHT)
        hexapod.wait_until_motion_complete()
        hexapod.deactivate_all_servos()

def test_circle_projection(step_radius=40.0):
    """Test the circle projection function independently."""
    print(f"\n=== Testing Circle Projection Function (radius = {step_radius}mm) ===")
    
    # Import the gait classes to test the projection function
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
    from robot.gait_generator import TripodGait, Vector2D
    from robot.hexapod import Hexapod
    from pathlib import Path
    
    # Create a mock hexapod for testing
    config_path = Path('src/robot/config/hexapod_config.yaml')
    calibration_path = Path('src/robot/config/calibration.json')
    
    try:
        hexapod = Hexapod(config_path=config_path, calibration_data_path=calibration_path)
        gait = TripodGait(hexapod, step_radius=step_radius)
        
        # Test cases
        test_cases = [
            (Vector2D(0, 0), Vector2D(1, 0), "Origin to right"),
            (Vector2D(0, 0), Vector2D(0, 1), "Origin to up"),
            (Vector2D(0, 0), Vector2D(0.707, 0.707), "Origin to diagonal Forward-Right"),
            (Vector2D(0, 0), Vector2D(0.707, -0.707), "Origin to diagonal Forward-Left"),
            (Vector2D(0, 0), Vector2D(-0.707, 0.707), "Origin to diagonal Backward-Right"),
            (Vector2D(0, 0), Vector2D(-0.707, -0.707), "Origin to diagonal Backward-Left"),
            (Vector2D(step_radius/2, 0), Vector2D(1, 0), f"Half radius ({step_radius/2}mm) to right"),
            (Vector2D(0, step_radius/2), Vector2D(0, 1), f"Half radius ({step_radius/2}mm) to up"),
            (Vector2D(step_radius/2, step_radius/2), Vector2D(1, 0), f"Diagonal point ({step_radius/2},{step_radius/2}) to right"),
        ]
        
        for origin, direction, description in test_cases:
            projected = gait.project_point_to_circle(step_radius, origin, direction)
            distance = projected.magnitude()
            print(f"{description}: Origin{origin.to_tuple()} + Direction{direction.to_tuple()} -> Projected{projected.to_tuple()} (distance: {distance:.1f})")
            
            # Verify the projection is on the circle
            if abs(distance - step_radius) < 0.1:
                print(f"  ✓ Projection is on circle boundary")
            else:
                print(f"  ✗ Projection is NOT on circle boundary (expected {step_radius}, got {distance:.1f})")
        
    except Exception as e:
        print(f"Error testing circle projection: {e}")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test circle-based gait patterns for the hexapod robot.')
    parser.add_argument('--gait', type=str, choices=['tripod', 'wave'], default='tripod',
                      help='Type of gait to test (tripod or wave)')
    parser.add_argument('--duration', type=float, default=10.0,
                      help='Duration to run the gait in seconds')
    parser.add_argument('--step-radius', type=float, default=40.0,
                      help='Radius of the step circle in mm')
    parser.add_argument('--leg-lift-distance', type=float, default=30.0,
                      help='Distance to lift leg during swing phase (mm)')
    parser.add_argument('--leg-lift-incline', type=float, default=2.0,
                      help='Incline ratio for leg lift (mm/degree)')
    parser.add_argument('--stance-height', type=float, default=0.0,
                      help='Height of stance legs (mm), 0.0 = reference position, positive = lower legs (raise body)')
    parser.add_argument('--dwell-time', type=float, default=0.5,
                      help='Time to spend in each phase (seconds)')
    parser.add_argument('--stability-threshold', type=float, default=0.2,
                      help='Maximum allowed IMU deviation for stability check')
    parser.add_argument('--movement-pattern', type=str, 
                      choices=['forward', 'backward', 'left', 'right', 'diagonal-fr', 'diagonal-fl', 'diagonal-br', 'diagonal-bl', 'rotation'],
                      default='forward',
                      help='Movement pattern to test')
    parser.add_argument('--movement-speed', type=float, default=1.0,
                      help='Movement speed multiplier (0.0 to 1.0)')
    parser.add_argument('--rotation-speed', type=float, default=1.0,
                      help='Rotation speed multiplier (-1.0 to 1.0)')
    parser.add_argument('--test-projection', action='store_true',
                      help='Run circle projection test before main test')
    args = parser.parse_args()

    # Run circle projection test if requested
    if args.test_projection:
        test_circle_projection(args.step_radius)
        print("Projection test completed. Skipping main test.")
    else:
        # Run the main test
        main(args) 