import os
import sys
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from maestro import MaestroUART
from robot import Leg

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

        self.load_calibration()

    def calibrate_all_servos(self):
        """
        Calibrate all servos by separating calibration steps into individual methods.
        Inverts the order of min and max calibration if the joint is inverted.
        """
        for i, leg in enumerate(self.legs):
            for joint_name in ['coxa', 'femur', 'tibia']:
                joint = getattr(leg, joint_name)
                calibration_success = False
                while not calibration_success:
                    if joint.invert:
                        self.calibrate_servo_min_inverted(i, joint_name)
                        self.calibrate_servo_max_inverted(i, joint_name)
                    else:
                        self.calibrate_servo_min(i, joint_name)
                        self.calibrate_servo_max(i, joint_name)
                    calibration_success = self.check_zero_angle(i, joint_name)
                # Set leg to default position after calibration
                # self.move_leg(i, -25, 0, 0)
                self.controller.go_home()
                print(f"Set Leg {i} to default position (0, 0, 0).")
        self.save_calibration()

    def calibrate_servo_min(self, leg_index, joint_name):
        """
        Calibrate servo_min for a specific joint of a leg.
        """
        calibrated_min = False
        while not calibrated_min:
            try:
                joint = getattr(self.legs[leg_index], joint_name)
                if joint.invert:
                    print(f"Expected angle_min ({joint.angle_min}°) corresponds to servo_max: {2000}")
                else:
                    print(f"Expected angle_min ({joint.angle_min}°) corresponds to servo_min: {992}")

                servo_min_input = int(input(f"Enter servo_min for Leg {leg_index} {joint_name} (992-2000): "))
                
                if not (992 <= servo_min_input <= 2000):
                    print("Error: servo_min must be between 992 and 2000.")
                    continue
                
                if joint.invert:
                    if servo_min_input >= (getattr(self.legs[leg_index], joint_name).servo_max // 4):
                        print("Error: Inverted servo_min must be greater than inverted servo_max.")
                        continue
                servo_min = servo_min_input * 4
                
                self.calibrate_servo(leg_index, joint_name, servo_min, getattr(self.legs[leg_index], joint_name).servo_max)
                
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

    def calibrate_servo_max(self, leg_index, joint_name):
        """
        Calibrate servo_max for a specific joint of a leg.
        """
        calibrated_max = False
        while not calibrated_max:
            try:
                joint = getattr(self.legs[leg_index], joint_name)
                if joint.invert:
                    print(f"Expected angle_max ({joint.angle_max}°) corresponds to servo_min: {992}")
                else:
                    print(f"Expected angle_max ({joint.angle_max}°) corresponds to servo_max: {2000}")

                servo_max_input = int(input(f"Enter servo_max for Leg {leg_index} {joint_name} (992-2000): "))
                
                if not (992 <= servo_max_input <= 2000):
                    print("Error: servo_max must be between 992 and 2000.")
                    continue

                if not joint.invert:
                    if servo_max_input <= (getattr(self.legs[leg_index], joint_name).servo_min // 4):
                        print("Error: servo_max must be greater than servo_min.")
                        continue
                
                servo_max = servo_max_input * 4
                
                self.calibrate_servo(leg_index, joint_name, getattr(self.legs[leg_index], joint_name).servo_min, servo_max)
                
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

    def calibrate_servo_min_inverted(self, leg_index, joint_name):
        """
        Calibrate servo_min (servo_max for inverted joints) for an inverted joint of a leg.
        """
        calibrated_min = False
        while not calibrated_min:
            try:
                print(f"Expected angle_min ({getattr(self.legs[leg_index], joint_name).angle_min}°) corresponds to servo_max: {2000}")
                servo_max_input = int(input(f"Enter servo_max for Leg {leg_index} {joint_name} (992-2000): "))
                
                if not (992 <= servo_max_input <= 2000):
                    print("Error: servo_max must be between 992 and 2000.")
                    continue

                servo_max = servo_max_input * 4
                
                self.calibrate_servo(leg_index, joint_name, getattr(self.legs[leg_index], joint_name).servo_min, servo_max)
                
                joint = getattr(self.legs[leg_index], joint_name)
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

    def calibrate_servo_max_inverted(self, leg_index, joint_name):
        """
        Calibrate servo_max (servo_min for inverted joints) for an inverted joint of a leg.
        """
        calibrated_max = False
        while not calibrated_max:
            try:
                print(f"Expected angle_max ({getattr(self.legs[leg_index], joint_name).angle_max}°) corresponds to servo_min: {992}")
                servo_min_input = int(input(f"Enter servo_min for Leg {leg_index} {joint_name} (992-2000): "))
                
                if not (992 <= servo_min_input <= 2000):
                    print("Error: servo_min must be between 992 and 2000.")
                    continue
                if servo_min_input >= (getattr(self.legs[leg_index], joint_name).servo_max // 4):
                    print("Error: Inverted servo_min must be less than inverted servo_max.")
                    continue

                servo_min = servo_min_input * 4
                
                self.calibrate_servo(leg_index, joint_name, servo_min, getattr(self.legs[leg_index], joint_name).servo_max)
                
                joint = getattr(self.legs[leg_index], joint_name)
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

    def check_zero_angle(self, leg_index, joint_name):
        """
        Check zero_angle for a specific joint of a leg.

        Returns:
            bool: True if calibration is correct, False otherwise.
        """
        calibrated_zero = False
        while not calibrated_zero:
            try:
                joint = getattr(self.legs[leg_index], joint_name)
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
        Save the current calibration settings to a JSON file.
        Overwrites the existing calibration.json file.
        """
        calibration_data = {}
        for i, leg in enumerate(self.legs):
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
        Load calibration data from calibration.json and update servo parameters.
        Ensures servo_min and servo_max are between 992 and 2000 and servo_min < servo_max before applying.
        """
        try:
            with open("calibration.json", "r") as f:
                calibration_data = json.load(f)
            for i, leg in enumerate(self.legs):
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
        Calibrate servo_min and servo_max for a specific joint of a leg.

        Args:
            leg_index (int): Index of the leg (0-5).
            joint (str): The joint to calibrate ('coxa', 'femur', or 'tibia').
            servo_min (int): New minimum servo value.
            servo_max (int): New maximum servo value.
        """
        if 0 <= leg_index < len(self.legs):
            leg = self.legs[leg_index]
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