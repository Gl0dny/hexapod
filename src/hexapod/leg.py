# src/control/leg.py

import math
from maestro.maestro_uart import MaestroUART

class Leg:
    def __init__(self, coxa_length, femur_length, tibia_length,
                 coxa_channel, femur_channel, tibia_channel,
                 servo_min=992*4, servo_max=2000*4, angle_min=-90, angle_max=90):
        """
        Represents a single leg of the hexapod.

        Args:
            coxa_length (float): Length of the coxa segment.
            femur_length (float): Length of the femur segment.
            tibia_length (float): Length of the tibia segment.
            coxa_channel (int): Servo channel for the coxa joint.
            femur_channel (int): Servo channel for the femur joint.
            tibia_channel (int): Servo channel for the tibia joint.
            servo_min (int): Minimum servo target value - hardware related.
            servo_max (int): Maximum servo target value - hardware related.
            angle_min (float): Minimum joint angle in degrees - specific joint limitation ( should be defined by user ).
            angle_max (float): Maximum joint angle in degrees - specific joint limitation ( should be defined by user ).
        """
        self.coxa_length = coxa_length
        self.femur_length = femur_length
        self.tibia_length = tibia_length
        self.coxa_channel = coxa_channel
        self.femur_channel = femur_channel
        self.tibia_channel = tibia_channel
        self.servo_min = servo_min
        self.servo_max = servo_max
        self.angle_min = angle_min
        self.angle_max = angle_max
        self.mu = MaestroUART('/dev/ttyS0', 9600)

    def compute_inverse_kinematics(self, x, y, z):
        pass

    def angle_to_servo_target(self, angle):
        """
        Map a joint angle to the servo target value.

        Args:
            angle (float): Joint angle in degrees.

        Returns:
            int: Servo target value in quarter-microseconds.

        Example:
        angle = max(min(-90, 90), -90)  # angle = -90
        target = 1000 + (2000 - 1000) * ((-90 - (-90)) / (90 - (-90)))
                = 1000 + 1000 * (0 / 180)
                = 1000 + 0
                = 1000
        """
        # Ensure the angle is within the specified range
        angle = max(min(angle, self.angle_max), self.angle_min)
        # Map the angle to the servo's range
        target = self.servo_min + (self.servo_max - self.servo_min) * ((angle - self.angle_min) / (self.angle_max - self.angle_min))
        return int(target)

    def move_to(self, x, y, z, speed=32, accel=5):
        """
        Move the leg to the desired foot position.

        Args:
            x (float): X coordinate of the foot position.
            y (float): Y coordinate of the foot position.
            z (float): Z coordinate of the foot position.
            speed (int): Speed setting for the servos.
            accel (int): Acceleration setting for the servos.
        """
        # Compute joint angles
        theta1, theta2, theta3 = self.compute_inverse_kinematics(x, y, z)

        # Convert angles to servo targets
        coxa_target = self.angle_to_servo_target(theta1)
        femur_target = self.angle_to_servo_target(theta2)
        tibia_target = self.angle_to_servo_target(theta3)

        # Set speed and acceleration
        self.mu.set_speed(self.coxa_channel, speed)
        self.mu.set_acceleration(self.coxa_channel, accel)
        self.mu.set_speed(self.femur_channel, speed)
        self.mu.set_acceleration(self.femur_channel, accel)
        self.mu.set_speed(self.tibia_channel, speed)
        self.mu.set_acceleration(self.tibia_channel, accel)

        # Move the servos to the calculated positions
        self.mu.set_target(self.coxa_channel, coxa_target)
        self.mu.set_target(self.femur_channel, femur_target)
        self.mu.set_target(self.tibia_channel, tibia_target)