import math
from hexapod import Joint

class Leg:
    def __init__(self, coxa_params, femur_params, tibia_params, controller):
        """
        Represents a single leg of the hexapod.

        Args:
            coxa_params (dict): Parameters for the coxa joint.
            femur_params (dict): Parameters for the femur joint.
            tibia_params (dict): Parameters for the tibia joint.
            controller (MaestroUART): Shared MaestroUART instance.
        """
        self.coxa = Joint(controller, **coxa_params)
        self.femur = Joint(controller, **femur_params)
        self.tibia = Joint(controller, **tibia_params)

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
        # Calculate the horizontal distance to the target using coxa length
        horizontal_distance = math.hypot(x, y) - self.coxa.length

        # Angle for the coxa joint
        theta1 = math.atan2(y, x)

        # Distance from femur joint to foot position using femur length
        r = math.hypot(horizontal_distance, z)
        if r > (self.femur.length + self.tibia.length):
            raise ValueError("Target is out of reach.")

        # Inverse kinematics calculations
        cos_theta3 = (self.femur.length**2 + self.tibia.length**2 - r**2) / (2 * self.femur.length * self.tibia.length)
        theta3 = math.acos(cos_theta3)

        cos_theta2 = (self.femur.length**2 + r**2 - self.tibia.length**2) / (2 * self.femur.length * r)
        theta2 = math.atan2(z, horizontal_distance) - math.acos(cos_theta2)

        theta1_deg = math.degrees(theta1)
        theta2_deg = math.degrees(theta2)
        theta3_deg = math.degrees(theta3)

        return theta1_deg, theta2_deg, theta3_deg

    def move_to(self, x, y, z, speed=32, accel=5):
        """
        Move the leg to the desired position.

        Args:
            x, y, z (float): Target coordinates.
            speed (int): Servo speed.
            accel (int): Servo acceleration.
        """
        theta1, theta2, theta3 = self.compute_inverse_kinematics(x, y, z)

        self.coxa.set_angle(theta1, speed, accel)
        self.femur.set_angle(-theta2, speed, accel)
        self.tibia.set_angle(theta3, speed, accel)