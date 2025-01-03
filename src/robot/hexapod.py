import os
import sys
from typing import Optional, List, Tuple, Dict
import threading
import time
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
            'angle_limit_min': None,
            'angle_limit_max': None,
            'z_offset': 22.5
        }
        femur_params: Dict[str, float] = {
            'length': 52.5,
            'angle_min': -45,
            'angle_max': 45,
            'angle_limit_min': None,
            'angle_limit_max': None,
            'invert': True
        }
        tibia_params: Dict[str, float] = {
            'length': 140.0,
            'angle_min': -45,
            'angle_max': 45,
            'angle_limit_min': -35,
            'angle_limit_max': None,
            'x_offset': 22.5
        }

        self.end_effector_offset: Tuple[float, float, float] = (
            tibia_params['x_offset'],
            femur_params['length'] + coxa_params['length'],
            tibia_params['length'] + coxa_params['z_offset']
        )

        self.legs: List[Leg] = []

        coxa_channel_map = [0, 3, 6, 15, 18, 21]
        femur_channel_map = [1, 4, 7, 16, 19, 22]
        tibia_channel_map = [2, 5, 8, 17, 20, 23]

        for i in range(6):
            coxa_params['channel'] = coxa_channel_map[i]
            femur_params['channel'] = femur_channel_map[i]
            tibia_params['channel'] = tibia_channel_map[i]

            leg = Leg(coxa_params, femur_params, tibia_params, self.controller, self.end_effector_offset)
            self.legs.append(leg)

        self.leg_to_led: Dict[int, int] = {
            0: 2,
            1: 0,
            2: 10,
            3: 8,
            4: 6,
            5: 4
        }

        self.predefined_positions: Dict[str, List[Tuple[float, float, float]]] = {
            'zero': [
                (-25.0, 0.0, 0.0),
                (-25.0, 0.0, 0.0),
                (-25.0, 0.0, 0.0),
                (-25.0, 0.0, 0.0),
                (-25.0, 0.0, 0.0),
                (-25.0, 0.0, 0.0),
            ],
        }

        self.predefined_angle_positions: Dict[str, List[Tuple[float, float, float]]] = {
            'home': [
                (0.0, 35, -35),
                (0.0, 35, -35),
                (0.0, 35, -26),
                (0.0, 35, -35),
                (0.0, 35, -17.5),
                (0.0, 35, -35),
            ],
        }

        self.coxa_params = coxa_params
        self.femur_params = femur_params
        self.tibia_params = tibia_params

        self.calibration: Calibration = Calibration(self)
        self.calibration.load_calibration('/home/hexapod/hexapod/src/robot/calibration.json')

        self.current_leg_angles = list(self.predefined_angle_positions['home'])
        self.current_leg_positions = list(self.predefined_positions['zero'])

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
        # Store the new positions
        self.current_leg_positions[leg_index] = (x, y, z)

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

    def move_leg_to_position(self, leg_index: int, position_name: str, positions_dict: Optional[Dict[str, List[Tuple[float, float, float]]]] = None) -> None:
        print(f"Setting leg {leg_index} to position '{position_name}'")
        positions = positions_dict.get(position_name) if positions_dict else self.predefined_positions.get(position_name)
        if positions:
            x, y, z = positions[leg_index]
            self.move_leg(leg_index, x, y, z)
        else:
            available = list(positions_dict.keys()) if positions_dict else list(self.predefined_positions.keys())
            print(f"Error: Unknown position '{position_name}'. Available positions: {available}")

    def move_to_position(self, position_name: str, positions_dict: Optional[Dict[str, List[Tuple[float, float, float]]]] = None) -> None:
        """
        Move the hexapod to a predefined position using an external dictionary if provided.
        
        Args:
            position_name (str): Name of the predefined position.
            positions_dict (Dict[str, List[Tuple[float, float, float]]], optional): 
                External dictionary mapping position names to coordinate configurations.
                If not provided, uses self.predefined_positions.
        """
        print(f"Setting all legs to position '{position_name}'")
        positions = positions_dict.get(position_name) if positions_dict else self.predefined_positions.get(position_name)
        if positions:
            self.move_all_legs(positions)
        else:
            available = list(positions_dict.keys()) if positions_dict else list(self.predefined_positions.keys())
            print(f"Error: Unknown position '{position_name}'. Available positions: {available}")

    def move_leg_angles(
        self,
        leg_index: int,
        coxa_angle: float,
        femur_angle: float,
        tibia_angle: float,
        speed: Optional[int] = None,
        accel: Optional[int] = None
    ) -> None:
        if speed is None:
            speed = self.speed
        if accel is None:
            accel = self.accel

        self.legs[leg_index].move_to_angles(coxa_angle, femur_angle, tibia_angle, speed, accel)
        self.current_leg_angles[leg_index] = (coxa_angle, femur_angle, tibia_angle)
        
    def move_all_legs_angles(self, angles_list: List[Tuple[float, float, float]], speed: Optional[int] = None, accel: Optional[int] = None) -> None:
        if speed is None:
            speed = self.speed
        if accel is None:
            accel = self.accel
        for i, angles in enumerate(angles_list):
            c_angle, f_angle, t_angle = angles
            self.move_leg_angles(i, c_angle, f_angle, t_angle, speed, accel)

    def move_leg_to_angles_position(self, leg_index: int, position_name: str, positions_dict: Optional[Dict[str, List[Tuple[float, float, float]]]] = None) -> None:
        print(f"Setting leg {leg_index} to angles position '{position_name}'")
        if positions_dict and position_name in positions_dict:
            angles = positions_dict.get(position_name)
        else:
            angles = self.predefined_angle_positions.get(position_name)
        if angles:
            c_angle, f_angle, t_angle = angles[leg_index]
            self.move_leg_angles(leg_index, c_angle, f_angle, t_angle)
        else:
            available = list(positions_dict.keys()) if positions_dict else list(self.predefined_angle_positions.keys())
            print(f"Error: Unknown angles position '{position_name}'. Available angle positions: {available}")

    def move_to_angles_position(self, position_name: str, positions_dict: Optional[Dict[str, List[Tuple[float, float, float]]]] = None) -> None:
        """
        Move the hexapod to a predefined angle position using an external dictionary if provided.
        
        Args:
            position_name (str): Name of the predefined angle position.
            positions_dict (Dict[str, List[Tuple[float, float, float]]], optional): 
                External dictionary mapping position names to angle configurations.
                If not provided, uses self.predefined_angle_positions.
        """
        print(f"Setting all legs to angles position '{position_name}'")
        angles = positions_dict.get(position_name) if positions_dict else self.predefined_angle_positions.get(position_name)
        if angles:
            self.move_all_legs_angles(angles)
        else:
            available = list(positions_dict.keys()) if positions_dict else list(self.predefined_angle_positions.keys())
            print(f"Error: Unknown angles position '{position_name}'. Available angle positions: {available}")

    def get_moving_state(self) -> bool:
        """
        Returns the moving state of the hexapod by querying the Maestro controller.

        Returns:
            True: If at least one servo is still moving.
            False: If no servos are moving or failed to retrieve the moving state.
        """
        moving_state = self.controller.get_moving_state()
        if moving_state == 0x01:
            return True
        else:
            return False

    def wait_until_motion_complete(self, stop_event: Optional[threading.Event] = None) -> None:
        """
        Waits up to 1 second for the robot to start moving. This short wait is required
        due to the Maestro controller's response delay over UART. Then remains waiting
        until all servos have stopped or a stop event is set.

        Args:
            stop_event (threading.Event, optional): Event to signal stopping the wait.
        """
        start_time = time.time()
        # Wait for at most 1 second to see if the robot starts moving
        while (time.time() - start_time < 1) and not (stop_event and stop_event.is_set()):
            if self.get_moving_state():
                break
            if stop_event:
                stop_event.wait(timeout=0.1)
        if stop_event and stop_event.is_set():
            return
        # Wait until the robot stops the motion
        while not (stop_event.is_set() if stop_event else False):
            if not self.get_moving_state():
                break
            if stop_event:
                stop_event.wait(timeout=0.1)

if __name__ == '__main__':
    hexapod = Hexapod()

    # Move a single leg to a new predefined coordinate position
    # hexapod.move_leg_to_position(2, 'home')

    # Move all legs to a new predefined coordinate position
    # hexapod.move_to_position('home')

    # Move a single leg to a new predefined angle position
    # hexapod.move_leg_to_angles_position(5, 'rest')

    # Move all legs to a new predefined angle position
    hexapod.move_to_angles_position('home')

    # Move all servos to hardware home position saved in the controler
    # hexapod.controller.go_home()