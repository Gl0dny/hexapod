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
            'angle_min': -30,
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

        # Define predefined positions as an instance attribute
        self.predefined_positions: Dict[str, List[Tuple[float, float, float]]] = {
            'home': [
                (-25.0, 0.0, 0.0),
                (-25.0, 0.0, 0.0),
                (-25.0, 0.0, 0.0),
                (-25.0, 0.0, 0.0),
                (-25.0, 0.0, 0.0),
                (-25.0, 0.0, 0.0),
            ],
            'sitting': [
                # ...positions for sitting...
            ],
            'edge': [
                # ...positions for edge...
            ],
        }

        self.predefined_positions.update({
            'tripod1': [
                (-30.0, 5.0, 0.0),
                (-25.0, -5.0, 10.0),
                (0.0, 0.0, 15.0),
                (-25.0, -10.0, 0.0),
                (-30.0, 10.0, 5.0),
                (0.0, 5.0, 5.0),
            ],
            'tripod2': [
                (-20.0, 0.0, 5.0),
                (-20.0, -5.0, 0.0),
                (-5.0, 10.0, 10.0),
                (-10.0, -5.0, 10.0),
                (-15.0, 0.0, 5.0),
                (0.0, 15.0, 0.0),
            ],
            # ...add other coordinate-based positions if needed...
        })

        self.predefined_angle_positions: Dict[str, List[Tuple[float, float, float]]] = {
            'rest': [
                (0.0, 0.0, 0.0),
                (0.0, 0.0, 0.0),
                (0.0, 0.0, 0.0),
                (0.0, 0.0, 0.0),
                (0.0, 0.0, 0.0),
                (0.0, 0.0, 0.0),
            ],
            # ...add more positions as needed...
        }

        self.predefined_angle_positions.update({
            'standing': [
                (5.0, -15.0, -70.0),
                (5.0, -15.0, -70.0),
                (5.0, -15.0, -70.0),
                (5.0, -15.0, -70.0),
                (5.0, -15.0, -70.0),
                (5.0, -15.0, -70.0),
            ],
            'crawl': [
                (10.0, -20.0, -60.0),
                (0.0, -20.0, -70.0),
                (-5.0, -15.0, -75.0),
                (0.0, -20.0, -70.0),
                (10.0, -15.0, -65.0),
                (5.0, -20.0, -70.0),
            ],
            # ...add more angle-based positions as needed...
        })

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

    def move_leg_angles(self, leg_index: int, coxa_angle: float, femur_angle: float, tibia_angle: float, speed: Optional[int] = None, accel: Optional[int] = None) -> None:
        if speed is None:
            speed = self.speed
        if accel is None:
            accel = self.accel
        self.legs[leg_index].move_to_angles(coxa_angle, femur_angle, tibia_angle, speed, accel)

    def move_all_legs_angles(self, angles_list: List[Tuple[float, float, float]], speed: Optional[int] = None, accel: Optional[int] = None) -> None:
        if speed is None:
            speed = self.speed
        if accel is None:
            accel = self.accel
        for i, angles in enumerate(angles_list):
            c_angle, f_angle, t_angle = angles
            self.move_leg_angles(i, c_angle, f_angle, t_angle, speed, accel)

    def move_to_position(self, position_name: str) -> None:
        """
        Move the hexapod to a predefined position.
        
        Args:
            position_name (str): Name of the predefined position.
        """
        positions = self.predefined_positions.get(position_name)
        if positions:
            self.move_all_legs(positions)
        else:
            print(f"Error: Unknown position '{position_name}'. Available positions: {list(self.predefined_positions.keys())}")

    def move_to_angles_position(self, position_name: str) -> None:
        angles = self.predefined_angle_positions.get(position_name)
        if angles:
            self.move_all_legs_angles(angles)
        else:
            print(f"Error: Unknown angles position '{position_name}'. Available angle positions: {list(self.predefined_angle_positions.keys())}")

    def move_leg_to_position(self, leg_index: int, position_name: str) -> None:
        positions = self.predefined_positions.get(position_name)
        if positions:
            x, y, z = positions[leg_index]
            self.move_leg(leg_index, x, y, z)
        else:
            print(f"Error: Unknown position '{position_name}'.")

    def move_leg_to_angles_position(self, leg_index: int, position_name: str) -> None:
        angles = self.predefined_angle_positions.get(position_name)
        if angles:
            c_angle, f_angle, t_angle = angles[leg_index]
            self.move_leg_angles(leg_index, c_angle, f_angle, t_angle)
        else:
            print(f"Error: Unknown angles position '{position_name}'.")

if __name__ == '__main__':
    hexapod = Hexapod()
    # Calibrate hexapod
    # hexapod.calibrate_all_servos()
    hexapod.move_to_position('home')
    # Move all legs to a new predefined coordinate position
    # hexapod.move_to_position('tripod1')
    # # Move all legs to a new predefined angle position
    # hexapod.move_to_angles_position('standing')
    # # Move a single leg to a new predefined coordinate position
    # hexapod.move_leg_to_position(2, 'tripod2')
    # # Move a single leg to a new predefined angle position
    # hexapod.move_leg_to_angles_position(4, 'crawl')