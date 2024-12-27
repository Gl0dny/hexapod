import math
from robot import Joint

class Leg:
    def __init__(self, coxa_params, femur_params, tibia_params, controller, end_effector_offset):
        """
        Represents a single leg of the hexapod.

        Args:
            coxa_params (dict): Parameters for the coxa joint, including 'z_offset' to define
                the vertical offset of the coxa relative to the base plane.
            femur_params (dict): Parameters for the femur joint.
            tibia_params (dict): Parameters for the tibia joint.
            controller (MaestroUART): Shared MaestroUART instance.
            end_effector_offset (tuple): Offset for the end effector position (x,y,z).
        """
        coxa_params_copy = dict(coxa_params)
        self.coxa_z_offset = coxa_params_copy.pop('z_offset', 0.0)
        tiba_params_copy = dict(tibia_params)
        self.tibia_x_offset = tiba_params_copy.pop('x_offset', 0.0)
        self.coxa = Joint(controller, **coxa_params_copy)
        self.femur = Joint(controller, **femur_params)
        self.tibia = Joint(controller, **tiba_params_copy)
        self.end_effector_offset = end_effector_offset
        # print(f"Initializing Leg with coxa_params: {coxa_params}, femur_params: {femur_params}, tibia_params: {tibia_params}")

    def compute_inverse_kinematics(self, x, y, z):
        """
        Compute the joint angles for the desired foot position.

        Args:
            x (float): X coordinate of the foot position.
            y (float): Y coordinate of the foot position.
            z (float): Z coordinate of the foot position.

        Returns:
            tuple: (theta1, theta2, theta3) in degrees.
        """
        print(f"Computing inverse kinematics for position x: {x}, y: {y}, z: {z}")
        # Compensate for end effector offset
        ox, oy, oz = self.end_effector_offset
        x += ox
        y += oy
        z += oz
        print(f"Adjusted position for IK - x: {x}, y: {y}, z: {z}")

        # Angle for the coxa joint
        theta1 = math.atan2(x, y)

        # Calculate the horizontal distance to the target
        R = math.hypot(x, y)
        print(f"horizontal_distance: {R}")

        # Distance from femur joint to foot adjusted for coxa length offset
        F = math.hypot(R - self.coxa.length, z - self.coxa_z_offset)
        print(f"F (distance from femur joint to foot position): {F}")
        
        max_reach = self.femur.length + self.tibia.length
        print(f"Maximum reach: {max_reach}")
        
        if F > max_reach:
            raise ValueError("Target is out of reach.")

        # Inverse kinematics calculations
        # cos_theta3 = (self.femur.length**2 + self.tibia.length**2 - r**2) / (2 * self.femur.length * self.tibia.length)
        # print(f"cos_theta3: {cos_theta3}")
        # theta3 = math.acos(cos_theta3)

        # cos_theta2 = (self.femur.length**2 + r**2 - self.tibia.length**2) / (2 * self.femur.length * r)
        # print(f"cos_theta2: {cos_theta2}")
        # theta2 = math.atan2(z, R - self.coxa.length) - math.acos(cos_theta2)

        theta3 = 0
        theta2 = 0

        theta1_deg = math.degrees(theta1)
        print(f"theta1 (radians): {theta1}")
        print(f"theta1_deg: {theta1_deg}")

        theta2_deg = math.degrees(theta2)
        print(f"theta2 (radians): {theta2}")
        print(f"theta2_deg: {theta2_deg}")

        theta3_deg = math.degrees(theta3)
        print(f"theta3 (radians): {theta3}")
        print(f"theta3_deg: {theta3_deg}")

        # Shift femur and tibia by 90 degrees
        theta2_user = theta2_deg
        theta3_user = theta3_deg

        print(f"Calculated angles - theta1_deg: {theta1_deg}, theta2_user: {theta2_user}, theta3_user: {theta3_user}")
        return theta1_deg, theta2_user, theta3_user

    def move_to(self, x, y, z, speed=32, accel=5):
        """
        Move the leg to the desired position.

        Args:
            x, y, z (float): Target coordinates.
            speed (int): Servo speed.
            accel (int): Servo acceleration.
        """
        print(f"Moving to x: {x}, y: {y}, z: {z} with speed: {speed}, accel: {accel}")

        theta1, theta2, theta3 = self.compute_inverse_kinematics(x, y, z)

        self.coxa.set_angle(theta1, speed, accel)
        self.femur.set_angle(theta2, speed, accel)
        self.tibia.set_angle(theta3, speed, accel)
        print(f"Set angles - coxa: {theta1}, femur: {theta2}, tibia: {theta3}")