import json
import threading
from typing import Optional

class Calibration:
    def __init__(self, hexapod):
        """
        Initializes the Calibration class with a reference to the Hexapod instance.
        
        Args:
            hexapod (Hexapod): The Hexapod instance to be calibrated.
        """
        self.hexapod = hexapod
        # Initialize all legs as not calibrated
        self.status = {i: "not_calibrated" for i in range(len(self.hexapod.legs))}

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
        try:
            for i, leg in enumerate(self.hexapod.legs):
                if stop_event and stop_event.is_set():
                    print("Calibration interrupted before starting Leg {}.".format(i))
                    return

                self.status[i] = "calibrating"
                for joint_name in ['coxa', 'femur', 'tibia']:
                    if stop_event and stop_event.is_set():
                        print("Calibration interrupted during calibration of Leg {}, Joint {}.".format(i, joint_name))
                        return

                    joint = getattr(leg, joint_name)
                    calibration_success = False
                    while not calibration_success:
                        if stop_event and stop_event.is_set():
                            print("Calibration interrupted during calibration of Leg {}, Joint {}.".format(i, joint_name))
                            return

                        if joint.invert:
                            self.calibrate_servo_min_inverted(i, joint_name, stop_event)
                            self.calibrate_servo_max_inverted(i, joint_name, stop_event)
                        else:
                            self.calibrate_servo_min(i, joint_name, stop_event)
                            self.calibrate_servo_max(i, joint_name, stop_event)

                        if stop_event and stop_event.is_set():
                            print("Calibration interrupted after calibrating Leg {}, Joint {}.".format(i, joint_name))
                            return

                        calibration_success = self.check_zero_angle(i, joint_name, stop_event)
                    
                    self.hexapod.controller.go_home()
                    print(f"Set Leg {i} to default position (0, 0, 0).")
                
                self.status[i] = "calibrated"
            self.save_calibration()
        except Exception as e:
            print(f"Error during calibration: {e}")

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

                servo_min_input = int(input(f"Enter servo_min for Leg {leg_index} {joint_name} (992-2000): "))
                
                if not (992 <= servo_min_input <= 2000):
                    print("Error: servo_min must be between 992 and 2000.")
                    continue
                
                servo_min = servo_min_input * 4
                
                self.calibrate_servo(leg_index, joint_name, servo_min, joint.servo_max)
                
                joint.set_angle(joint.angle_min)
                print(f"Set {joint_name} of Leg {leg_index} to angle_min: {joint.angle_min}°")
                
                confirm_min = input("Is the servo_min calibration correct? (y/n): ").strip().lower()
                print()
                if confirm_min == 'y':
                    calibrated_min = True
                else:
                    print("Re-enter servo_min calibration value.")
            except ValueError as e:
                print(f"Invalid input. Please enter an integer value for servo_min. Error: {e}")

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
                print(f"Calibration interrupted during calibration of servo_max of Leg {leg_index} {joint_name}.")
                return
            try:
                joint = getattr(self.hexapod.legs[leg_index], joint_name)
                print(f"Expected angle_max ({joint.angle_max}°) corresponds to servo_max: {2000}")

                servo_max_input = int(input(f"Enter servo_max for Leg {leg_index} {joint_name} (992-2000): "))
                
                if not (992 <= servo_max_input <= 2000):
                    print("Error: servo_max must be between 992 and 2000.")
                    continue

                if servo_max_input <= (joint.servo_min // 4):
                    print("Error: servo_max must be greater than servo_min.")
                    continue
                
                servo_max = servo_max_input * 4
                
                self.calibrate_servo(leg_index, joint_name, joint.servo_min, servo_max)
                
                joint.set_angle(joint.angle_max)
                print(f"Set {joint_name} of Leg {leg_index} to angle_max: {joint.angle_max}°")
                
                confirm_max = input("Is the servo_max calibration correct? (y/n): ").strip().lower()
                print()
                if confirm_max == 'y':
                    calibrated_max = True
                else:
                    print("Re-enter servo_max calibration value.")
            except ValueError:
                print("Invalid input. Please enter an integer value for servo_max.")

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
                
                servo_max_input = int(input(f"Enter servo_max for Leg {leg_index} {joint_name} (992-2000): "))
                
                if not (992 <= servo_max_input <= 2000):
                    print("Error: servo_max must be between 992 and 2000.")
                    continue

                servo_max = servo_max_input * 4
                
                self.calibrate_servo(leg_index, joint.servo_min, servo_max)
                
                joint.set_angle(joint.angle_min)
                print(f"Set {joint_name} of Leg {leg_index} to angle_min: {joint.angle_min}°")
                
                confirm_min = input("Is the servo_max calibration correct? (y/n): ").strip().lower()
                print()
                if confirm_min == 'y':
                    calibrated_min = True
                else:
                    print("Re-enter servo_max calibration value.")
            except ValueError as e:
                print(f"Invalid input. Please enter an integer value for servo_max. Error: {e}")

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
                print(f"Calibration interrupted during calibration of inverted servo_max of Leg {leg_index} {joint_name}.")
                return
            try:
                joint = getattr(self.hexapod.legs[leg_index], joint_name)
                print(f"Expected angle_max ({joint.angle_max}°) corresponds to servo_min: {992}")
                
                servo_min_input = int(input(f"Enter servo_min for Leg {leg_index} {joint_name} (992-2000): "))
                
                if not (992 <= servo_min_input <= 2000):
                    print("Error: servo_min must be between 992 and 2000.")
                    continue
                if servo_min_input >= (joint.servo_max // 4):
                    print("Error: Inverted servo_min must be less than inverted servo_max.")
                    continue

                servo_min = servo_min_input * 4
                
                self.calibrate_servo(leg_index, joint_name, servo_min, joint.servo_max)
                
                joint.set_angle(joint.angle_max)
                print(f"Set {joint_name} of Leg {leg_index} to angle_max: {joint.angle_max}°")
                
                confirm_max = input("Is the servo_min calibration correct? (y/n): ").strip().lower()
                print()
                if confirm_max == 'y':
                    calibrated_max = True
                else:
                    print("Re-enter servo_min calibration value.")
            except ValueError:
                print("Invalid input. Please enter an integer value for servo_min.")

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
                
                confirm_zero = input("Is the zero angle calibration correct? (y/n): ").strip().lower()
                print()
                if confirm_zero == 'y':
                    calibrated_zero = True
                    return True
                else:
                    print("Zero angle calibrated incorrectly. Recalibrating...")
                    return False
            except ValueError as e:
                print(f"Error setting zero angle: {e}")
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