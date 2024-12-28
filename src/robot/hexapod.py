import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from maestro import MaestroUART
from robot import Leg, Calibration

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
            calibration (Calibration): Instance managing servo calibrations and related processes.
        """
        self.controller = MaestroUART('/dev/ttyS0', 9600)
        
        self.speed = 32
        self.accel = 5

        coxa_params = {
            'length': 27.5,
            'angle_min': -45,
            'angle_max': 45,
            'z_offset': 22.5
        }
        femur_params = {
            'length': 52.5,
            'angle_min': -45,
            'angle_max': 45,
            'invert': True
        }
        tibia_params = {
            'length': 140.0,
            'angle_min': -45,
            'angle_max': 45,
            'x_offset': 22.5
        }

        self.end_effector_offset = (
            tibia_params['x_offset'],
            femur_params['length']+coxa_params['length'],
            tibia_params['length']+coxa_params['z_offset']
        )

        self.legs = []
        for i in range(6):
            coxa = coxa_params.copy()
            coxa['channel'] = i * 3
            femur = femur_params.copy()
            femur['channel'] = i * 3 + 1
            tibia = tibia_params.copy()
            tibia['channel'] = i * 3 + 2

            leg = Leg(coxa, femur, tibia, self.controller, self.end_effector_offset)
            self.legs.append(leg)

        self.calibration = Calibration(self)
        self.calibration.load_calibration()

    def calibrate_all_servos(self):
        """
        Initiates the calibration of all servos.
        Updates leg statuses to "calibrating" during the process and "calibrated" upon completion.
        """
        self.calibration.calibrate_all_servos()

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
    # positions = [
    #     (100.0,  50.0, -50.0),  # Leg 0
    #     (100.0, -50.0, -50.0),  # Leg 1
    #     (80.0,  60.0, -50.0),   # Leg 2
    #     (80.0, -60.0, -50.0),   # Leg 3
    #     (60.0,  70.0, -50.0),   # Leg 4
    #     (60.0, -70.0, -50.0),   # Leg 5
    # ]

    # Start calibration
    hexapod.calibrate_all_servos()

    # Move all legs to their initial positions after calibration
    # hexapod.move_all_legs(positions)

    # Implement gait control loops and additional functionality