from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import json
import threading
import time
from pathlib import Path

from interface import NonBlockingConsoleInputHandler
from utils import rename_thread
from robot import Joint

if TYPE_CHECKING:
    from typing import Optional
    from robot import Hexapod

logger = logging.getLogger("robot_logger")

class Calibration:
    def __init__(self, hexapod: Hexapod, calibration_data_path: Path) -> None:
        """
        Initialize the Calibration class with the Hexapod instance and calibration data path.
        
        Args:
            hexapod (Hexapod): The Hexapod instance to be calibrated.
            calibration_data_path (Path): Path to save or read the calibration data.
        """
        self.hexapod = hexapod
        self.calibration_data_path = calibration_data_path
        self.input_handler = None
        self.status = {i: "not_calibrated" for i in range(len(self.hexapod.legs))}

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
        Calibrate all servos for each leg and joint of the hexapod.
        
        This method allows the calibration process to be interrupted using a stop event.
        It updates the calibration status for each leg to "calibrating" during the process
        and "calibrated" upon completion. Calibration steps are separated into individual
        methods and handle inverted joints. Calibration data is saved after successful calibration.
        
        Args:
            stop_event (Optional[threading.Event]): Event to signal stopping the calibration process.
        """
        from robot import PredefinedAnglePosition
        
        self.input_handler = NonBlockingConsoleInputHandler()
        rename_thread(self.input_handler, "CalibrationInputHandler")
        self.input_handler.start()

        self.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)

        logger.debug("Starting calibration of all servos.")
        logger.debug(f"Calibration status: {self.status}")
        try:
            for i, leg in enumerate(self.hexapod.legs):
                if stop_event and stop_event.is_set():
                    logger.error("Calibration interrupted before starting Leg {}.".format(i))
                    return

                self.hexapod.move_leg_angles(
                    leg_index=i,
                    coxa_angle=self.calibration_positions['calibration_init'][i][0],
                    femur_angle=self.calibration_positions['calibration_init'][i][1],
                    tibia_angle=self.calibration_positions['calibration_init'][i][2]
                )
                logger.debug(f"Set Leg {i} to calibration position.")

                self.status[i] = "calibrating"
                logger.debug(f"Calibration status: {self.status}")
                for joint_name in ['coxa', 'femur', 'tibia']:
                    if stop_event and stop_event.is_set():
                        logger.error("Calibration interrupted during calibration of Leg {}, Joint {}.".format(i, joint_name))
                        return

                    joint = getattr(leg, joint_name)
                    calibration_success = False
                    while not calibration_success:
                        if stop_event and stop_event.is_set():
                            logger.error("Calibration interrupted during calibration of Leg {}, Joint {}.".format(i, joint_name))
                            return

                        if joint.invert:
                            self._calibrate_servo_min_inverted(i, joint_name, stop_event)
                            self._calibrate_servo_max_inverted(i, joint_name, stop_event)
                        else:
                            self._calibrate_servo_min(i, joint_name, stop_event)
                            self._calibrate_servo_max(i, joint_name, stop_event)

                        if stop_event and stop_event.is_set():
                            logger.error("Calibration interrupted after calibrating Leg {}, Joint {}.".format(i, joint_name))
                            return

                        calibration_success = self._check_zero_angle(i, joint_name, stop_event)
                    
                    self.hexapod.move_leg_angles(
                        leg_index=i,
                        coxa_angle=self.calibration_positions['calibration_init'][i][0],
                        femur_angle=self.calibration_positions['calibration_init'][i][1],
                        tibia_angle=self.calibration_positions['calibration_init'][i][2]
                    )
                    logger.debug(f"Set Leg {i} to calibration position.")
                
                self.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)
                self.status[i] = "calibrated"
                logger.debug(f"Calibration status: {self.status}")
            self.hexapod.move_to_angles_position(PredefinedAnglePosition.HOME)
            self._save_calibration()
        except Exception as e:
            logger.exception(f"Error during calibration: {e}")
        finally:
            self.status = {i: "not_calibrated" for i in range(len(self.hexapod.legs))}
            if self.input_handler:
                self.input_handler.shutdown()
                self.input_handler = None

    def get_calibration_status(self) -> dict:
        """
        Retrieve the current calibration status for all legs.
        
        Returns:
            dict: A dictionary mapping each leg index to its calibration status.
        """
        return self.status

    def load_calibration(self) -> None:
        """
        Load calibration data from the specified calibration data path.
        
        This method reads the calibration data from a JSON file and updates each leg's
        joint calibration parameters. If the calibration data is invalid or the file
        is not found, default calibration values are used.
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
                        if (Joint.SERVO_INPUT_MIN * Joint.SERVO_UNIT_MULTIPLIER <= servo_min <= Joint.SERVO_INPUT_MAX * Joint.SERVO_UNIT_MULTIPLIER and
                            Joint.SERVO_INPUT_MIN * Joint.SERVO_UNIT_MULTIPLIER <= servo_max <= Joint.SERVO_INPUT_MAX * Joint.SERVO_UNIT_MULTIPLIER and
                            servo_min < servo_max):
                            self._calibrate_servo(i, joint_name, servo_min, servo_max)
                            logger.debug(f"Loaded calibration for leg {i} {joint_name}: servo_min={servo_min}, servo_max={servo_max}")
                        else:
                            logger.warning(f"Calibration values for leg {i} {joint_name} are invalid (servo_min: {servo_min}, servo_max: {servo_max}). Using default values: servo_min={Joint.SERVO_INPUT_MIN * Joint.SERVO_UNIT_MULTIPLIER}, servo_max={Joint.SERVO_INPUT_MAX * Joint.SERVO_UNIT_MULTIPLIER}.")
                            self._calibrate_servo(i, joint_name, Joint.SERVO_INPUT_MIN * Joint.SERVO_UNIT_MULTIPLIER, Joint.SERVO_INPUT_MAX * Joint.SERVO_UNIT_MULTIPLIER)
        except FileNotFoundError:
            logger.exception(f"{self.calibration_data_path} not found. Using default calibration values. Run calibrate_all_servos() to set new values.")
        except json.JSONDecodeError as e:
            logger.exception(f"Error decoding {self.calibration_data_path}: {e}. Using default calibration values. Run calibrate_all_servos() to set new values.")

    def _save_calibration(self) -> None:
        """
        Save the current calibration settings to a JSON file.
        
        This method overwrites the existing calibration data file with the latest
        calibration data for all legs and their respective joints.
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
            logger.user_info(f"Calibration data saved to {self.calibration_data_path}.")
        except IOError as e:
            logger.exception(f"Failed to save calibration data: {e}")

    def _calibrate_servo_min(self, leg_index: int, joint_name: str, stop_event: Optional[threading.Event] = None) -> None:
        """
        Calibrate the minimum servo value for a specified joint.
        
        Args:
            leg_index (int): Index of the leg (0-5) to calibrate.
            joint_name (str): Name of the joint ('coxa', 'femur', or 'tibia') to calibrate.
            stop_event (Optional[threading.Event]): Event to signal stopping the calibration process.
        """
        joint = getattr(self.hexapod.legs[leg_index], joint_name)
        self._calibrate_joint(
            leg_index, joint_name, 'angle_min', joint.angle_min, 'servo_min',
            stop_event=stop_event, invert=False
        )

    def _calibrate_servo_max(self, leg_index: int, joint_name: str, stop_event: Optional[threading.Event] = None) -> None:
        """
        Calibrate the maximum servo value for a specified joint.
        
        Args:
            leg_index (int): Index of the leg (0-5) to calibrate.
            joint_name (str): Name of the joint ('coxa', 'femur', or 'tibia') to calibrate.
            stop_event (Optional[threading.Event]): Event to signal stopping the calibration process.
        """
        joint = getattr(self.hexapod.legs[leg_index], joint_name)
        self._calibrate_joint(
            leg_index, joint_name, 'angle_max', joint.angle_max, 'servo_max',
            stop_event=stop_event, invert=False
        )

    def _calibrate_servo_min_inverted(self, leg_index: int, joint_name: str, stop_event: Optional[threading.Event] = None) -> None:
        """
        Calibrate the minimum servo value for an inverted joint.
        
        Args:
            leg_index (int): Index of the leg (0-5) to calibrate.
            joint_name (str): Name of the joint ('coxa', 'femur', or 'tibia') to calibrate.
            stop_event (Optional[threading.Event]): Event to signal stopping the calibration process.
        """
        joint = getattr(self.hexapod.legs[leg_index], joint_name)
        self._calibrate_joint(
            leg_index, joint_name, 'angle_min', joint.angle_min, 'servo_max',
            stop_event=stop_event, invert=True
        )

    def _calibrate_servo_max_inverted(self, leg_index: int, joint_name: str, stop_event: Optional[threading.Event] = None) -> None:
        """
        Calibrate the maximum servo value for an inverted joint.
        
        Args:
            leg_index (int): Index of the leg (0-5) to calibrate.
            joint_name (str): Name of the joint ('coxa', 'femur', or 'tibia') to calibrate.
            stop_event (Optional[threading.Event]): Event to signal stopping the calibration process.
        """
        joint = getattr(self.hexapod.legs[leg_index], joint_name)
        self._calibrate_joint(
            leg_index, joint_name, 'angle_max', joint.angle_max, 'servo_min',
            stop_event=stop_event, invert=True
        )

    def _check_zero_angle(self, leg_index: int, joint_name: str, stop_event: Optional[threading.Event] = None) -> bool:
        """
        Validate the zero angle calibration for a specific joint of a leg.
        
        This method sets the joint angle to zero and prompts the user to confirm if the calibration is correct.
        It allows the calibration process to be interrupted using a stop event.
        
        Args:
            leg_index (int): Index of the leg (0-5).
            joint_name (str): Name of the joint ('coxa', 'femur', or 'tibia').
            stop_event (Optional[threading.Event]): Event to signal stopping the calibration process.
        
        Returns:
            bool: True if zero angle calibration is correct, False otherwise.
        """
        logger.debug(f"Checking zero angle for Leg {leg_index} {joint_name}.")
        calibrated_zero = False
        while not calibrated_zero:
            if stop_event and stop_event.is_set():
                logger.error(f"Calibration interrupted during zero angle check of Leg {leg_index} {joint_name}.")
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
                        logger.error(f"\nCalibration interrupted during zero angle confirmation of Leg {leg_index} {joint_name}.")
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
                    print("Zero angle calibrated incorrectly. Recalibrating...")
                    return False
            except Exception as e:
                logger.exception(f"Error setting zero angle: {e}")
                
        return False

    def _prompt_servo_value(self, leg_index: int, joint_name: str, servo_label: str, stop_event: Optional[threading.Event] = None) -> int:
        """
        Prompt the user to enter a servo calibration value.
        
        This method ensures that the input provided by the user is a valid integer within the defined range.
        It allows the calibration process to be interrupted using a stop event.
        
        Args:
            leg_index (int): Index of the leg (0-5).
            joint_name (str): Name of the joint ('coxa', 'femur', or 'tibia').
            servo_label (str): Label indicating which servo value is being calibrated ('servo_min' or 'servo_max').
            stop_event (Optional[threading.Event]): Event to signal stopping the calibration process.
        
        Returns:
            int: The validated servo input value, or None if interrupted.
        """
        prompt = f"\nEnter {servo_label} for Leg {leg_index} {joint_name} ({Joint.SERVO_INPUT_MIN}-{Joint.SERVO_INPUT_MAX}): "
        print(prompt, end='', flush=True)
        servo_input = None
        while servo_input is None:
            if stop_event and stop_event.is_set():
                return None
            servo_input_str = self.input_handler.get_input()
            if servo_input_str is not None:
                try:
                    servo_input = int(servo_input_str)
                except ValueError:
                    print(f"Invalid input. Please enter an integer value for {servo_label}.")
                    print(prompt, end='', flush=True)
                    servo_input = None
            else:
                if stop_event:
                    stop_event.wait(timeout=0.1)
                else:
                    time.sleep(0.1)
        return servo_input

    def _confirm_calibration_done(self, servo_label: str, stop_event: Optional[threading.Event] = None) -> bool:
        """
        Confirm with the user whether the servo calibration is correct.
        
        This method prompts the user to confirm the calibration by entering 'y' or 'n'.
        It allows the calibration process to be interrupted using a stop event.
        
        Args:
            servo_label (str): Label indicating which servo calibration is being confirmed ('servo_min' or 'servo_max').
            stop_event (Optional[threading.Event]): Event to signal stopping the calibration process.
        
        Returns:
            bool: True if the calibration is confirmed correct, False otherwise.
        """
        confirm_prompt = f"Is the {servo_label} calibration correct? (y/n): "
        print(confirm_prompt, end='', flush=True)
        confirm = None
        while confirm is None:
            if stop_event and stop_event.is_set():
                return False
            confirm_str = self.input_handler.get_input()
            if confirm_str is not None:
                confirm = confirm_str.strip().lower()
            else:
                if stop_event:
                    stop_event.wait(timeout=0.1)
                else:
                    time.sleep(0.1)
        return confirm == 'y'

    def _validate_servo_input(self, servo_label: str, servo_input: int, invert: bool = False) -> bool:
        """
        Validate the servo input based on the servo label and inversion status.
        
        This method checks if the provided servo input is within the acceptable range and
        adheres to the inversion constraints if applicable.
        
        Args:
            servo_label (str): Label indicating which servo value is being validated ('servo_min' or 'servo_max').
            servo_input (int): The servo input value to validate.
            invert (bool, optional): Indicates if the joint is inverted.
        
        Returns:
            bool: True if the input is valid, False otherwise.
        """
        if not (Joint.SERVO_INPUT_MIN <= servo_input <= Joint.SERVO_INPUT_MAX):
            print(f"Error: {servo_label} must be between {Joint.SERVO_INPUT_MIN} and {Joint.SERVO_INPUT_MAX}.")
            return False

        if invert:
            if servo_label == 'servo_min' and servo_input >= Joint.SERVO_INPUT_MAX:
                print(f"Error: {servo_label} must be less than current maximum servo_max input ({Joint.SERVO_INPUT_MAX}).")
                return False
            elif servo_label == 'servo_max' and servo_input <= Joint.SERVO_INPUT_MIN:
                print(f"Error: {servo_label} must be greater than current minimum servo_min input ({Joint.SERVO_INPUT_MIN}).")
                return False
        else:
            if servo_label == 'servo_min' and servo_input >= Joint.SERVO_INPUT_MAX:
                print(f"Error: {servo_label} must be less than current maximum servo_max input ({Joint.SERVO_INPUT_MAX}).")
                return False
            elif servo_label == 'servo_max' and servo_input <= Joint.SERVO_INPUT_MIN:
                print(f"Error: {servo_label} must be greater than current minimum servo_min input ({Joint.SERVO_INPUT_MIN}).")
                return False

        return True

    def _calibrate_joint(self, leg_index: int, joint_name: str, angle_label: str, expected_angle: float, 
                        servo_label: str, stop_event: Optional[threading.Event] = None, invert: bool = False) -> None:
        """
        Prompt the user to calibrate a specific servo of a joint.
        
        This helper method guides the user through entering and confirming servo calibration values,
        ensuring that inputs are valid and that servo_max remains greater than servo_min.
        
        Args:
            leg_index (int): Index of the leg (0-5) to calibrate.
            joint_name (str): Name of the joint ('coxa', 'femur', or 'tibia') to calibrate.
            angle_label (str): Label indicating which angle is being calibrated ('angle_min' or 'angle_max').
            expected_angle (float): The expected angle value corresponding to the servo calibration.
            servo_label (str): Label indicating which servo value is being calibrated ('servo_min' or 'servo_max').
            stop_event (Optional[threading.Event]): Event to signal stopping the calibration process.
            invert (bool, optional): Indicates if the joint is inverted.
        """
        logger.debug(f"Entering {servo_label} calibration for Leg {leg_index} {joint_name}.")
        calibrated = False
        while not calibrated:
            if stop_event and stop_event.is_set():
                logger.error(f"Calibration interrupted during {servo_label} of Leg {leg_index} {joint_name}.")
                return
            try:
                joint = getattr(self.hexapod.legs[leg_index], joint_name)

                if servo_label == 'servo_min':
                    expected_servo = Joint.SERVO_INPUT_MIN
                else:
                    expected_servo = Joint.SERVO_INPUT_MAX
                print(f"Expected {angle_label} ({expected_angle}°) corresponds to {servo_label} (Expected Value: {expected_servo}).")

                servo_input = self._prompt_servo_value(leg_index, joint_name, servo_label, stop_event)
                if servo_input is None:  # interrupted
                    return

                if not self._validate_servo_input(servo_label, servo_input, invert):
                    continue

                servo_value = servo_input * Joint.SERVO_UNIT_MULTIPLIER

                if servo_label == 'servo_min':
                    self._calibrate_servo(leg_index, joint_name, servo_value, joint.servo_max)
                else:
                    self._calibrate_servo(leg_index, joint_name, joint.servo_min, servo_value)

                # If this is the second input, ensure servo_max > servo_min
                if joint.servo_max <= joint.servo_min:
                    print("Error: servo_max must be greater than servo_min")
                    continue

                joint.set_angle(expected_angle, check_custom_limits=False)
                logger.debug(f"Set {joint_name} of Leg {leg_index} to {angle_label}: {expected_angle}°")

                if self._confirm_calibration_done(servo_label, stop_event):
                    calibrated = True
                else:
                    print(f"Re-enter {servo_label} calibration value.")
            except Exception as e:
                logger.exception(f"Error during {servo_label} calibration: {e}")

    def _calibrate_servo(self, leg_index: int, joint: str, servo_min: int, servo_max: int) -> None:
        """
        Update the servo calibration parameters for a specific joint of a leg.
        
        This method sets the new minimum and maximum servo values and updates the joint's calibration.
        
        Args:
            leg_index (int): Index of the leg (0-5).
            joint (str): Name of the joint ('coxa', 'femur', or 'tibia').
            servo_min (int): New minimum servo value.
            servo_max (int): New maximum servo value.
        """
        try:
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
                    logger.error("Invalid joint name. Choose 'coxa', 'femur', or 'tibia'.")
            else:
                logger.error("Invalid leg index. Must be between 0 and 5.")
        except Exception as e:
            logger.exception(f"Error updating servo calibration for leg {leg_index} {joint}: {e}")