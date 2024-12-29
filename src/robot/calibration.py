import json
import threading
import logging
from typing import Optional
from interface.input_handler import InputHandler

class Calibration:
    def __init__(self, hexapod):
        """
        Initializes the Calibration class with a reference to the Hexapod instance.
        
        Args:
            hexapod (Hexapod): The Hexapod instance to be calibrated.
        """
        self.hexapod = hexapod
        # Initialize the InputHandler
        self.input_handler = InputHandler()
        # Initialize all legs as not calibrated
        self.status = {i: "not_calibrated" for i in range(len(self.hexapod.legs))}

    def get_input(self) -> Optional[str]:
        """
        Retrieves user input in a non-blocking manner by fetching it from the InputHandler.
        
        Returns:
            Optional[str]: The user input or None if interrupted.
        """
        return self.input_handler.get_input(timeout=0.1)

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
        self.status = {i: "not_calibrated" for i in range(len(self.hexapod.legs))}
        try:
            for i, leg in enumerate(self.hexapod.legs):
                if stop_event and stop_event.is_set():
                    print("Calibration interrupted before starting Leg {}.".format(i))
                    self._shutdown_input_listener()
                    return

                self.status[i] = "calibrating"
                for joint_name in ['coxa', 'femur', 'tibia']:
                    if stop_event and stop_event.is_set():
                        print("Calibration interrupted during calibration of Leg {}, Joint {}.".format(i, joint_name))
                        self._shutdown_input_listener()
                        return

                    joint = getattr(leg, joint_name)
                    calibration_success = False
                    while not calibration_success:
                        if stop_event and stop_event.is_set():
                            print("Calibration interrupted during calibration of Leg {}, Joint {}.".format(i, joint_name))
                            self._shutdown_input_listener()
                            return

                        if joint.invert:
                            self.calibrate_servo_min_inverted(i, joint_name, stop_event)
                            self.calibrate_servo_max_inverted(i, joint_name, stop_event)
                        else:
                            self.calibrate_servo_min(i, joint_name, stop_event)
                            self.calibrate_servo_max(i, joint_name, stop_event)

                        if stop_event and stop_event.is_set():
                            print("Calibration interrupted after calibrating Leg {}, Joint {}.".format(i, joint_name))
                            self._shutdown_input_listener()
                            return

                        calibration_success = self.check_zero_angle(i, joint_name, stop_event)
                    
                    self.hexapod.controller.go_home()
                    print(f"Set Leg {i} to default position (0, 0, 0).")
                
                self.status[i] = "calibrated"
            self.save_calibration()
            self._shutdown_input_listener()
        except Exception as e:
            print(f"Error during calibration: {e}")
            self._shutdown_input_listener()

    def _shutdown_input_listener(self):
        """
        Shuts down the input listener gracefully using the InputHandler.
        """
        self.input_handler.shutdown()
        try:
            import sys
            sys.stdin.close()
        except Exception as e:
            logging.error("Error shutting down input listener", exc_info=True)

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
        calibrated_min = False
        while not calibrated_min:
            if stop_event and stop_event.is_set():
                print(f"Calibration interrupted during calibration of servo_min of Leg {leg_index} {joint_name}.")
                return
            try:
                joint = getattr(self.hexapod.legs[leg_index], joint_name)
                print(f"Expected angle_min ({joint.angle_min}°) corresponds to servo_min: {992}")

                prompt = f"Enter servo_min for Leg {leg_index} {joint_name} (992-2000): "
                print(prompt, end='', flush=True)  # Print prompt once
                servo_min_input = None
                while servo_min_input is None:
                    if stop_event and stop_event.is_set():
                        print(f"\nCalibration interrupted during servo_min input of Leg {leg_index} {joint_name}.")
                        return
                    servo_min_input_str = self.get_input()
                    if servo_min_input_str is not None:
                        try:
                            servo_min_input = int(servo_min_input_str)
                        except ValueError:
                            print("\nInvalid input. Please enter an integer value for servo_min.")
                            print(prompt, end='', flush=True)  # Re-prompt once for valid input
                    else:
                        stop_event.wait(timeout=0.1)

                if not (992 <= servo_min_input <= 2000):
                    print("\nError: servo_min must be between 992 and 2000.")
                    servo_min_input = None
                    continue
                
                servo_min = servo_min_input * 4
                
                self.calibrate_servo(leg_index, joint_name, servo_min, joint.servo_max)
                
                joint.set_angle(joint.angle_min)
                print(f"Set {joint_name} of Leg {leg_index} to angle_min: {joint.angle_min}°")

                confirm_min = None
                confirm_prompt = "Is the servo_min calibration correct? (y/n): "
                print(confirm_prompt, end='', flush=True)  # Print confirmation prompt once
                while confirm_min is None:
                    if stop_event and stop_event.is_set():
                        print(f"\nCalibration interrupted during confirmation of servo_min of Leg {leg_index} {joint_name}.")
                        return
                    confirm_min_str = self.get_input()
                    if confirm_min_str is not None:
                        confirm_min = confirm_min_str.strip().lower()
                    else:
                        stop_event.wait(timeout=0.1)

                if confirm_min == 'y':
                    calibrated_min = True
                else:
                    print("\nRe-enter servo_min calibration value.")
                    print(prompt, end='', flush=True)  # Re-prompt once for re-entry
            except Exception as e:
                print(f"\nError during servo_min calibration: {e}")

    def calibrate_servo_max(self, leg_index, joint_name, stop_event: Optional[threading.Event] = None):
        """
        Calibrates the maximum servo value for a specific joint of a leg.
        Allows interruption using stop_event.
        
        Args:
            leg_index (int): Index of the leg (0-5).
            joint_name (str): Name of the joint ('coxa', 'femur', or 'tibia').
            stop_event (threading.Event, optional): Event to signal stopping the calibration process.
        """
        calibrated_max = False
        while not calibrated_max:
            if stop_event and stop_event.is_set():
                print(f"Calibration interrupted during servo_max of Leg {leg_index} {joint_name}.")
                return
            try:
                joint = getattr(self.hexapod.legs[leg_index], joint_name)
                if joint.invert:
                    print(f"Expected angle_max ({joint.angle_max}°) corresponds to servo_min: {992}")
                else:
                    print(f"Expected angle_max ({joint.angle_max}°) corresponds to servo_max: {2000}")

                prompt = f"Enter servo_max for Leg {leg_index} {joint_name} (992-2000): "
                print(prompt, end='', flush=True)  # Print prompt once
                servo_max_input = None
                while servo_max_input is None:
                    if stop_event and stop_event.is_set():
                        print(f"\nCalibration interrupted during servo_max input of Leg {leg_index} {joint_name}.")
                        return
                    servo_max_input_str = self.get_input()
                    if servo_max_input_str is not None:
                        try:
                            servo_max_input = int(servo_max_input_str)
                        except ValueError:
                            print("\nInvalid input. Please enter an integer value for servo_max.")
                            print(prompt, end='', flush=True)  # Re-prompt once for valid input
                    else:
                        # No input yet, wait briefly
                        stop_event.wait(timeout=0.1)

                if not (992 <= servo_max_input <= 2000):
                    print("\nError: servo_max must be between 992 and 2000.")
                    servo_max_input = None
                    continue

                if not joint.invert:
                    if servo_max_input <= (joint.servo_min // 4):
                        print("\nError: servo_max must be greater than servo_min.")
                        servo_max_input = None
                        continue

                servo_max = servo_max_input * 4

                self.calibrate_servo(leg_index, joint_name, joint.servo_min, servo_max)

                joint.set_angle(joint.angle_max)
                print(f"Set {joint_name} of Leg {leg_index} to angle_max: {joint.angle_max}°")

                confirm_max = None
                confirm_prompt = "Is the servo_max calibration correct? (y/n): "
                print(confirm_prompt, end='', flush=True)  # Print confirmation prompt once
                while confirm_max is None:
                    if stop_event and stop_event.is_set():
                        print(f"\nCalibration interrupted during confirmation of servo_max of Leg {leg_index} {joint_name}.")
                        return
                    confirm_max_str = self.get_input()
                    if confirm_max_str is not None:
                        confirm_max = confirm_max_str.strip().lower()
                    else:
                        stop_event.wait(timeout=0.1)

                if confirm_max == 'y':
                    calibrated_max = True
                else:
                    print("\nRe-enter servo_max calibration value.")
                    print(prompt, end='', flush=True)  # Re-prompt once for re-entry
            except Exception as e:
                print(f"\nError during servo_max calibration: {e}")

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
        calibrated_min = False
        while not calibrated_min:
            if stop_event and stop_event.is_set():
                print(f"Calibration interrupted during calibration of inverted servo_min of Leg {leg_index} {joint_name}.")
                return
            try:
                joint = getattr(self.hexapod.legs[leg_index], joint_name)
                print(f"Expected angle_min ({joint.angle_min}°) corresponds to servo_max: {2000}")
                
                prompt = f"Enter servo_max for Leg {leg_index} {joint_name} (992-2000): "
                print(prompt, end='', flush=True)  # Print prompt once
                servo_max_input = None
                while servo_max_input is None:
                    if stop_event and stop_event.is_set():
                        print(f"\nCalibration interrupted during inverted servo_min input of Leg {leg_index} {joint_name}.")
                        return
                    servo_max_input_str = self.get_input()
                    if servo_max_input_str is not None:
                        try:
                            servo_max_input = int(servo_max_input_str)
                        except ValueError as e:
                            print(f"\nInvalid input. Please enter an integer value for servo_max. Error: {e}")
                            print(prompt, end='', flush=True)  # Re-prompt once for valid input
                    else:
                        stop_event.wait(timeout=0.1)

                if not (992 <= servo_max_input <= 2000):
                    print("\nError: servo_max must be between 992 and 2000.")
                    servo_max_input = None
                    continue

                servo_max = servo_max_input * 4

                self.calibrate_servo(leg_index, joint_name, joint.servo_min, servo_max)

                joint.set_angle(joint.angle_min)
                print(f"Set {joint_name} of Leg {leg_index} to angle_min: {joint.angle_min}°")

                confirm_min = None
                confirm_prompt = "Is the servo_max calibration correct? (y/n): "
                print(confirm_prompt, end='', flush=True)  # Print confirmation prompt once
                while confirm_min is None:
                    if stop_event and stop_event.is_set():
                        print(f"\nCalibration interrupted during inverted servo_min confirmation of Leg {leg_index} {joint_name}.")
                        return
                    confirm_min_str = self.get_input()
                    if confirm_min_str is not None:
                        confirm_min = confirm_min_str.strip().lower()
                    else:
                        stop_event.wait(timeout=0.1)

                if confirm_min == 'y':
                    calibrated_min = True
                else:
                    print("\nRe-enter servo_max calibration value.")
                    print(prompt, end='', flush=True)  # Re-prompt once for re-entry
            except ValueError as e:
                print(f"\nInvalid input. Please enter an integer value for servo_max. Error: {e}")

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
        calibrated_max = False
        while not calibrated_max:
            if stop_event and stop_event.is_set():
                print(f"Calibration interrupted during inverted servo_max of Leg {leg_index} {joint_name}.")
                return
            try:
                joint = getattr(self.hexapod.legs[leg_index], joint_name)
                print(f"Expected angle_max ({joint.angle_max}°) corresponds to servo_min: {992}")
                
                prompt = f"Enter servo_min for Leg {leg_index} {joint_name} (992-2000): "
                print(prompt, end='', flush=True)  # Print prompt once
                servo_min_input = None
                while servo_min_input is None:
                    if stop_event and stop_event.is_set():
                        print(f"\nCalibration interrupted during inverted servo_max input of Leg {leg_index} {joint_name}.")
                        return
                    servo_min_input_str = self.get_input()
                    if servo_min_input_str is not None:
                        try:
                            servo_min_input = int(servo_min_input_str)
                        except ValueError:
                            print("\nInvalid input. Please enter an integer value for servo_min.")
                            print(prompt, end='', flush=True)  # Re-prompt once for valid input
                    else:
                        stop_event.wait(timeout=0.1)

                if not (992 <= servo_min_input <= 2000):
                    print("\nError: servo_min must be between 992 and 2000.")
                    servo_min_input = None
                    continue
                if servo_min_input >= (joint.servo_max // 4):
                    print("\nError: Inverted servo_min must be less than inverted servo_max.")
                    servo_min_input = None
                    continue

                servo_min = servo_min_input * 4

                self.calibrate_servo(leg_index, joint_name, servo_min, joint.servo_max)

                joint.set_angle(joint.angle_max)
                print(f"Set {joint_name} of Leg {leg_index} to angle_max: {joint.angle_max}°")

                confirm_max = None
                confirm_prompt = "Is the servo_min calibration correct? (y/n): "
                print(confirm_prompt, end='', flush=True)  # Print confirmation prompt once
                while confirm_max is None:
                    if stop_event and stop_event.is_set():
                        print(f"\nCalibration interrupted during inverted servo_max confirmation of Leg {leg_index} {joint_name}.")
                        return
                    confirm_max_str = self.get_input()
                    if confirm_max_str is not None:
                        confirm_max = confirm_max_str.strip().lower()
                    else:
                        stop_event.wait(timeout=0.1)

                if confirm_max == 'y':
                    calibrated_max = True
                else:
                    print("\nRe-enter servo_min calibration value.")
                    print(prompt, end='', flush=True)  # Re-prompt once for re-entry
            except ValueError:
                print("\nInvalid input. Please enter an integer value for servo_min.")

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
        calibrated_zero = False
        while not calibrated_zero:
            if stop_event and stop_event.is_set():
                print(f"Calibration interrupted during zero angle check of Leg {leg_index} {joint_name}.")
                return False
            try:
                joint = getattr(self.hexapod.legs[leg_index], joint_name)
                joint.set_angle(0)
                print(f"Set {joint_name} of Leg {leg_index} to angle_zero: 0°")
                
                prompt = "Is the zero angle calibration correct? (y/n): "
                print(prompt, end='', flush=True)  # Print prompt once
                confirm_zero = None
                while confirm_zero is None:
                    if stop_event and stop_event.is_set():
                        print(f"\nCalibration interrupted during zero angle confirmation of Leg {leg_index} {joint_name}.")
                        return False
                    confirm_zero_str = self.get_input()
                    if confirm_zero_str is not None:
                        confirm_zero = confirm_zero_str.strip().lower()
                    else:
                        stop_event.wait(timeout=0.1)

                if confirm_zero == 'y':
                    calibrated_zero = True
                    return True
                else:
                    print("\nZero angle calibrated incorrectly. Recalibrating...")
                    return False
            except ValueError as e:
                print(f"\nError setting zero angle: {e}")
        return False

    def save_calibration(self):
        """
        Saves the current calibration settings to a JSON file.
        Overwrites the existing calibration.json file with the latest calibration data.
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
            with open("calibration.json", "w") as f:
                json.dump(calibration_data, f, indent=4)
            print("Calibration data saved to calibration.json.")
        except IOError as e:
            print(f"Failed to save calibration data: {e}")

    def load_calibration(self):
        """
        Loads calibration data from the calibration.json file and updates servo parameters.
        Validates that servo_min and servo_max are within acceptable ranges before applying.
        """
        try:
            with open("calibration.json", "r") as f:
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
                            print(f"Loaded calibration for leg {i} {joint_name}: servo_min={servo_min}, servo_max={servo_max}")
                        else:
                            print(f"Calibration values for leg {i} {joint_name} are invalid (servo_min: {servo_min}, servo_max: {servo_max}). Using default values.")
                            self.calibrate_servo(i, joint_name, 992 * 4, 2000 * 4)
                            print(f"Set to default: servo_min=3968, servo_max=8000")
        except FileNotFoundError:
            print("calibration.json not found. Using default calibration values. Run calibrate_all_servos() to set new values.")
        except json.JSONDecodeError as e:
            print(f"Error decoding calibration.json: {e}")
            print("Using default calibration values. Run calibrate_all_servos() to set new values.")

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
                print("Invalid joint name. Choose 'coxa', 'femur', or 'tibia'.")
        else:
            print("Invalid leg index. Must be between 0 and 5.")