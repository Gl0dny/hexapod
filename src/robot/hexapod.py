import os
import sys
from typing import Optional, List, Tuple, Dict
import threading
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from maestro import MaestroUART
from robot import Leg, Calibration, Joint
from imu import Imu
from utils import map_range

class Hexapod:
    CONTROLLER_CHANNELS = 24
    
    def __init__(self) -> None:
        """
        Represents the hexapod robot with six legs.

        Attributes:
            controller (MaestroUART): Serial controller for managing servo motors.
            speed (int): Default speed setting for servo movements.
            accel (int): Default acceleration setting for servo movements.
            imu (Imu): Instance of the Imu class for imu sensor data.
            legs (List[Leg]): List of Leg instances representing each of the hexapod's legs.
            leg_to_led (Dict[int, int]): Mapping from leg indices to LED indices.
            coxa_params (Dict[str, float]): Parameters for the coxa joint, including length (mm), channel, angle limits (degrees), and servo settings.
            femur_params (Dict[str, float]): Parameters for the femur joint, including length (mm), channel, angle limits (degrees), and servo settings.
            tibia_params (Dict[str, float]): Parameters for the tibia joint, including length (mm), channel, angle limits (degrees), and servo settings.
            end_effector_offset (Tuple[float, float, float]): Default offset for the end effector position - (x, y, z) in mm.
            calibration (Calibration): Instance managing servo calibrations and related processes.
            predefined_positions (Dict[str, List[Tuple[float, float, float]]]): Predefined positions for the legs.
            predefined_angle_positions (Dict[str, List[Tuple[float, float, float]]]): Predefined angle positions for the legs.
            current_leg_angles (List[Tuple[float, float, float]]): Current angles of the legs.
            current_leg_positions (List[Tuple[float, float, float]]): Current positions of the legs.
        """
        self.controller: MaestroUART = MaestroUART('/dev/ttyS0', 9600)
        
        # Speed setting for the servo in percent. Speed unit - (0.25us/10ms).
        # The speed parameter can be set to a maximum value of 255, corresponding to a change of 63.75 μs every 10 ms.
        self.speed: int = 25
        # Acceleration setting for the servo percent. Acceleration units - (0.25us/10ms/80ms).
        # The maximum acceleration setting is 255, allowing the speed to change by 63.75 μs per 10 ms interval every 80 ms.
        self.accel: int = 10

        self.imu = Imu()

        coxa_params: Dict[str, float] = {
            'length': 27.5,  # mm
            'angle_min': -45,  # degrees
            'angle_max': 45,  # degrees
            'angle_limit_min': None,  # degrees
            'angle_limit_max': None,  # degrees
            'z_offset': 22.5  # mm
        }
        femur_params: Dict[str, float] = {
            'length': 52.5,  # mm
            'angle_min': -45,  # degrees
            'angle_max': 45,  # degrees
            'angle_limit_min': None,  # degrees
            'angle_limit_max': None,  # degrees
            'invert': True
        }
        tibia_params: Dict[str, float] = {
            'length': 140.0,  # mm
            'angle_min': -45,  # degrees
            'angle_max': 45,  # degrees
            'angle_limit_min': -35,  # degrees
            'angle_limit_max': None,  # degrees
            'x_offset': 22.5  # mm
        }

        self.coxa_channel_map = [0, 3, 6, 15, 18, 21]
        self.femur_channel_map = [1, 4, 7, 16, 19, 22]
        self.tibia_channel_map = [2, 5, 8, 17, 20, 23]

        self.end_effector_offset: Tuple[float, float, float] = (
            tibia_params['x_offset'],
            femur_params['length'] + coxa_params['length'],
            tibia_params['length'] + coxa_params['z_offset']
        )

        self.legs: List[Leg] = []

        for i in range(6):
            coxa_params['channel'] = self.coxa_channel_map[i]
            femur_params['channel'] = self.femur_channel_map[i]
            tibia_params['channel'] = self.tibia_channel_map[i]

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

        self.coxa_params = coxa_params
        self.femur_params = femur_params
        self.tibia_params = tibia_params

        self.calibration: Calibration = Calibration(self)
        self.calibration.load_calibration('/home/hexapod/hexapod/src/robot/calibration.json')

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
                (0.0, 35, -35),
                (0.0, 35, -35),
                (0.0, 35, -35),
                (0.0, 35, -35),
            ],
        }

        self.current_leg_angles: List[Tuple[float, float, float]] = list(self.predefined_angle_positions['home'])
        self.current_leg_positions: List[Tuple[float, float, float]] = list(self.predefined_positions['zero'])

    def calibrate_all_servos(self, stop_event: Optional[threading.Event] = None) -> None:
        """
        Calibrate all servo motors using the Calibration module.
        Sets each leg's status to 'calibrating' and updates to 'calibrated' once done.

        Args:
            stop_event (threading.Event, optional): Event to signal stopping the calibration process.
        """
        self.calibration.calibrate_all_servos(stop_event=stop_event)

    def set_all_servos_speed(self, speed: int = Joint.DEFAULT_SPEED) -> None:
        """
        Set speed for all servos.

        Args:
            speed (int, optional): The speed to set for all servos.
        """
        if speed == 0:
            print("Setting all servos speed to: Unlimited")
        else:
            print(f"Setting all servos speed to: {speed}%")
            speed = map_range(speed, 1, 100, 1, 255)
        
        used_channels = self.coxa_channel_map + self.femur_channel_map + self.tibia_channel_map
        for channel in used_channels:
            self.controller.set_speed(channel, speed)

    def set_all_servos_accel(self, accel: int = Joint.DEFAULT_ACCEL) -> None:
        """
        Set acceleration for all servos.

        Args:
            accel (int, optional): The acceleration to set for all servos.
        """
        if accel == 0:
            print("Setting all servos acceleration to: Unlimited")
        else:
            print(f"Setting all servos acceleration to: {accel}%")
            accel = map_range(accel, 1, 100, 1, 255)
        
        used_channels = self.coxa_channel_map + self.femur_channel_map + self.tibia_channel_map
        for channel in used_channels:
            self.controller.set_acceleration(channel, accel)

    def deactivate_all_servos(self) -> None:
        """
        Sets all servos to 0 to deactivate them.
        """
        targets = []
        for leg in self.legs:
            targets.append((leg.coxa_params['channel'], 0))
            targets.append((leg.femur_params['channel'], 0))
            targets.append((leg.tibia_params['channel'], 0))
        
        # Add unused channels with 0
        unused_channels = [ch for ch in range(self.CONTROLLER_CHANNELS) if ch not in (self.coxa_channel_map + self.femur_channel_map + self.tibia_channel_map)]
        for channel in unused_channels:
            targets.append((channel, 0))

        targets = sorted(targets, key=lambda target: target[0])
        self.controller.set_multiple_targets(targets)

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
        self.current_leg_positions[leg_index] = (x, y, z)

    def move_all_legs(self, positions: List[Tuple[float, float, float]], speed: Optional[int] = None, accel: Optional[int] = None) -> None:
        """
        Move all legs simultaneously to specified positions.
        
        Args:
            positions (List[Tuple[float, float, float]]): List of (x, y, z) tuples for each leg.
            speed (int, optional): Overrides default servo speed.
            accel (int, optional): Overrides default servo acceleration.
        """
        print(f"move_all_legs called with positions: {positions}, speed: {speed}, accel: {accel}")
        if speed is None:
            speed = self.speed
        if accel is None:
            accel = self.accel
        
        for i, pos in enumerate(positions):
            x, y, z = pos
            coxa_angle, femur_angle, tibia_angle = self.legs[i].compute_inverse_kinematics(x, y, z)
            
            if not (self.coxa_params['angle_min'] <= coxa_angle <= self.coxa_params['angle_max']):
                raise ValueError(f"Coxa angle {coxa_angle}° for leg {i} is out of limits ({self.coxa_params['angle_min']}° to {self.coxa_params['angle_max']}°).")
            
            if not (self.femur_params['angle_min'] <= femur_angle <= self.femur_params['angle_max']):
                raise ValueError(f"Femur angle {femur_angle}° for leg {i} is out of limits ({self.femur_params['angle_min']}° to {self.femur_params['angle_max']}°).")
            
            if not (self.tibia_params['angle_min'] <= tibia_angle <= self.tibia_params['angle_max']):
                raise ValueError(f"Tibia angle {tibia_angle}° for leg {i} is out of limits ({self.tibia_params['angle_min']}° to {self.tibia_params['angle_max']}°).")
        
        targets = []
        for i, pos in enumerate(positions):
            x, y, z = pos
            coxa_angle, femur_angle, tibia_angle = self.legs[i].compute_inverse_kinematics(x, y, z)
            
            # Invert angles if required
            if self.legs[i].coxa.invert:
                coxa_angle *= -1
            if self.legs[i].femur.invert:
                femur_angle *= -1
            if self.legs[i].tibia.invert:
                tibia_angle *= -1

            coxa_target = self.legs[i].coxa.angle_to_servo_target(coxa_angle)
            femur_target = self.legs[i].femur.angle_to_servo_target(femur_angle)
            tibia_target = self.legs[i].tibia.angle_to_servo_target(tibia_angle)
            targets.append((self.legs[i].coxa.channel, coxa_target))
            targets.append((self.legs[i].femur.channel, femur_target))
            targets.append((self.legs[i].tibia.channel, tibia_target))
        
        self.set_all_servos_speed(speed)
        self.set_all_servos_accel(accel)
        
        # Add unused channels with 0
        unused_channels = [ch for ch in range(self.CONTROLLER_CHANNELS) if ch not in (self.coxa_channel_map + self.femur_channel_map + self.tibia_channel_map)]
        for channel in unused_channels:
            targets.append((channel, 0))
        
        # Sort targets by channel number to ensure sequential order
        targets = sorted(targets, key=lambda x: x[0])
        print(f"set_multiple_targets called with targets: {targets}")
        self.controller.set_multiple_targets(targets)
        self.current_leg_positions = positions

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
        """
        Move a specific leg to the given joint angles.
        
        Args:
            leg_index (int): Index of the leg (0-5).
            coxa_angle (float): Target angle for the coxa joint.
            femur_angle (float): Target angle for the femur joint.
            tibia_angle (float): Target angle for the tibia joint.
            speed (int, optional): Overrides the default servo speed.
            accel (int, optional): Overrides the default servo acceleration.
        """
        if speed is None:
            speed = self.speed
        if accel is None:
            accel = self.accel

        self.legs[leg_index].move_to_angles(coxa_angle, femur_angle, tibia_angle, speed, accel)
        self.current_leg_angles[leg_index] = (coxa_angle, femur_angle, tibia_angle)
        
    def move_all_legs_angles(self, angles_list: List[Tuple[float, float, float]], speed: Optional[int] = None, accel: Optional[int] = None) -> None:
        """
        Move all legs' angles simultaneously.
        
        Args:
            angles_list (List[Tuple[float, float, float]]): List of (coxa_angle, femur_angle, tibia_angle) tuples for each leg.
            speed (int, optional): Overrides default servo speed.
            accel (int, optional): Overrides default servo acceleration.
        """
        print(f"move_all_legs_angles called with angles_list: {angles_list}, speed: {speed}, accel: {accel}")
        if speed is None:
            speed = self.speed
        if accel is None:
            accel = self.accel
        
        for i, angles in enumerate(angles_list):
            c_angle, f_angle, t_angle = angles
            
            if not (self.coxa_params['angle_min'] <= c_angle <= self.coxa_params['angle_max']):
                raise ValueError(f"Coxa angle {c_angle}° for leg {i} is out of limits ({self.coxa_params['angle_min']}° to {self.coxa_params['angle_max']}°).")
            
            if not (self.femur_params['angle_min'] <= f_angle <= self.femur_params['angle_max']):
                raise ValueError(f"Femur angle {f_angle}° for leg {i} is out of limits ({self.femur_params['angle_min']}° to {self.femur_params['angle_max']}°).")
            
            if not (self.tibia_params['angle_min'] <= t_angle <= self.tibia_params['angle_max']):
                raise ValueError(f"Tibia angle {t_angle}° for leg {i} is out of limits ({self.tibia_params['angle_min']}° to {self.tibia_params['angle_max']}°).")
        
        targets = []
        for i, angles in enumerate(angles_list):
            c_angle, f_angle, t_angle = angles
            
            # Invert angles if required
            if self.legs[i].coxa.invert:
                c_angle *= -1
            if self.legs[i].femur.invert:
                f_angle *= -1
            if self.legs[i].tibia.invert:
                t_angle *= -1

            coxa_target = self.legs[i].coxa.angle_to_servo_target(c_angle)
            femur_target = self.legs[i].femur.angle_to_servo_target(f_angle)
            tibia_target = self.legs[i].tibia.angle_to_servo_target(t_angle)
            targets.append((self.legs[i].coxa.channel, coxa_target))
            targets.append((self.legs[i].femur.channel, femur_target))
            targets.append((self.legs[i].tibia.channel, tibia_target))
        
        self.set_all_servos_speed(speed)
        self.set_all_servos_accel(accel)
        
        # Add unused channels with 0
        unused_channels = [ch for ch in range(self.CONTROLLER_CHANNELS) if ch not in (self.coxa_channel_map + self.femur_channel_map + self.tibia_channel_map)]
        for channel in unused_channels:
            targets.append((channel, 0))
        
        # Sort targets by channel number to ensure sequential order
        targets = sorted(targets, key=lambda x: x[0])
        print(f"set_multiple_targets called with targets: {targets}")
        self.controller.set_multiple_targets(targets)
        self.current_leg_angles = angles_list

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
            bool: True if at least one servo is still moving, False otherwise.
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
        # Wait for at most <motion_timeout> second to see if the robot starts moving
        motion_timeout = 1
        while (time.time() - start_time < motion_timeout) and not (stop_event and stop_event.is_set()):
            if self.get_moving_state():
                break
            if stop_event:
                stop_event.wait(timeout=0.2)

        if stop_event and stop_event.is_set():
            return
        # Wait until the robot stops the motion
        while not (stop_event.is_set() if stop_event else False):
            if not self.get_moving_state():
                break
            if stop_event:
                stop_event.wait(timeout=0.2)

if __name__ == '__main__':
    hexapod = Hexapod()
    # hexapod.calibrate_all_servos()
    hexapod.move_to_angles_position('home')
    # hexapod.controller.go_home()
    # hexapod.deactivate_all_servos()

    # while True:
    #     ax, ay, az = hexapod.imu.get_acceleration()
    #     gx, gy, gz = hexapod.imu.get_gyroscope()
    #     mag_x, mag_y, mag_z = hexapod.imu.get_magnetometer()
    #     temp = hexapod.imu.get_temperature()

    #     print(f"""
    # Accel: {ax:05.2f} {ay:05.2f} {az:05.2f}
    # Gyro:  {gx:05.2f} {gy:05.2f} {gz:05.2f}
    # Mag:   {mag_x:05.2f} {mag_y:05.2f} {mag_z:05.2f}
    # Temp:  {temp:05.2f}""")
    #     time.sleep(1)