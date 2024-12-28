import os
import sys
from typing import Optional, List, Tuple, Dict
import threading
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from maestro import MaestroUART
from robot import Leg, Calibration

class Hexapod:
    def __init__(self) -> None:
        """
        Represents the hexapod robot with six legs.

        Attributes:
            controller (MaestroUART): Serial controller for managing servo motors.
            speed (int): Default speed setting for servo movements.
            accel (int): Default acceleration setting for servo movements.
            legs (List[Leg]): List of Leg instances representing each of the hexapod's legs.
            coxa_params (Dict[str, float]): Parameters for the coxa joint, including length, channel, angle limits, and servo settings.
            femur_params (Dict[str, float]): Parameters for the femur joint, including length, channel, angle limits, and servo settings.
            tibia_params (Dict[str, float]): Parameters for the tibia joint, including length, channel, angle limits, and servo settings.
            end_effector_offset (Tuple[float, float, float]): Default offset for the end effector position - (x, y, z).
            leg_to_led (Dict[int, int]): Mapping from leg indices to LED indices.
            calibration (Calibration): Instance managing servo calibrations and related processes.
        """
        self.controller: MaestroUART = MaestroUART('/dev/ttyS0', 9600)
        
        self.speed: int = 32
        self.accel: int = 5

        coxa_params: Dict[str, float] = {
            'length': 27.5,
            'angle_min': -45,
            'angle_max': 45,
            'z_offset': 22.5
        }
        femur_params: Dict[str, float] = {
            'length': 52.5,
            'angle_min': -45,
            'angle_max': 45,
            'invert': True
        }
        tibia_params: Dict[str, float] = {
            'length': 140.0,
            'angle_min': -45,
            'angle_max': 45,
            'x_offset': 22.5
        }

        self.end_effector_offset: Tuple[float, float, float] = (
            tibia_params['x_offset'],
            femur_params['length'] + coxa_params['length'],
            tibia_params['length'] + coxa_params['z_offset']
        )

        self.legs: List[Leg] = []
        for i in range(6):
            coxa = coxa_params.copy()
            coxa['channel'] = i * 3
            femur = femur_params.copy()
            femur['channel'] = i * 3 + 1
            tibia = tibia_params.copy()
            tibia['channel'] = i * 3 + 2

            leg = Leg(coxa, femur, tibia, self.controller, self.end_effector_offset)
            self.legs.append(leg)

        self.leg_to_led: Dict[int, int] = {
            0: 2,
            1: 0,
            2: 4,
            3: 6,
            4: 8,
            5: 10
        }

        self.calibration: Calibration = Calibration(self)
        self.calibration.load_calibration()

    def calibrate_all_servos(self, stop_event: Optional[threading.Event] = None) -> None:
        """
        Calibrate all servo motors using the Calibration module.
        Sets each leg's status to 'calibrating' and updates to 'calibrated' once done.

        Args:
            stop_event (threading.Event, optional): Event to signal stopping the calibration process.
        """
        self.calibration.calibrate_all_servos(stop_event=stop_event)

    def move_leg(self, leg_index: int, x: float, y: float, z: float, speed: Optional[int] = None, accel: Optional[int] = None) -> None:
        """
        Move a specific leg to the given (x, y, z) coordinate.
        
        Args:
            leg_index (int): Index of the leg (0-5).
            x (float): Target x-coordinate.
            y (float): Target y-coordinate.
            z (float): Target z-coordinate.
            speed (int, optional): Overrides the default servo speed.
            accel (int, optional): Overrides the default servo acceleration.
        """
        if speed is None:
            speed = self.speed
        if accel is None:
            accel = self.accel
        self.legs[leg_index].move_to(x, y, z, speed, accel)

    def move_all_legs(self, positions: List[Tuple[float, float, float]], speed: Optional[int] = None, accel: Optional[int] = None) -> None:
        """
        Move all legs simultaneously to specified positions.
        
        Args:
            positions (List[Tuple[float, float, float]]): List of (x, y, z) tuples for each leg.
            speed (int, optional): Overrides default servo speed.
            accel (int, optional): Overrides default servo acceleration.
        """
        if speed is None:
            speed = self.speed
        if accel is None:
            accel = self.accel
        for i, pos in enumerate(positions):
            x, y, z = pos
            self.move_leg(i, x, y, z, speed, accel)

if __name__ == '__main__':
    # Calibrate hexapod
    hexapod = Hexapod()
    hexapod.calibrate_all_servos()