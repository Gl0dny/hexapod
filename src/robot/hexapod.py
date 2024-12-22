import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from maestro import MaestroUART
from robot import Leg

class Hexapod:
    def __init__(self):
        """
        Represents the hexapod robot with six legs.
        Attributes:
            controller (MaestroUART): Serial controller for managing servo motors.
            speed (int): Default speed setting for servo movements.
            accel (int): Default acceleration setting for servo movements.
            legs (list): List of Leg instances representing each of the hexapod's legs.
            coxa_params (dict): Parameters for the coxa joint, including length, channel, angle limits, and servo settings.
            femur_params (dict): Parameters for the femur joint, including length, channel, angle limits, and servo settings.
            tibia_params (dict): Parameters for the tibia joint, including length, channel, angle limits, and servo settings.
            end_effector_offset (tuple): Default offset for the end effector position - (x,y,z).
        """
        self.controller = MaestroUART('/dev/ttyS0', 9600)
        
        self.speed = 32
        self.accel = 5

        self.end_effector_offset = (0.0, 0.0, 0.0)

        self.legs = []
        for i in range(6):
            coxa_params = {
                'length': 30.0,
                'channel': i * 3,
                'angle_min': -45,
                'angle_max': 45,
                'servo_min': 992 * 4,
                'servo_max': 2000 * 4
                
            }
            femur_params = {
                'length': 50.0,
                'channel': i * 3 + 1,
                'angle_min': -45,
                'angle_max': 45,
                'servo_min': 992 * 4,
                'servo_max': 2000 * 4
            }
            tibia_params = {
                'length': 80.0,
                'channel': i * 3 + 2,
                'angle_min': -45,
                'angle_max': 45,
                'servo_min': 992 * 4,
                'servo_max': 2000 * 4
            }
            leg = Leg(coxa_params, femur_params, tibia_params, self.controller, self.end_effector_offset)
            self.legs.append(leg)


    def move_leg(self, leg_index, x, y, z, speed=None, accel=None):
        """
        Command a leg to move to a position.

        Args:
            leg_index (int): Index of the leg (0-5).
            x, y, z (float): Target coordinates.
            speed (int, optional): Servo speed. Defaults to Hexapod's speed.
            accel (int, optional): Servo acceleration. Defaults to Hexapod's accel.
        """
        if speed is None:
            speed = self.speed
        if accel is None:
            accel = self.accel
        self.legs[leg_index].move_to(x, y, z, speed, accel)

    def move_all_legs(self, positions, speed=None, accel=None):
        """
        Command all legs to move to specified positions.

        Args:
            positions (list): List of (x, y, z) tuples.
            speed (int, optional): Servo speed. Defaults to Hexapod's speed.
            accel (int, optional): Servo acceleration. Defaults to Hexapod's accel.
        """
        if speed is None:
            speed = self.speed
        if accel is None:
            accel = self.accel
        for i, pos in enumerate(positions):
            x, y, z = pos
            self.move_leg(i, x, y, z, speed, accel)

    # Implement gait algorithms here

# Example usage
if __name__ == '__main__':
    hexapod = Hexapod()

    # Define target positions for each leg
    positions = [
        (100.0,  50.0, -50.0),  # Leg 0
        (100.0, -50.0, -50.0),  # Leg 1
        (80.0,  60.0, -50.0),   # Leg 2
        (80.0, -60.0, -50.0),   # Leg 3
        (60.0,  70.0, -50.0),   # Leg 4
        (60.0, -70.0, -50.0),   # Leg 5
    ]

    # Move all legs to their initial positions
    hexapod.move_all_legs(positions)

    # Implement gait control loops and additional functionality