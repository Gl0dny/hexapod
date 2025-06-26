#!/usr/bin/env python3
import sys
import os
import time
import argparse
import threading
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from robot.hexapod import Hexapod, PredefinedPosition, PredefinedAnglePosition
from robot.gait_generator import TripodGait, WaveGait, Vector2D, Vector3D

def execute_waypoint_movement(hexapod, leg_index, waypoints, description, verbose=False):
    """Execute movement through a series of waypoints."""
    print(f"\nExecuting {description} movement through {len(waypoints)} waypoints...")
    
    for i, waypoint in enumerate(waypoints):
        print(f"  Waypoint {i + 1}/{len(waypoints)}: {waypoint.to_tuple()}")
        
        if verbose:
            print(f"    X: {waypoint.x:.2f}mm, Y: {waypoint.y:.2f}mm, Z: {waypoint.z:.2f}mm")
        
        try:
            hexapod.move_leg(leg_index, waypoint.x, waypoint.y, waypoint.z)
            hexapod.wait_until_motion_complete()
            time.sleep(0.5)  # Delay between waypoints based on hexapod speed/accel
            
            print(f"    Moved successfully")
                
        except Exception as e:
            print(f"    Error moving to waypoint {i + 1}: {e}")
            print(f"    Attempting to return to safe position...")
            hexapod.move_to_position(PredefinedPosition.UPRIGHT)
            hexapod.wait_until_motion_complete()
            raise e
    
    print(f"  Completed {description} movement")

