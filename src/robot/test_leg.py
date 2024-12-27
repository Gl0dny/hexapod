import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from robot import Leg
from maestro import MaestroUART

def main():
    # Initialize controller
    controller = MaestroUART()

    # Define joint parameters
    coxa_params = {
        'length': 50,
        'channel': 0,
        'angle_min': -45,
        'angle_max': 45
    }
    femur_params = {
        'length': 100,
        'channel': 1,
        'angle_min': -45,
        'angle_max': 45
    }
    tibia_params = {
        'length': 150,
        'channel': 2,
        'angle_min': -30,
        'angle_max': 45
    }

    # Define end effector offset
    end_effector_offset = {
        'x': 0,  # Set appropriate values
        'y': 0,
        'z': 0
    }

    # Initialize Leg
    leg = Leg(coxa_params, femur_params, tibia_params, controller, end_effector_offset)

    # Set fixed angles
    theta1 = 0     # Coxa angle in degrees
    theta2 = 0    # Femur angle in degrees (reversed Z axis)
    theta3 = 0     # Tibia angle in degrees

    # Apply fixed angles
    leg.coxa.set_angle(theta1, speed=32, accel=5)
    leg.femur.set_angle(-theta2, speed=32, accel=5)
    leg.tibia.set_angle(theta3, speed=32, accel=5)

    print(f"Set angles to Coxa: {theta1}°, Femur: {theta2}°, Tibia: {theta3}°")

    # controller.go_home()

if __name__ == "__main__":
    main()