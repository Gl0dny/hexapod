from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import threading
import time
from enum import Enum
from pathlib import Path

import yaml
import numpy as np

from maestro import MaestroUART
from robot import Leg, Joint, Calibration, GaitGenerator
from imu import Imu
from utils import map_range, homogeneous_transformation_matrix

if TYPE_CHECKING:
    from typing import Optional, List, Tuple, Dict, Union, Callable

logger = logging.getLogger("robot_logger")

class PredefinedAnglePosition(Enum):
    LOW_PROFILE = 'low_profile'
    UPRIGHT = 'upright'

class PredefinedPosition(Enum):
    LOW_PROFILE = 'low_profile'
    UPRIGHT = 'upright'

class Hexapod:
    """
    Represents the hexapod robot with six legs, managing servo motors, sensor data, and gait generation.

    Attributes:
        hexagon_side_length (float): Side length of the hexagon formed by the legs.
        leg_angles (List[int]): Angles for each leg in a regular hexagon.
        controller (MaestroUART): Serial controller for managing servo motors.
        speed (int): Default speed setting for servo movements.
        accel (int): Default acceleration setting for servo movements.
        imu (Imu): Instance of the Imu class for IMU sensor data.
        legs (List[Leg]): List of Leg instances representing each of the hexapod's legs.
        leg_to_led (Dict[int, int]): Mapping from leg indices to LED indices.
        coxa_params (Dict[str, float]): Parameters for the coxa joint, including length (mm), channel, angle limits (degrees), and servo settings.
        femur_params (Dict[str, float]): Parameters for the femur joint, including length (mm), channel, angle limits (degrees), and servo settings.
        tibia_params (Dict[str, float]): Parameters for the tibia joint, including length (mm), channel, angle limits (degrees), and servo settings.
        end_effector_offset (Tuple[float, float, float]): Default offset for the end effector position - (x, y, z) in mm.
        self.end_effector_radius (float): Distance from the body center to the end effector.
        calibration (Calibration): Instance managing servo calibrations and related processes.
        predefined_positions (Dict[str, List[Tuple[float, float, float]]]): Predefined positions for the legs.
        predefined_angle_positions (Dict[str, List[Tuple[float, float, float]]]): Predefined angle positions for the legs.
        current_leg_angles (List[Tuple[float, float, float]]): Current angles of the legs.
        current_leg_positions (List[Tuple[float, float, float]]): Current positions of the legs.
        gait_generator (GaitGenerator): Instance managing gait patterns.
    """
    CONTROLLER_CHANNELS: int = 24  # Number of all controller channels used to manage the servos.
    
    def __init__(
        self, 
        config_path: Path = Path('src/robot/config/hexapod_config.yaml'),
        calibration_data_path: Path = Path('src/robot/config/calibration.json')
    ) -> None:
        """
        Initializes the Hexapod robot by loading configuration parameters, setting up servo controllers,
        and initializing all legs.

        Args:
            config_path (Path): Path to the hexapod configuration YAML file.
            calibration_data_path (Path): Path to the calibration data JSON file.
        """
        
        if config_path.is_file():
            with config_path.open('r') as config_file:
                config = yaml.safe_load(config_file)
        else:
            raise FileNotFoundError(f"Hexapod configuration file not found at {config_path}")
        
        self.hexagon_side_length: float = config['hexagon_side_length']
        
        # Initialize hexagon angles
        self._compute_hexagon_angles: Callable[[], List[int]] = lambda: [i * 60 for i in range(6)]
        self.leg_angles: List[int] = np.radians(self._compute_hexagon_angles()).tolist()

        self.controller: MaestroUART = MaestroUART(config['controller']['port'], config['controller']['baudrate'])
        
        # Speed setting for the servo in percent. Speed unit - (0.25us/10ms).
        # The speed parameter can be set to a maximum value of 255, corresponding to a change of 63.75 μs every 10 ms.
        # Default from config: 25% (from hexapod_config.yaml)
        # This is a percentage value (1-100) that gets converted to Maestro range (1-255) when used
        self.speed: int = config['speed']
        # Acceleration setting for the servo percent. Acceleration units - (0.25us/10ms/80ms).
        # The maximum acceleration setting is 255, allowing the speed to change by 63.75 μs per 10 ms interval every 80 ms.
        # Default from config: 10% (from hexapod_config.yaml)
        # This is a percentage value (1-100) that gets converted to Maestro range (1-255) when used
        self.accel: int = config['accel']

        self.imu = Imu()

        coxa_params: Dict[str, Union[float, bool]] = config['coxa_params']
        femur_params: Dict[str, Union[float, bool]] = config['femur_params']
        tibia_params: Dict[str, Union[float, bool]] = config['tibia_params']

        self.coxa_channel_map = config['coxa_channel_map']
        self.femur_channel_map = config['femur_channel_map']
        self.tibia_channel_map = config['tibia_channel_map']

        self.end_effector_offset: Tuple[float, float, float] = tuple(config['end_effector_offset'])

        self.legs: List[Leg] = []

        for i in range(6):
            coxa_params['channel'] = self.coxa_channel_map[i]
            femur_params['channel'] = self.femur_channel_map[i]
            tibia_params['channel'] = self.tibia_channel_map[i]

            leg = Leg(coxa_params, femur_params, tibia_params, self.controller, self.end_effector_offset)
            self.legs.append(leg)

        self.leg_to_led: Dict[int, int] = config['leg_to_led']

        self.coxa_params: Dict[str, Union[float, bool]] = coxa_params
        self.femur_params: Dict[str, Union[float, bool]] = femur_params
        self.tibia_params: Dict[str, Union[float, bool]] = tibia_params

        self.end_effector_radius = self.hexagon_side_length + self.coxa_params['length'] + self.femur_params['length'] # For regular hexagon, side length = radius ; Tibia points downward, Coxa and Femur are horizontal in initial position

        self.calibration: Calibration = Calibration(self, calibration_data_path=calibration_data_path)
        self.calibration.load_calibration()

        self.predefined_positions: Dict[str, List[Tuple[float, float, float]]] = config['predefined_positions']
        self.predefined_angle_positions: Dict[str, List[Tuple[float, float, float]]] = config['predefined_angle_positions']

        self.current_leg_angles: List[Tuple[float, float, float]] = list(self.predefined_angle_positions['low_profile'])
        self.current_leg_positions: List[Tuple[float, float, float]] = list(self.predefined_positions['low_profile'])

        self.gait_generator = GaitGenerator(self)

        self.set_all_servos_speed(self.speed)
        self.set_all_servos_accel(self.accel)

        self.move_to_position(PredefinedPosition.LOW_PROFILE)
        self.wait_until_motion_complete()
        
        logger.info("Hexapod initialized successfully")

    def calibrate_all_servos(self, stop_event: Optional[threading.Event] = None) -> None:
        logger.info("Starting calibration of all servos")
        """
        Calibrate all servo motors using the Calibration module.
        Sets each leg's status to 'calibrating' and updates to 'calibrated' once done.

        Args:
            stop_event (threading.Event, optional): Event to signal stopping the calibration process.
        """
        self.calibration.calibrate_all_servos(stop_event=stop_event)
        logger.info("Calibration of all servos completed")

    def set_all_servos_speed(self, speed: int) -> None:
        """
        Set speed for all servos.

        Args:
            speed (int): The speed to set for all servos.
                - Range: 1-100 (percentage) or 0 (unlimited)
                - 0: Unlimited speed (no speed limit)
                - 1-100: Percentage of maximum speed (1% = slowest, 100% = fastest)
        """
        if speed == 0:
            logger.warning("Setting all servos speed to: Unlimited")
        else:
            logger.info(f"Setting all servos speed to: {speed}%")
            speed = map_range(speed, 1, 100, 1, 255)
        
        used_channels = self.coxa_channel_map + self.femur_channel_map + self.tibia_channel_map
        for channel in used_channels:
            self.controller.set_speed(channel, speed)

    def set_all_servos_accel(self, accel: int) -> None:
        """
        Set acceleration for all servos.

        Args:
            accel (int): The acceleration to set for all servos.
                - Range: 1-100 (percentage) or 0 (unlimited)
                - 0: Unlimited acceleration (no acceleration limit)
                - 1-100: Percentage of maximum acceleration (1% = slowest, 100% = fastest)
        """
        if accel == 0:
            logger.warning("Setting all servos acceleration to: Unlimited")
        else:
            logger.info(f"Setting all servos acceleration to: {accel}%")
            accel = map_range(accel, 1, 100, 1, 255)
        
        used_channels = self.coxa_channel_map + self.femur_channel_map + self.tibia_channel_map
        for channel in used_channels:
            self.controller.set_acceleration(channel, accel)

    def deactivate_all_servos(self) -> None:
        logger.info("Moving to LOW_PROFILE position before deactivating servos")
        """
        First moves the hexapod to LOW_PROFILE position, then sets all servos to 0 to deactivate them.
        """
        # First move to LOW_PROFILE position
        self.move_to_position(PredefinedPosition.LOW_PROFILE)
        self.wait_until_motion_complete()
        
        logger.info("Deactivating all servos")
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
        logger.info("All servos deactivated")

    def move_leg(
        self, 
        leg_index: int, 
        x: float, 
        y: float, 
        z: float
    ) -> None:
        logger.info(f"Moving leg {leg_index} to position x: {x}, y: {y}, z: {z}")
        """
        Move a specific leg to the given (x, y, z) coordinate.
        
        Args:
            leg_index (int): Index of the leg (0-5).
            x (float): Target x-coordinate.
            y (float): Target y-coordinate.
            z (float): Target z-coordinate.
        """
        self.legs[leg_index].move_to(x, y, z)
        self.current_leg_positions[leg_index] = (x, y, z)
        coxa_angle, femur_angle, tibia_angle = self.legs[leg_index].compute_inverse_kinematics(x, y, z)
        self.current_leg_angles[leg_index] = (coxa_angle, femur_angle, tibia_angle)
        logger.info(f"Leg {leg_index} moved to position x: {x}, y: {y}, z: {z}")

    def move_all_legs(
        self, 
        positions: List[Tuple[float, float, float]]
    ) -> None:
        logger.info(f"move_all_legs called with positions: {positions}")
        """
        Move all legs simultaneously to specified positions.
        
        Args:
            positions (List[Tuple[float, float, float]]): List of (x, y, z) tuples for each leg.
        """
        logger.info(f"move_all_legs called with positions: {positions}")
        
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
        
        # Add unused channels with 0
        unused_channels = [ch for ch in range(self.CONTROLLER_CHANNELS) if ch not in (self.coxa_channel_map + self.femur_channel_map + self.tibia_channel_map)]
        for channel in unused_channels:
            targets.append((channel, 0))
        
        # Sort targets by channel number to ensure sequential order
        targets = sorted(targets, key=lambda x: x[0])
        logger.debug(f"set_multiple_targets called with targets: {targets}")
        self.controller.set_multiple_targets(targets)
        self.current_leg_positions = positions
        self._sync_angles_from_positions()
        logger.info("All legs moved to new positions")

    def move_body(
        self,
        tx: float = 0.0,
        ty: float = 0.0,
        tz: float = 0.0,
        roll: float = 0.0,
        pitch: float = 0.0, 
        yaw: float = 0.0
        ):
        """
        Compute body inverse kinematics using provided translation and rotation parameters,
        transform the computed deltas to leg frames, and move all legs to new target positions.
        
        Args:
            tx (float): Translation along the x-axis in mm.
            ty (float): Translation along the y-axis in mm.
            tz (float): Translation along the z-axis in mm.
            roll (float): Rotation around the x-axis in degrees.
            pitch (float): Rotation around the y-axis in degrees.
            yaw (float): Rotation around the z-axis in degrees.
        """
        logger.debug(f"Moving body: tx={tx}, ty={ty}, tz={tz}, roll={roll}, pitch={pitch}, yaw={yaw}")
        global_deltas = self._compute_body_inverse_kinematics(tx, ty, tz, roll, pitch, yaw)
        local_deltas = self._transform_body_to_leg_frames(global_deltas)
        
        target_positions = [
            (
                current_x + delta_x,
                current_y + delta_y,
                current_z + delta_z
            )
            for (current_x, current_y, current_z), (delta_x, delta_y, delta_z) in zip(self.current_leg_positions, local_deltas)
        ]
        
        try:
            self.move_all_legs(target_positions)
        except ValueError as e:
            # Chain the exception with move_body context
            context_msg = f"move_body(tx={tx}, ty={ty}, tz={tz}, roll={roll}, pitch={pitch}, yaw={yaw})"
            raise ValueError(f"{str(e)} (called from: {context_msg})") from e
        
        self._sync_angles_from_positions()

    def move_to_position(self, position_name: PredefinedPosition) -> None:
        """
        Move the hexapod to a predefined position.
        
        Args:
            position_name (PredefinedPosition): Enum member representing the predefined position.
        """
        logger.info(f"Setting all legs to position '{position_name.value}'")
        positions = self.predefined_positions.get(position_name.value)
        if positions:
            self.move_all_legs(positions)
            logger.info(f"All legs set to position '{position_name.value}'")
        else:
            available = list(self.predefined_positions.keys())
            logger.error(f"Unknown position '{position_name.value}'. Available positions: {available}")

    def move_leg_angles(
        self,
        leg_index: int,
        coxa_angle: float,
        femur_angle: float,
        tibia_angle: float
    ) -> None:
        logger.info(f"Moving leg {leg_index} to angles coxa: {coxa_angle}, femur: {femur_angle}, tibia: {tibia_angle}")
        """
        Move a specific leg to the given joint angles.
        
        Args:
            leg_index (int): Index of the leg (0-5).
            coxa_angle (float): Target angle for the coxa joint.
            femur_angle (float): Target angle for the femur joint.
            tibia_angle (float): Target angle for the tibia joint.
        """
        self.legs[leg_index].move_to_angles(coxa_angle, femur_angle, tibia_angle)
        self.current_leg_angles[leg_index] = (coxa_angle, femur_angle, tibia_angle)
        x, y, z = self.legs[leg_index].compute_forward_kinematics(coxa_angle, femur_angle, tibia_angle)
        self.current_leg_positions[leg_index] = (x, y, z)
        logger.info(f"Leg {leg_index} moved to angles coxa: {coxa_angle}, femur: {femur_angle}, tibia: {tibia_angle}")
        
    def move_all_legs_angles(
        self, 
        angles_list: List[Tuple[float, float, float]]
    ) -> None:
        logger.info(f"move_all_legs_angles called with angles_list: {angles_list}")
        """
        Move all legs' angles simultaneously.
        
        Args:
            angles_list (List[Tuple[float, float, float]]): List of (coxa_angle, femur_angle, tibia_angle) tuples for each leg.
        """
        logger.info(f"move_all_legs_angles called with angles_list: {angles_list}")
        
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
        
        # Add unused channels with 0
        unused_channels = [ch for ch in range(self.CONTROLLER_CHANNELS) if ch not in (self.coxa_channel_map + self.femur_channel_map + self.tibia_channel_map)]
        for channel in unused_channels:
            targets.append((channel, 0))
        
        # Sort targets by channel number to ensure sequential order
        targets = sorted(targets, key=lambda x: x[0])
        logger.debug(f"set_multiple_targets called with targets: {targets}")
        self.controller.set_multiple_targets(targets)
        self.current_leg_angles = angles_list
        self._sync_positions_from_angles()
        logger.info("All legs moved to new angles")

    def wait_until_motion_complete(
        self, 
        stop_event: Optional[threading.Event] = None
    ) -> None:
        logger.info("Waiting until motion is complete")
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
            if self._get_moving_state():
                break
            if stop_event:
                stop_event.wait(timeout=0.2)

        logger.info("Motion started")

        if stop_event and stop_event.is_set():
            return
        # Wait until the robot stops the motion
        while not (stop_event.is_set() if stop_event else False):
            if not self._get_moving_state():
                break
            if stop_event:
                stop_event.wait(timeout=0.2)
        logger.info("Motion complete")

    def move_to_angles_position(self, position_name: PredefinedAnglePosition) -> None:
        logger.info(f"Setting all legs to angles position '{position_name.value}'")
        """
        Move the hexapod to a predefined angle position.
        
        Args:
            position_name (PredefinedAnglePosition): Enum member representing the predefined angle position.
        """
        logger.info(f"Setting all legs to angles position '{position_name.value}'")
        angles = self.predefined_angle_positions.get(position_name.value)
        if angles:
            try:
                self.move_all_legs_angles(angles)
            except ValueError as e:
                # Chain the exception with move_to_angles_position context
                context_msg = f"move_to_angles_position('{position_name.value}')"
                raise ValueError(f"{str(e)} (called from: {context_msg})") from e
            logger.info(f"All legs set to angles position '{position_name.value}'")
        else:
            available = list(self.predefined_angle_positions.keys())
            logger.error(f"Unknown angles position '{position_name.value}'. Available angle positions: {available}")

    def _sync_positions_from_angles(self) -> None:
        """
        Synchronize the current_leg_positions with current_leg_angles by computing
        forward kinematics from the current angles.
        """
        logger.debug("Before sync (angles -> positions):")
        logger.debug(f"Positions: {self.current_leg_positions}")
        logger.debug(f"Angles: {self.current_leg_angles}")
            
        for i, leg in enumerate(self.legs):
            coxa_angle, femur_angle, tibia_angle = self.current_leg_angles[i]
            x, y, z = leg.compute_forward_kinematics(coxa_angle, femur_angle, tibia_angle)
            self.current_leg_positions[i] = (x, y, z)
            
        logger.debug("After sync (angles -> positions):")
        logger.debug(f"Positions: {self.current_leg_positions}")
        logger.debug(f"Angles: {self.current_leg_angles}")

    def _sync_angles_from_positions(self) -> None:
        """
        Synchronize the current_leg_angles with current_leg_positions by computing
        inverse kinematics from the current positions.
        """
        logger.debug("Before sync (positions -> angles):")
        logger.debug(f"Positions: {self.current_leg_positions}")
        logger.debug(f"Angles: {self.current_leg_angles}")
            
        for i, leg in enumerate(self.legs):
            x, y, z = self.current_leg_positions[i]
            coxa_angle, femur_angle, tibia_angle = leg.compute_inverse_kinematics(x, y, z)
            self.current_leg_angles[i] = (coxa_angle, femur_angle, tibia_angle)
            
        logger.debug("After sync (positions -> angles):")
        logger.debug(f"Positions: {self.current_leg_positions}")
        logger.debug(f"Angles: {self.current_leg_angles}")

    def _get_moving_state(self) -> bool:
        logger.debug("Querying moving state from Maestro controller")
        """
        Returns the moving state of the hexapod by querying the Maestro controller.

        Returns:
            bool: True if at least one servo is still moving, False otherwise.
        """
        moving_state = self.controller.get_moving_state()
        logger.debug(f"Moving state: {moving_state}")
        if moving_state == 0x01:
            return True
        else:
            return False

    def _compute_body_inverse_kinematics(
        self, 
        tx: float = 0.0, 
        ty: float = 0.0, 
        tz: float = 0.0,
        roll: float = 0.0, 
        pitch: float = 0.0, 
        yaw: float = 0.0
    ) -> np.ndarray:
        """
        Calculate leg position deltas using homogeneous transformations.

        Args:
            tx (float): Translation along the x-axis in mm.
            ty (float): Translation along the y-axis in mm.
            tz (float): Translation along the z-axis in mm.
            roll (float): Rotation around the x-axis in degrees.
            pitch (float): Rotation around the y-axis in degrees.
            yaw (float): Rotation around the z-axis in degrees.

        Returns:
            np.ndarray: 6x3 array of (Δx, Δy, Δz) for each leg.
        """

        # Calculate initial end effector positions
        leg_angles = self.leg_angles
        initial_positions = np.array([
            [
                self.end_effector_radius * np.cos(theta),
                self.end_effector_radius * np.sin(theta),
                -self.tibia_params["length"]  # Tibia points downward
            ] for theta in leg_angles
        ])

        # Create homogeneous transformation matrix
        T = homogeneous_transformation_matrix(tx, ty, -tz, roll, pitch, yaw)
        
        # Apply transformation
        homogenous_pos = np.hstack((initial_positions, np.ones((6, 1))))
        transformed = (homogenous_pos @ T.T)[:, :3]
    
        # Calculate deltas relative to initial positions
        deltas = transformed - initial_positions
        deltas = np.round(deltas, 2)
        logger.debug(f"Computed body IK deltas: {deltas}")
        return deltas

    def _transform_body_to_leg_frames(
        self, 
        body_frame_deltas: np.ndarray
    ) -> np.ndarray:
        """
        Transform deltas from body reference frame to each leg's local frame.
        Each leg's local frame is rotated -90° relative to its mounting angle.

        Args:
            body_frame_deltas (np.ndarray): Deltas in the body reference frame.

        Returns:
            np.ndarray: Deltas in each leg's local frame.
        """
        
        # Initialize array for leg frame deltas
        leg_frame_deltas = np.zeros_like(body_frame_deltas)
        
        for i, leg_angle_rad in enumerate(self.leg_angles):
            # Create rotation matrix for leg's local frame (-90° relative to mounting angle)
            rotation_matrix_leg_frame = np.array([
                [np.sin(leg_angle_rad), -np.cos(leg_angle_rad), 0],  # X-axis: perpendicular to mounting angle
                [np.cos(leg_angle_rad), np.sin(leg_angle_rad), 0],   # Y-axis: along mounting angle
                [0, 0, 1]                                             # Z-axis: unchanged
            ])
            
            # Transform delta to leg frame
            leg_frame_deltas[i] = rotation_matrix_leg_frame @ body_frame_deltas[i]
            deltas = np.round(leg_frame_deltas, 2)
            logger.debug(f"Computed local body:leg frame IK deltas: {deltas}")
        
        return deltas

if __name__ == '__main__':
    hexapod = Hexapod()
    # hexapod.calibrate_all_servos()
    hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)
    # hexapod.controller.go_home()
    # hexapod.deactivate_all_servos()

    # while True:
    #     ax, ay, az = hexapod.imu.get_acceleration()
    #     gx, gy, gz = hexapod.imu.get_gyroscope()
    #     mag_x, mag_y, mag_z = hexapod.imu.get_magnetometer()
    #     temp = hexapod.imu.get_temperature()

    #     logger.info(f"""
    # Accel: {ax:05.2f} {ay:05.2f} {az:05.2f}
    # Gyro:  {gx:05.2f} {gy:05.2f} {gz:05.2f}
    # Mag:   {mag_x:05.2f} {mag_y:05.2f} {mag_z:05.2f}
    # Temp:  {temp:05.2f}""")
    #     time.sleep(1)