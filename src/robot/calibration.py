import json
import threading
import time
import logging
from typing import Optional
from interface.input_handler import InputHandler
from pathlib import Path

logger = logging.getLogger(__name__)

class Calibration:
    def __init__(self, hexapod, calibration_data_path: Path) -> None:
        """
        Initializes the Calibration class with a reference to the Hexapod instance and config file path.
        
        Args:
            hexapod (Hexapod): The Hexapod instance to be calibrated.
            calibration_data_path (Path): Path to save/read the calibration data.
        """
        self.hexapod = hexapod
        self.calibration_data_path = calibration_data_path
        self.input_handler = None
        self.status = {}

        self.calibration_positions = {
            'calibration_init': [
                (0.0, self.hexapod.femur_params['angle_max'], self.hexapod.tibia_params['angle_max']),
                (0.0, self.hexapod.femur_params['angle_max'], self.hexapod.tibia_params['angle_max']),
                (0.0, self.hexapod.femur_params['angle_max'], self.hexapod.tibia_params['angle_max']),
                (0.0, self.hexapod.femur_params['angle_max'], self.hexapod.tibia_params['angle_max']),
                (0.0, self.hexapod.femur_params['angle_max'], self.hexapod.tibia_params['angle_max']),
                (0.0, self.hexapod.femur_params['angle_max'], self.hexapod.tibia_params['angle_max']),
            ],
        }

    def calibrate_all_servos(self, stop_event: Optional[threading.Event] = None) -> None:
        """
        Calibrates all servos for each leg and joint of the hexapod.
        Allows the calibration process to be interrupted using stop_event.
        Updates calibration status for each leg to "calibrating" during the process and "calibrated" upon completion.
        Separates calibration steps into individual methods and handles inverted joints.
        Saves calibration data after successful calibration.
        
        Args:
            stop_event (threading.Event, optional): Event to signal stopping the calibration process.
        """
        from robot import PredefinedAnglePosition
        
        self.input_handler = InputHandler()
        self.input_handler.start()

        self.status = {i: "not_calibrated" for i in range(len(self.hexapod.legs))}
        self.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)

        logger.info("Starting calibration of all servos.")
        try:
            for i, leg in enumerate(self.hexapod.legs):
                if stop_event and stop_event.is_set():
                    logger.warning("Calibration interrupted before starting Leg {}.".format(i))
                    return

                self.hexapod.move_leg_angles(
                    leg_index=i,
                    coxa_angle=self.calibration_positions['calibration_init'][i][0],
                    femur_angle=self.calibration_positions['calibration_init'][i][1],
                    tibia_angle=self.calibration_positions['calibration_init'][i][2]
                )
                logger.debug(f"Set Leg {i} to calibration position.")

                self.status[i] = "calibrating"
                for joint_name in ['coxa', 'femur', 'tibia']:
                    if stop_event and stop_event.is_set():
                        logger.warning("Calibration interrupted during calibration of Leg {}, Joint {}.".format(i, joint_name))
                        return

                    joint = getattr(leg, joint_name)
                    calibration_success = False
                    while not calibration_success:
                        if stop_event and stop_event.is_set():
                            logger.warning("Calibration interrupted during calibration of Leg {}, Joint {}.".format(i, joint_name))
                            return

                        if joint.invert:
                            self.calibrate_servo_min_inverted(i, joint_name, stop_event)
                            self.calibrate_servo_max_inverted(i, joint_name, stop_event)
                        else:
                            self.calibrate_servo_min(i, joint_name, stop_event)
                            self.calibrate_servo_max(i, joint_name, stop_event)

                        if stop_event and stop_event.is_set():
                            logger.warning("Calibration interrupted after calibrating Leg {}, Joint {}.".format(i, joint_name))
                            return

                        calibration_success = self.check_zero_angle(i, joint_name, stop_event)
                    
                    self.hexapod.move_leg_angles(
                        leg_index=i,
                        coxa_angle=self.calibration_positions['calibration_init'][i][0],
                        femur_angle=self.calibration_positions['calibration_init'][i][1],
                        tibia_angle=self.calibration_positions['calibration_init'][i][2]
                    )
                    logger.debug(f"Set Leg {i} to calibration position.")
                
                self.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)
                self.status[i] = "calibrated"
            self.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)
            self.save_calibration()
        except Exception as e:
            logger.exception(f"Error during calibration: {e}")
        finally:
            if self.input_handler:
                self.input_handler.shutdown()
                self.input_handler = None

    def get_calibration_status(self):
        """
        Retrieves current calibration status for all legs.
        
        Returns:
            dict: Mapping of leg_index to calibration status.
        """
        return self.status

    def calibrate_servo_min(self, leg_index, joint_name, stop_event: Optional[threading.Event] = None):
        """
        Calibrates the minimum servo value for a specific joint of a leg.
        Allows interruption using stop_event.
        
        Args:
            leg_index (int): Index of the leg (0-5).
            joint_name (str): Name of the joint ('coxa', 'femur', or 'tibia').
            stop_event (threading.Event, optional): Event to signal stopping the calibration process.
        """
        logger.info(f"Entering servo_min calibration for Leg {leg_index} {joint_name}.")
        calibrated_min = False
        while not calibrated_min:
            if stop_event and stop_event.is_set():
                logger.warning(f"Calibration interrupted during calibration of servo_min of Leg {leg_index} {joint_name}.")
                return
            try:
                joint = getattr(self.hexapod.legs[leg_index], joint_name)
                logger.info(f"Expected angle_min ({joint.angle_min}°) corresponds to servo_min: {992}")

                prompt = f"Enter servo_min for Leg {leg_index} {joint_name} (992-2000): "
                print(prompt, end='', flush=True)  # Print prompt once
                servo_min_input = None
                while servo_min_input is None:
                    if stop_event and stop_event.is_set():
                        logger.warning(f"\nCalibration interrupted during servo_min input of Leg {leg_index} {joint_name}.")
                        return
                    servo_min_input_str = self.input_handler.get_input()
                    if servo_min_input_str is not None:
                        try:
                            servo_min_input = int(servo_min_input_str)
                        except ValueError:
                            logger.warning("\nInvalid input. Please enter an integer value for servo_min.")
                            print(prompt, end='', flush=True)  # Re-prompt once for valid input
                    else:
                        if stop_event:
                            stop_event.wait(timeout=0.1)
                        else:
                            time.sleep(0.1)

                if not (992 <= servo_min_input <= 2000):
                    logger.warning("\nError: servo_min must be between 992 and 2000.")
                    servo_min_input = None
                    continue
                
                servo_min = servo_min_input * 4
                
                self.calibrate_servo(leg_index, joint_name, servo_min, joint.servo_max)
                
                joint.set_angle(joint.angle_min, check_custom_limits=False)
                logger.debug(f"Set {joint_name} of Leg {leg_index} to angle_min: {joint.angle_min}°")

                confirm_min = None
                confirm_prompt = "Is the servo_min calibration correct? (y/n): "
                print(confirm_prompt, end='', flush=True)  # Print confirmation prompt once
                while confirm_min is None:
                    if stop_event and stop_event.is_set():
                        logger.warning(f"\nCalibration interrupted during confirmation of servo_min of Leg {leg_index} {joint_name}.")
                        return
                    confirm_min_str = self.input_handler.get_input()
                    if confirm_min_str is not None:
                        confirm_min = confirm_min_str.strip().lower()
                    else:
                        if stop_event:
                            stop_event.wait(timeout=0.1)
                        else:
                            time.sleep(0.1)

                if confirm_min == 'y':
                    calibrated_min = True
                else:
                    logger.warning("\nRe-enter servo_min calibration value.")
                    print(prompt, end='', flush=True)  # Re-prompt once for re-entry
            except Exception as e:
                logger.exception(f"\nError during servo_min calibration: {e}")

    def calibrate_servo_max(self, leg_index, joint_name, stop_event: Optional[threading.Event] = None):
        """
        Calibrates the maximum servo value for a specific joint of a leg.
        Allows interruption using stop_event.
        
        Args:
            leg_index (int): Index of the leg (0-5).
            joint_name (str): Name of the joint ('coxa', 'femur', or 'tibia').
            stop_event (threading.Event, optional): Event to signal stopping the calibration process.
        """
        logger.info(f"Entering servo_max calibration for Leg {leg_index} {joint_name}.")
        calibrated_max = False
        while not calibrated_max:
            if stop_event and stop_event.is_set():
                logger.warning(f"Calibration interrupted during servo_max of Leg {leg_index} {joint_name}.")
                return
            try:
                joint = getattr(self.hexapod.legs[leg_index], joint_name)
                logger.info(f"Expected angle_max ({joint.angle_max}°) corresponds to servo_max: {2000}")

                prompt = f"Enter servo_max for Leg {leg_index} {joint_name} (992-2000): "
                print(prompt, end='', flush=True)
                servo_max_input = None
                while servo_max_input is None:
                    if stop_event and stop_event.is_set():
                        logger.warning(f"\nCalibration interrupted during servo_max input of Leg {leg_index} {joint_name}.")
                        return
                    servo_max_input_str = self.input_handler.get_input()
                    if servo_max_input_str is not None:
                        try:
                            servo_max_input = int(servo_max_input_str)
                        except ValueError:
                            logger.warning("\nInvalid input. Please enter an integer value for servo_max.")
                            print(prompt, end='', flush=True)
                    else:
                        if stop_event:
                            stop_event.wait(timeout=0.1)
                        else:
                            time.sleep(0.1)

                if not (992 <= servo_max_input <= 2000):
                    logger.warning("\nError: servo_max must be between 992 and 2000.")
                    servo_max_input = None
                    continue

                if servo_max_input <= (joint.servo_min // 4):
                    logger.warning("\nError: servo_max must be greater than servo_min.")
                    servo_max_input = None
                    continue

                servo_max = servo_max_input * 4

                self.calibrate_servo(leg_index, joint_name, joint.servo_min, servo_max)

                joint.set_angle(joint.angle_max, check_custom_limits=False)
                logger.debug(f"Set {joint_name} of Leg {leg_index} to angle_max: {joint.angle_max}°")

                confirm_max = None
                confirm_prompt = "Is the servo_max calibration correct? (y/n): "
                print(confirm_prompt, end='', flush=True)
                while confirm_max is None:
                    if stop_event and stop_event.is_set():
                        logger.warning(f"\nCalibration interrupted during confirmation of servo_max of Leg {leg_index} {joint_name}.")
                        return
                    confirm_max_str = self.input_handler.get_input()
                    if confirm_max_str is not None:
                        confirm_max = confirm_max_str.strip().lower()
                    else:
                        if stop_event:
                            stop_event.wait(timeout=0.1)
                        else:
                            time.sleep(0.1)

                if confirm_max == 'y':
                    calibrated_max = True
                else:
                    logger.warning("\nRe-enter servo_max calibration value.")
                    print(prompt, end='', flush=True)
            except Exception as e:
                logger.exception(f"\nError during servo_max calibration: {e}")

    def calibrate_servo_min_inverted(self, leg_index, joint_name, stop_event: Optional[threading.Event] = None):
        """
        Calibrates the minimum servo value for an inverted joint of a leg.
        
        Inverted joints require swapping the usual servo_min and servo_max values
        to accommodate their reversed movement directions. This method ensures that
        the servo_min is set correctly for joints that are inverted, maintaining proper
        motion ranges and preventing mechanical conflicts.
        Allows interruption using stop_event.
        
        Args:
            leg_index (int): Index of the leg (0-5).
            joint_name (str): Name of the joint ('coxa', 'femur', or 'tibia').
            stop_event (threading.Event, optional): Event to signal stopping the calibration process.
        """
        logger.info(f"Entering inverted servo_min calibration for Leg {leg_index} {joint_name}.")
        calibrated_min = False
        while not calibrated_min:
            if stop_event and stop_event.is_set():
                logger.warning(f"Calibration interrupted during calibration of inverted servo_min of Leg {leg_index} {joint_name}.")
                return
            try:
                joint = getattr(self.hexapod.legs[leg_index], joint_name)
                logger.info(f"Servo inverted. Expected angle_min ({joint.angle_min}°) corresponds to servo_max: {2000}")
                
                prompt = f"Enter servo_max for Leg {leg_index} {joint_name} (992-2000): "
                print(prompt, end='', flush=True)  # Print prompt once
                servo_max_input = None
                while servo_max_input is None:
                    if stop_event and stop_event.is_set():
                        logger.warning(f"\nCalibration interrupted during inverted servo_min input of Leg {leg_index} {joint_name}.")
                        return
                    servo_max_input_str = self.input_handler.get_input()
                    if servo_max_input_str is not None:
                        try:
                            servo_max_input = int(servo_max_input_str)
                        except ValueError as e:
                            logger.warning(f"\nInvalid input. Please enter an integer value for servo_max. Error: {e}")
                            print(prompt, end='', flush=True)  # Re-prompt once for valid input
                    else:
                        if stop_event:
                            stop_event.wait(timeout=0.1)
                        else:
                            time.sleep(0.1)

                if not (992 <= servo_max_input <= 2000):
                    logger.warning("\nError: servo_max must be between 992 and 2000.")
                    servo_max_input = None
                    continue

                servo_max = servo_max_input * 4

                self.calibrate_servo(leg_index, joint_name, joint.servo_min, servo_max)

                joint.set_angle(joint.angle_min, check_custom_limits=False)
                logger.debug(f"Set {joint_name} of Leg {leg_index} to angle_min: {joint.angle_min}°")

                confirm_min = None
                confirm_prompt = "Is the servo_max calibration correct? (y/n): "
                print(confirm_prompt, end='', flush=True)  # Print confirmation prompt once
                while confirm_min is None:
                    if stop_event and stop_event.is_set():
                        logger.warning(f"\nCalibration interrupted during inverted servo_min confirmation of Leg {leg_index} {joint_name}.")
                        return
                    confirm_min_str = self.input_handler.get_input()
                    if confirm_min_str is not None:
                        confirm_min = confirm_min_str.strip().lower()
                    else:
                        if stop_event:
                            stop_event.wait(timeout=0.1)
                        else:
                            time.sleep(0.1)

                if confirm_min == 'y':
                    calibrated_min = True
                else:
                    logger.warning("\nRe-enter servo_max calibration value.")
                    print(prompt, end='', flush=True)  # Re-prompt once for re-entry
            except ValueError as e:
                logger.exception(f"\nInvalid input. Please enter an integer value for servo_max. Error: {e}")

    def calibrate_servo_max_inverted(self, leg_index, joint_name, stop_event: Optional[threading.Event] = None):
        """
        Calibrates the maximum servo value for an inverted joint of a leg.
        
        Inverted joints require swapping the usual servo_min and servo_max values
        to accommodate their reversed movement directions. This method ensures that
        the servo_max is set correctly for joints that are inverted, maintaining proper
        motion ranges and preventing mechanical conflicts.
        Allows interruption using stop_event.
        
        Args:
            leg_index (int): Index of the leg (0-5).
            joint_name (str): Name of the joint ('coxa', 'femur', or 'tibia').
            stop_event (threading.Event, optional): Event to signal stopping the calibration process.
        """
        logger.info(f"Entering inverted servo_max calibration for Leg {leg_index} {joint_name}.")
        calibrated_max = False
        while not calibrated_max:
            if stop_event and stop_event.is_set():
                logger.warning(f"Calibration interrupted during inverted servo_max of Leg {leg_index} {joint_name}.")
                return
            try:
                joint = getattr(self.hexapod.legs[leg_index], joint_name)
                logger.info(f"Servo inverted. Expected angle_max ({joint.angle_max}°) corresponds to servo_min: {992}")
                
                prompt = f"Enter servo_min for Leg {leg_index} {joint_name} (992-2000): "
                print(prompt, end='', flush=True)  # Print prompt once
                servo_min_input = None
                while servo_min_input is None:
                    if stop_event and stop_event.is_set():
                        logger.warning(f"\nCalibration interrupted during inverted servo_max input of Leg {leg_index} {joint_name}.")
                        return
                    servo_min_input_str = self.input_handler.get_input()
                    if servo_min_input_str is not None:
                        try:
                            servo_min_input = int(servo_min_input_str)
                        except ValueError:
                            logger.exception("\nInvalid input. Please enter an integer value for servo_min.")
                            print(prompt, end='', flush=True)  # Re-prompt once for valid input
                    else:
                        if stop_event:
                            stop_event.wait(timeout=0.1)
                        else:
                            time.sleep(0.1)

                if not (992 <= servo_min_input <= 2000):
                    logger.warning("\nError: servo_min must be between 992 and 2000.")
                    servo_min_input = None
                    continue
                if servo_min_input >= (joint.servo_max // 4):
                    logger.warning("\nError: Inverted servo_min must be less than inverted servo_max.")
                    servo_min_input = None
                    continue

                servo_min = servo_min_input * 4

                self.calibrate_servo(leg_index, joint_name, servo_min, joint.servo_max)

                joint.set_angle(joint.angle_max, check_custom_limits=False)
                logger.debug(f"Set {joint_name} of Leg {leg_index} to angle_max: {joint.angle_max}°")

                confirm_max = None
                confirm_prompt = "Is the servo_min calibration correct? (y/n): "
                print(confirm_prompt, end='', flush=True)  # Print confirmation prompt once
                while confirm_max is None:
                    if stop_event and stop_event.is_set():
                        logger.warning(f"\nCalibration interrupted during inverted servo_max confirmation of Leg {leg_index} {joint_name}.")
                        return
                    confirm_max_str = self.input_handler.get_input()
                    if confirm_max_str is not None:
                        confirm_max = confirm_max_str.strip().lower()
                    else:
                        if stop_event:
                            stop_event.wait(timeout=0.1)
                        else:
                            time.sleep(0.1)

                if confirm_max == 'y':
                    calibrated_max = True
                else:
                    logger.warning("\nRe-enter servo_min calibration value.")
                    print(prompt, end='', flush=True)  # Re-prompt once for re-entry
            except ValueError:
                logger.exception("\nInvalid input. Please enter an integer value for servo_min.")

    def check_zero_angle(self, leg_index, joint_name, stop_event: Optional[threading.Event] = None):
        """
        Checks and validates the zero angle calibration for a specific joint of a leg.
        Allows interruption using stop_event.
        
        Args:
            leg_index (int): Index of the leg (0-5).
            joint_name (str): Name of the joint ('coxa', 'femur', or 'tibia').
            stop_event (threading.Event, optional): Event to signal stopping the calibration process.

        Returns:
            bool: True if zero angle calibration is correct, False otherwise.
        """
        logger.info(f"Checking zero angle for Leg {leg_index} {joint_name}.")
        calibrated_zero = False
        while not calibrated_zero:
            if stop_event and stop_event.is_set():
                logger.warning(f"Calibration interrupted during zero angle check of Leg {leg_index} {joint_name}.")
                return False
            try:
                joint = getattr(self.hexapod.legs[leg_index], joint_name)
                joint.set_angle(0, check_custom_limits=False)
                logger.debug(f"Set {joint_name} of Leg {leg_index} to angle_zero: 0°")
                
                prompt = "Is the zero angle calibration correct? (y/n): "
                print(prompt, end='', flush=True)  # Print prompt once
                confirm_zero = None
                while confirm_zero is None:
                    if stop_event and stop_event.is_set():
                        logger.warning(f"\nCalibration interrupted during zero angle confirmation of Leg {leg_index} {joint_name}.")
                        return False
                    confirm_zero_str = self.input_handler.get_input()
                    if confirm_zero_str is not None:
                        confirm_zero = confirm_zero_str.strip().lower()
                    else:
                        if stop_event:
                            stop_event.wait(timeout=0.1)
                        else:
                            time.sleep(0.1)

                if confirm_zero == 'y':
                    calibrated_zero = True
                    return True
                else:
                    logger.warning("\nZero angle calibrated incorrectly. Recalibrating...")
                    return False
            except ValueError as e:
                logger.exception(f"\nError setting zero angle: {e}")
        return False

    def save_calibration(self):
        """
        Saves the current calibration settings to a JSON file.
        Overwrites the existing file at self.calibration_data_path with the latest calibration data.
        """
        calibration_data = {}
        for i, leg in enumerate(self.hexapod.legs):
            calibration_data[f"leg_{i}"] = {
                "coxa": {
                    "servo_min": leg.coxa.servo_min,
                    "servo_max": leg.coxa.servo_max
                },
                "femur": {
                    "servo_min": leg.femur.servo_min,
                    "servo_max": leg.femur.servo_max
                },
                "tibia": {
                    "servo_min": leg.tibia.servo_min,
                    "servo_max": leg.tibia.servo_max
                }
            }
        
        try:
            with self.calibration_data_path.open("w") as f:
                json.dump(calibration_data, f, indent=4)
            logger.info(f"Calibration data saved to {self.calibration_data_path}.")
        except IOError as e:
            logger.exception(f"Failed to save calibration data: {e}")

    def load_calibration(self):
        """
        Load calibration data from the save path.
        """
        try:
            with self.calibration_data_path.open("r") as f:
                calibration_data = json.load(f)
            for i, leg in enumerate(self.hexapod.legs):
                leg_data = calibration_data.get(f"leg_{i}", {})
                for joint_name in ['coxa', 'femur', 'tibia']:
                    joint_calib = leg_data.get(joint_name, {})
                    servo_min = joint_calib.get('servo_min')
                    servo_max = joint_calib.get('servo_max')
                    if servo_min and servo_max:
                        if (992 * 4 <= servo_min <= 2000 * 4 and
                            992 * 4 <= servo_max <= 2000 * 4 and
                            servo_min < servo_max):
                            self.calibrate_servo(i, joint_name, servo_min, servo_max)
                            logger.info(f"Loaded calibration for leg {i} {joint_name}: servo_min={servo_min}, servo_max={servo_max}")
                        else:
                            logger.warning(f"Calibration values for leg {i} {joint_name} are invalid (servo_min: {servo_min}, servo_max: {servo_max}). Using default values.")
                            self.calibrate_servo(i, joint_name, 992 * 4, 2000 * 4)
                            logger.info(f"Set to default: servo_min=3968, servo_max=8000")
        except FileNotFoundError:
            logger.warning(f"{self.calibration_data_path} not found. Using default calibration values. Run calibrate_all_servos() to set new values.")
        except json.JSONDecodeError as e:
            logger.warning(f"Error decoding {self.calibration_data_path}: {e}. Using default calibration values. Run calibrate_all_servos() to set new values.")

    def calibrate_servo(self, leg_index, joint, servo_min, servo_max):
        """
        Updates the servo calibration parameters for a specific joint of a leg.
        
        Args:
            leg_index (int): Index of the leg (0-5).
            joint (str): Name of the joint ('coxa', 'femur', or 'tibia').
            servo_min (int): New minimum servo value.
            servo_max (int): New maximum servo value.
        """
        if 0 <= leg_index < len(self.hexapod.legs):
            leg = self.hexapod.legs[leg_index]
            if joint == 'coxa':
                leg.coxa_params['servo_min'] = servo_min
                leg.coxa_params['servo_max'] = servo_max
                leg.coxa.update_calibration(servo_min, servo_max)
            elif joint == 'femur':
                leg.femur_params['servo_min'] = servo_min
                leg.femur_params['servo_max'] = servo_max
                leg.femur.update_calibration(servo_min, servo_max)
            elif joint == 'tibia':
                leg.tibia_params['servo_min'] = servo_min
                leg.tibia_params['servo_max'] = servo_max
                leg.tibia.update_calibration(servo_min, servo_max)
            else:
                logger.warning("Invalid joint name. Choose 'coxa', 'femur', or 'tibia'.")
        else:
            logger.warning("Invalid leg index. Must be between 0 and 5.")