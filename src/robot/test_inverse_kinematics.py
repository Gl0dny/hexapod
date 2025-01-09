import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from robot import Hexapod

def main():
    hexapod = Hexapod()
    # hexapod.calibrate_all_servos()

    # Define target positions for each leg
    positions = [
        (-22.5,  0.0, 0.0),  # Leg 0
        (-22.5, 0.0, 0.0),  # Leg 1
        (-22.5,  0.0, 0.0),   # Leg 2
        (-22.5, 0.0, 0.0),   # Leg 3
        (-22.5,  0.0, 0.0),   # Leg 4
        (-25.5, 0.0, 0.0),   # Leg 5
    ]

    # # Test move_all_legs method
    hexapod.move_all_legs(positions)
    print("Moved all legs to initial positions.")

    # Test move_leg method with example values
    leg_index = 0
    new_position = (-22.5, 0.0, 0.0)
    hexapod.move_leg(leg_index, *new_position)
    print(f"Moved leg {leg_index} to position {new_position}")

    # Test forward kinematics
    leg = hexapod.legs[leg_index]
    # Assuming move_leg sets the angles, retrieve them
    coxa_angle, femur_angle, tibia_angle = leg.compute_inverse_kinematics(*new_position)
    foot_position = leg.compute_forward_kinematics(coxa_angle, femur_angle, tibia_angle)
    print(f"Forward kinematics result for leg {leg_index}: {foot_position}")

if __name__ == '__main__':
    main()