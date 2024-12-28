import math
from robot import Joint

class Leg:
    def __init__(self, coxa_params, femur_params, tibia_params, controller, end_effector_offset):
        """
        Initialize a single leg of the hexapod robot.

        Parameters:
            coxa_params (dict): Configuration parameters for the coxa joint, including 'z_offset' to define the vertical offset of the coxa relative to the base.
            femur_params (dict): Configuration parameters for the femur joint.
            tibia_params (dict): Configuration parameters for the tibia joint, including 'x_offset' - horizontal offset of the tibia relative to the base.
            controller (MaestroUART): The shared MaestroUART controller instance for servo communication.
            end_effector_offset (tuple): (x, y, z) offset for the end effector's position relative to the leg's base.
        """
        self.coxa_params = dict(coxa_params)
        self.femur_params = dict(femur_params)
        self.tibia_params = dict(tibia_params)
        
        self.coxa_z_offset = self.coxa_params.pop('z_offset', 0.0)
        self.tibia_x_offset = self.tibia_params.pop('x_offset', 0.0)
        
        self.coxa = Joint(controller, **self.coxa_params)
        self.femur = Joint(controller, **self.femur_params)
        self.tibia = Joint(controller, **self.tibia_params)
        self.end_effector_offset = end_effector_offset
        # print(f"Initializing Leg with coxa_params: {coxa_params}, femur_params: {femur_params}, tibia_params: {tibia_params}")

    def compute_inverse_kinematics(self, x, y, z):
        """
        Calculate the necessary joint angles to position the foot at the specified coordinates.

        Args:
            x (float): Desired X position of the foot.
            y (float): Desired Y position of the foot.
            z (float): Desired Z position of the foot.

        Returns:
            tuple: A tuple containing the angles for the coxa, femur, and tibia joints in degrees.

        Raises:
            ValueError: If the target position is beyond the leg's maximum reach.
        """
        print(f"Computing inverse kinematics for position x: {x}, y: {y}, z: {z}")
        # Compensate for end effector offset
        ox, oy, oz = self.end_effector_offset
        x += ox
        y += oy
        z += oz
        print(f"Adjusted position for IK - x: {x}, y: {y}, z: {z}")

        # Calculate the angle for the coxa joint based on x and y positions
        coxa_angle = math.atan2(x, y)
        print(f"coxa_angle (radians): {coxa_angle}")

        # Calculate the horizontal distance to the target position
        R = math.hypot(x, y)
        print(f"horizontal_distance: {R}")

        # Distance from femur joint to foot adjusted for coxa length offset
        F = math.hypot(R - self.coxa.length, z - self.coxa_z_offset)
        print(f"F (distance from femur joint to foot position): {F}")
        
        max_reach = self.femur.length + self.tibia.length
        print(f"Maximum reach: {max_reach}")
        
        if F > max_reach:
            raise ValueError("Target is out of reach.")

        # Inverse kinematics calculations to find joint angles
        alpha1_tan = (R - self.coxa.length) / (z - self.coxa_z_offset)
        alpha2_cos = (self.tibia.length**2 - self.femur.length**2 - F**2) / (-2 * self.femur.length * F)
        alpha1 = math.atan(alpha1_tan)
        alpha2 = math.acos(alpha2_cos)
        print(f"alpha1 (radians): {alpha1}")
        print(f"alpha2 (radians): {alpha2}")

        beta_cos = (F**2 - self.femur.length**2 - self.tibia.length**2) / (-2 * self.femur.length * self.tibia.length)
        beta = math.acos(beta_cos)
        print(f"beta (radians): {beta}")

        coxa_angle_deg = math.degrees(coxa_angle)
        print(f"coxa_angle_deg: {coxa_angle_deg}")

        femur_angle_deg = math.degrees(alpha1) + math.degrees(alpha2) - 90
        print(f"femur_angle_deg: {femur_angle_deg}")

        tibia_angle_deg = math.degrees(beta) - 90
        print(f"tibia_angle_deg: {tibia_angle_deg}")

        print(f"Calculated angles - coxa_angle_deg: {coxa_angle_deg}, femur_angle_deg: {femur_angle_deg}, tibia_angle_deg: {tibia_angle_deg}")
        return coxa_angle_deg, femur_angle_deg, tibia_angle_deg

    def move_to(self, x, y, z, speed=32, accel=5):
        """
        Move the leg's end effector to the specified (x, y, z) coordinates.

        Args:
            x (float): Target X coordinate.
            y (float): Target Y coordinate.
            z (float): Target Z coordinate.
            speed (int, optional): Speed setting for servo movement. Defaults to 32.
            accel (int, optional): Acceleration setting for servo movement. Defaults to 5.
        """
        print(f"Moving to x: {x}, y: {y}, z: {z} with speed: {speed}, accel: {accel}")

        coxa_angle, femur_angle, tibia_angle = self.compute_inverse_kinematics(x, y, z)

        self.coxa.set_angle(coxa_angle, speed, accel)
        self.femur.set_angle(femur_angle, speed, accel)
        self.tibia.set_angle(tibia_angle, speed, accel)
        print(f"Set angles - coxa: {coxa_angle}, femur: {femur_angle}, tibia: {tibia_angle}")