def test_single_leg_movement():
    """Test individual leg movement using circle-based targeting."""
    print("\n=== Testing Single Leg Movement ===")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test individual leg movement with circle-based targeting.')
    parser.add_argument('--leg', type=int, choices=[0, 1, 2, 3, 4, 5], default=0,
                      help='Leg index to test (0-5)')
    parser.add_argument('--movement-direction', type=str, 
                      choices=['forward', 'backward', 'left', 'right', 'diagonal-fr', 'diagonal-fl', 'diagonal-br', 'diagonal-bl', 'rotation'],
                      default='forward',
                      help='Movement direction to test')
    parser.add_argument('--step-radius', type=float, default=40.0,
                      help='Radius of the step circle in mm')
    parser.add_argument('--leg-lift-distance', type=float, default=30.0,
                      help='Distance to lift leg during swing phase (mm)')
    parser.add_argument('--stance-height', type=float, default=0.0,
                      help='Height of stance legs (mm), 0.0 = reference position, positive = lower legs (raise body)')
    parser.add_argument('--movement-speed', type=float, default=1,
                      help='Movement speed multiplier (0.0 to 1.0)')
    parser.add_argument('--rotation-speed', type=float, default=1,
                      help='Rotation speed multiplier (-1.0 to 1.0)')
    parser.add_argument('--cycles', type=int, default=1,
                      help='Number of movement cycles to perform')
    parser.add_argument('--dwell-time', type=float, default=2.0,
                      help='Time to spend in each phase (seconds)')
    parser.add_argument('--verbose', action='store_true',
                      help='Enable verbose debugging output')
    args = parser.parse_args()

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
        
        # Create gait instance for testing
        gait = TripodGait(
            hexapod,
            step_radius=args.step_radius,
            leg_lift_distance=args.leg_lift_distance,
            stance_height=args.stance_height,
            dwell_time=args.dwell_time
        )
        
        print(f"Testing leg {args.leg} with {args.movement_direction} movement")
        print(f"Step radius: {gait.step_radius}mm")
        print(f"Leg lift distance: {gait.leg_lift_distance}mm")
        print(f"Stance height: {gait.stance_height}mm")
        print(f"Movement speed: {args.movement_speed}")
        print(f"Rotation speed: {args.rotation_speed}")
        print(f"Cycles: {args.cycles}")
        print(f"Verbose mode: {args.verbose}")
        
        # Set movement direction
        movement_direction = (0.0, 0.0)
        rotation_speed = 0.0
        
        if args.movement_direction == 'forward':
            base_direction = gait.DIRECTION_MAP['forward']
            movement_direction = (base_direction[0] * args.movement_speed, base_direction[1] * args.movement_speed)
        elif args.movement_direction == 'backward':
            base_direction = gait.DIRECTION_MAP['backward']
            movement_direction = (base_direction[0] * args.movement_speed, base_direction[1] * args.movement_speed)
        elif args.movement_direction == 'left':
            base_direction = gait.DIRECTION_MAP['left']
            movement_direction = (base_direction[0] * args.movement_speed, base_direction[1] * args.movement_speed)
        elif args.movement_direction == 'right':
            base_direction = gait.DIRECTION_MAP['right']
            movement_direction = (base_direction[0] * args.movement_speed, base_direction[1] * args.movement_speed)
        elif args.movement_direction == 'diagonal-fr':
            base_direction = gait.DIRECTION_MAP['diagonal-fr']
            movement_direction = (base_direction[0] * args.movement_speed, base_direction[1] * args.movement_speed)
        elif args.movement_direction == 'diagonal-fl':
            base_direction = gait.DIRECTION_MAP['diagonal-fl']
            movement_direction = (base_direction[0] * args.movement_speed, base_direction[1] * args.movement_speed)
        elif args.movement_direction == 'diagonal-br':
            base_direction = gait.DIRECTION_MAP['diagonal-br']
            movement_direction = (base_direction[0] * args.movement_speed, base_direction[1] * args.movement_speed)
        elif args.movement_direction == 'diagonal-bl':
            base_direction = gait.DIRECTION_MAP['diagonal-bl']
            movement_direction = (base_direction[0] * args.movement_speed, base_direction[1] * args.movement_speed)
        elif args.movement_direction == 'rotation':
            rotation_speed = args.rotation_speed
        
        print(f"Movement direction vector: {movement_direction}")
        print(f"Rotation speed: {rotation_speed}")
        
        gait.set_direction(movement_direction, rotation_speed)
        
        # Test individual leg movement
        print(f"\n=== Testing Leg {args.leg} Movement ===")
        
        for cycle in range(args.cycles):
            print(f"\n--- Cycle {cycle + 1}/{args.cycles} ---")
            
            # Get current position
            current_pos = Vector3D(*hexapod.current_leg_positions[args.leg])
            print(f"Current position: {current_pos.to_tuple()}")
            
            if args.verbose:
                print(f"  Current X: {current_pos.x:.2f}mm")
                print(f"  Current Y: {current_pos.y:.2f}mm")
                print(f"  Current Z: {current_pos.z:.2f}mm")
            
            # Calculate swing target with detailed debugging
            print(f"\nCalculating swing target for leg {args.leg}...")
            if args.verbose:
                print(f"  Leg mounting angle: {gait.leg_mount_angles[args.leg]}°")
                print(f"  Direction input: {gait.direction_input.to_tuple()}")
                print(f"  Rotation input: {gait.rotation_input}")
            
            swing_target = gait.calculate_leg_target(args.leg, is_swing=True)
            print(f"Swing target: {swing_target.to_tuple()}")
            
            if args.verbose:
                print(f"  Swing X: {swing_target.x:.2f}mm")
                print(f"  Swing Y: {swing_target.y:.2f}mm")
                print(f"  Swing Z: {swing_target.z:.2f}mm")
                print(f"  Swing distance from current: {(swing_target - current_pos).magnitude():.2f}mm")
            
            # Calculate stance target with detailed debugging
            print(f"\nCalculating stance target for leg {args.leg}...")
            stance_target = gait.calculate_leg_target(args.leg, is_swing=False)
            print(f"Stance target: {stance_target.to_tuple()}")
            
            if args.verbose:
                print(f"  Stance X: {stance_target.x:.2f}mm")
                print(f"  Stance Y: {stance_target.y:.2f}mm")
                print(f"  Stance Z: {stance_target.z:.2f}mm")
                print(f"  Stance distance from current: {(stance_target - current_pos).magnitude():.2f}mm")
            
            # Check if targets are within reachable limits
            print(f"\nChecking target reachability...")
            
            # Get leg parameters for limit checking
            coxa_length = hexapod.coxa_params['length']
            femur_length = hexapod.femur_params['length']
            tibia_length = hexapod.tibia_params['length']
            max_reach = coxa_length + femur_length + tibia_length
            
            print(f"  Leg dimensions:")
            print(f"    Coxa length: {coxa_length}mm")
            print(f"    Femur length: {femur_length}mm")
            print(f"    Tibia length: {tibia_length}mm")
            print(f"    Max theoretical reach: {max_reach}mm")
            
            # Calculate actual reach needed
            swing_reach_needed = swing_target.magnitude()
            stance_reach_needed = stance_target.magnitude()
            
            print(f"  Reach analysis:")
            print(f"    Swing reach needed: {swing_reach_needed:.2f}mm")
            print(f"    Stance reach needed: {stance_reach_needed:.2f}mm")
            print(f"    Swing reachable: {'✓' if swing_reach_needed <= max_reach else '✗'}")
            print(f"    Stance reachable: {'✓' if stance_reach_needed <= max_reach else '✗'}")
            
            # If targets are too far, scale them down
            if swing_reach_needed > max_reach:
                print(f"  WARNING: Swing target too far! Scaling down...")
                scale_factor = max_reach / swing_reach_needed * 0.8  # 80% of max reach for safety
                swing_target = swing_target * scale_factor
                print(f"  Scaled swing target: {swing_target.to_tuple()}")
            
            if stance_reach_needed > max_reach:
                print(f"  WARNING: Stance target too far! Scaling down...")
                scale_factor = max_reach / stance_reach_needed * 0.8  # 80% of max reach for safety
                stance_target = stance_target * scale_factor
                print(f"  Scaled stance target: {stance_target.to_tuple()}")
            
            # Calculate paths with detailed debugging
            print(f"\nCalculating paths for leg {args.leg}...")
            gait.calculate_leg_path(args.leg, swing_target, is_swing=True)
            swing_path = gait.leg_paths[args.leg]
            print(f"Swing path has {len(swing_path.waypoints)} waypoints:")
            for i, waypoint in enumerate(swing_path.waypoints):
                print(f"  Waypoint {i}: {waypoint.to_tuple()}")
                if args.verbose:
                    print(f"    X: {waypoint.x:.2f}mm, Y: {waypoint.y:.2f}mm, Z: {waypoint.z:.2f}mm")
            
            gait.calculate_leg_path(args.leg, stance_target, is_swing=False)
            stance_path = gait.leg_paths[args.leg]
            print(f"Stance path has {len(stance_path.waypoints)} waypoints:")
            for i, waypoint in enumerate(stance_path.waypoints):
                print(f"  Waypoint {i}: {waypoint.to_tuple()}")
                if args.verbose:
                    print(f"    X: {waypoint.x:.2f}mm, Y: {waypoint.y:.2f}mm, Z: {waypoint.z:.2f}mm")
            
            # Execute swing movement through waypoints
            try:
                execute_waypoint_movement(hexapod, args.leg, swing_path.waypoints, "swing", args.verbose)
            except Exception as e:
                print(f"✗ Error during swing movement: {e}")
                continue
            
            # Wait
            print(f"  Waiting {args.dwell_time}s...")
            time.sleep(args.dwell_time)
            
            # Execute stance movement through waypoints
            try:
                execute_waypoint_movement(hexapod, args.leg, stance_path.waypoints, "stance", args.verbose)
            except Exception as e:
                print(f"  ✗ Error moving to stance position: {e}")
                print(f"  Attempting to return to safe position...")
                hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
                hexapod.wait_until_motion_complete()
                continue
            
            # Wait
            print(f"  Waiting {args.dwell_time}s...")
            time.sleep(args.dwell_time)
        
        # Return to home position
        print(f"\nReturning leg {args.leg} to home position...")
        hexapod.move_to_position(PredefinedPosition.UPRIGHT)
        hexapod.wait_until_motion_complete()
        print(f"✓ Returned to home position successfully")
        
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt, stopping...")
        hexapod.move_to_position(PredefinedPosition.UPRIGHT)
        hexapod.wait_until_motion_complete()
    except Exception as e:
        print(f"\nError: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        hexapod.move_to_position(PredefinedPosition.UPRIGHT)
        hexapod.wait_until_motion_complete()
    finally:
        # Deactivate all servos
        print("Deactivating servos...")
        hexapod.move_to_position(PredefinedPosition.UPRIGHT)
        hexapod.wait_until_motion_complete()
        hexapod.deactivate_all_servos()

def test_leg_workspace_analysis():
    """Analyze the workspace of a single leg using circle-based targeting."""
    print("\n=== Testing Leg Workspace Analysis ===")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Analyze leg workspace with circle-based targeting.')
    parser.add_argument('--leg', type=int, choices=[0, 1, 2, 3, 4, 5], default=0,
                      help='Leg index to analyze (0-5)')
    parser.add_argument('--step-radius', type=float, default=30.0,  # Reduced for safety
                      help='Radius of the step circle in mm')
    parser.add_argument('--stance-height', type=float, default=35.0,
                      help='Height of stance legs above ground (mm)')
    parser.add_argument('--verbose', action='store_true',
                      help='Enable verbose debugging output')
    args = parser.parse_args()

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
        
        # Create gait instance for analysis
        gait = TripodGait(
            hexapod,
            step_radius=args.step_radius,
            stance_height=args.stance_height
        )
        
        print(f"Analyzing workspace for leg {args.leg}")
        print(f"Step radius: {gait.step_radius}mm")
        print(f"Stance height: {gait.stance_height}mm")
        print(f"Leg mounting angle: {gait.leg_mount_angles[args.leg]}°")
        
        # Get leg parameters for limit checking
        coxa_length = hexapod.coxa_params['length']
        femur_length = hexapod.femur_params['length']
        tibia_length = hexapod.tibia_params['length']
        max_reach = coxa_length + femur_length + tibia_length
        
        print(f"\nLeg physical parameters:")
        print(f"  Coxa length: {coxa_length}mm")
        print(f"  Femur length: {femur_length}mm")
        print(f"  Tibia length: {tibia_length}mm")
        print(f"  Max theoretical reach: {max_reach}mm")
        print(f"  Safe reach (80%): {max_reach * 0.8:.1f}mm")
        
        # Test different movement directions
        directions = [
            ((0.5, 0.0), "Forward (50%)"),
            ((-0.5, 0.0), "Backward (50%)"),
            ((0.0, 0.5), "Right (50%)"),
            ((0.0, -0.5), "Left (50%)"),
            ((0.35, 0.35), "Diagonal Forward-Right (50%)"),
            ((-0.35, 0.35), "Diagonal Backward-Right (50%)"),
            ((0.35, -0.35), "Diagonal Forward-Left (50%)"),
            ((-0.35, -0.35), "Diagonal Backward-Left (50%)"),
        ]
        
        print(f"\n--- Workspace Analysis for Leg {args.leg} ---")
        
        for direction, name in directions:
            print(f"\n{name} movement:")
            print(f"  Direction vector: {direction}")
            
            # Test swing target
            gait.set_direction(direction, 0.0)
            swing_target = gait.calculate_leg_target(args.leg, is_swing=True)
            print(f"  Swing target: {swing_target.to_tuple()}")
            
            # Test stance target
            stance_target = gait.calculate_leg_target(args.leg, is_swing=False)
            print(f"  Stance target: {stance_target.to_tuple()}")
            
            # Calculate distance moved
            current_pos = Vector3D(*hexapod.current_leg_positions[args.leg])
            swing_distance = (swing_target - current_pos).magnitude()
            stance_distance = (stance_target - current_pos).magnitude()
            print(f"  Swing distance: {swing_distance:.1f}mm")
            print(f"  Stance distance: {stance_distance:.1f}mm")
            
            # Check reachability
            swing_reachable = swing_distance <= max_reach * 0.8
            stance_reachable = stance_distance <= max_reach * 0.8
            print(f"  Swing reachable: {'✓' if swing_reachable else '✗'}")
            print(f"  Stance reachable: {'✓' if stance_reachable else '✗'}")
            
            if args.verbose:
                print(f"    Swing X: {swing_target.x:.2f}mm, Y: {swing_target.y:.2f}mm, Z: {swing_target.z:.2f}mm")
                print(f"    Stance X: {stance_target.x:.2f}mm, Y: {stance_target.y:.2f}mm, Z: {stance_target.z:.2f}mm")
        
        # Test rotation
        print(f"\nRotation analysis:")
        for rotation in [-0.5, -0.25, 0.25, 0.5]:
            gait.set_direction((0.0, 0.0), rotation)
            swing_target = gait.calculate_leg_target(args.leg, is_swing=True)
            stance_target = gait.calculate_leg_target(args.leg, is_swing=False)
            swing_distance = swing_target.magnitude()
            stance_distance = stance_target.magnitude()
            print(f"  Rotation {rotation:+.2f}: Swing{swing_target.to_tuple()} ({swing_distance:.1f}mm), Stance{stance_target.to_tuple()} ({stance_distance:.1f}mm)")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Deactivate all servos
        print("Deactivating servos...")
        hexapod.move_to_position(PredefinedPosition.UPRIGHT)
        hexapod.wait_until_motion_complete()
        hexapod.deactivate_all_servos()

def test_circle_projection_visualization():
    """Visualize circle projection for different scenarios."""
    print("\n=== Testing Circle Projection Visualization ===")
    
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
        gait = TripodGait(hexapod, step_radius=30.0)  # Reduced for safety
        
        print("Circle projection visualization (radius = 30mm):")
        
        # Test different starting points and directions
        test_scenarios = [
            # (origin, direction, description)
            (Vector2D(0, 0), Vector2D(1, 0), "Origin → Forward"),
            (Vector2D(0, 0), Vector2D(0, 1), "Origin → Right"),
            (Vector2D(0, 0), Vector2D(1, 1), "Origin → Diagonal"),
            (Vector2D(30, 0), Vector2D(1, 0), "Half radius right → Forward"),
            (Vector2D(0, 30), Vector2D(0, 1), "Half radius up → Right"),
            (Vector2D(30, 30), Vector2D(1, 0), "Diagonal point → Forward"),
            (Vector2D(60, 0), Vector2D(1, 0), "On circle → Forward"),
            (Vector2D(80, 0), Vector2D(-1, 0), "Outside circle → Backward"),
        ]
        
        for origin, direction, description in test_scenarios:
            projected = gait.project_point_to_circle(30.0, origin, direction)
            distance = projected.magnitude()
            print(f"\n{description}:")
            print(f"  Origin: {origin.to_tuple()}")
            print(f"  Direction: {direction.to_tuple()}")
            print(f"  Projected: {projected.to_tuple()}")
            print(f"  Distance: {distance:.1f}mm")
            
            # Verify the projection is on the circle
            if abs(distance - 30.0) < 0.1:
                print(f"  ✓ Projection is on circle boundary")
            else:
                print(f"  ✗ Projection is NOT on circle boundary (expected 30.0, got {distance:.1f})")
        
    except Exception as e:
        print(f"Error testing circle projection: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to run the single leg tests."""
    parser = argparse.ArgumentParser(description='Test individual leg movement and workspace analysis.')
    parser.add_argument('--test', type=str, 
                      choices=['movement', 'workspace', 'projection', 'all'],
                      default='all',
                      help='Type of test to run')
    args, remaining_args = parser.parse_known_args()
    
    # Set sys.argv to remaining args for sub-parsers
    sys.argv = [sys.argv[0]] + remaining_args
    
    if args.test == 'movement' or args.test == 'all':
        test_single_leg_movement()
    
    if args.test == 'workspace' or args.test == 'all':
        test_leg_workspace_analysis()
    
    if args.test == 'projection' or args.test == 'all':
        test_circle_projection_visualization()

if __name__ == "__main__":
    main() 