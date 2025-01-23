import sys
import os
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from robot.hexapod import Hexapod

def main():
    config_path = Path('../../src/robot/config/hexapod_config.yaml')
    calibration_data_path = Path('../../src/robot/config/calibration.json')
    hexapod = Hexapod(config_path=config_path, calibration_data_path=calibration_data_path)
    
    # Example 1: Pure Yaw rotation (10 degrees)
    print("Example 1 - Yaw Rotation (10°):")
    global_deltas = hexapod.compute_body_inverse_kinematics(yaw=10)
    local_deltas = hexapod.transform_body_to_leg_frames(global_deltas)
    print("Global Deltas:")
    print(global_deltas)
    print("Local Deltas:")
    print(local_deltas)
    
    # Move legs to new positions based on deltas
    target_positions = [
        (
            current_x + delta_x,
            current_y + delta_y,
            current_z + delta_z
        )
        for (current_x, current_y, current_z), (delta_x, delta_y, delta_z) in zip(hexapod.current_leg_positions, global_deltas)
    ]
    hexapod.move_all_legs(target_positions)
    
    # Example 2: Combined movement with your Excel parameters
    print("\nExample 2 - Combined Transformation (ty=10, roll=10°):")
    global_deltas = hexapod.compute_body_inverse_kinematics(ty=10, roll=10)
    local_deltas = hexapod.transform_body_to_leg_frames(global_deltas)
    print("Global Deltas:")
    print(global_deltas)
    print("Local Deltas:")
    print(local_deltas)
    
    # Move legs to new positions based on deltas
    target_positions = [
        (
            current_x + delta_x,
            current_y + delta_y,
            current_z + delta_z
        )
        for (current_x, current_y, current_z), (delta_x, delta_y, delta_z) in zip(hexapod.current_leg_positions, global_deltas)
    ]
    hexapod.move_all_legs(target_positions)
    
    # Example 3: Pure translation
    print("\nExample 3 - Pure Translation (tx=10):")
    global_deltas = hexapod.compute_body_inverse_kinematics(tx=0)
    local_deltas = hexapod.transform_body_to_leg_frames(global_deltas)
    print("Global Deltas:")
    print(global_deltas)
    print("Local Deltas:")
    print(local_deltas)
    
    # Move legs to new positions based on deltas
    target_positions = [
        (
            current_x + delta_x,
            current_y + delta_y,
            current_z + delta_z
        )
        for (current_x, current_y, current_z), (delta_x, delta_y, delta_z) in zip(hexapod.current_leg_positions, global_deltas)
    ]
    hexapod.move_all_legs(target_positions)

if __name__ == '__main__':
    main()
