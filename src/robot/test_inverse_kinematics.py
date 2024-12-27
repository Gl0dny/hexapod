import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from robot import Hexapod

def main():
    hexapod = Hexapod()

    # # Define target positions for each leg
    # positions = [
    #     (100.0,  50.0, -50.0),  # Leg 0
    #     (100.0, -50.0, -50.0),  # Leg 1
    #     (80.0,  60.0, -50.0),   # Leg 2
    #     (80.0, -60.0, -50.0),   # Leg 3
    #     (60.0,  70.0, -50.0),   # Leg 4
    #     (60.0, -70.0, -50.0),   # Leg 5
    # ]

    # # Test move_all_legs method
    # hexapod.move_all_legs(positions)
    # print("Moved all legs to initial positions.")

    # Test move_leg method with example values
    leg_index = 0
    new_position = (-25.0, 0.0, 0.0)
    hexapod.move_leg(leg_index, *new_position)
    print(f"Moved leg {leg_index} to position {new_position}")

if __name__ == '__main__':
    main()