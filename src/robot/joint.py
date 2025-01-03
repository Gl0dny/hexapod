class Joint:
    DEFAULT_SPEED = 32
    DEFAULT_ACCEL = 5

    def __init__(self, controller, length, channel, angle_min, angle_max, servo_min=992*4, servo_max=2000*4, invert=False):
        """
        Represents a single joint controlled by a servo.

        Args:
            controller (MaestroUART): Shared MaestroUART instance.
            length (float): Length of the joint segment.
            channel (int): Servo channel for the joint.
            angle_min (float): Minimum joint angle in degrees - joint limitation.
            angle_max (float): Maximum joint angle in degrees - joint limitation.
            servo_min (int): Minimum servo target value - hardware related.
            servo_max (int): Maximum servo target value - hardware related.
            invert (bool): Whether to invert the angle limits for the joint.
        """
        self.controller = controller
        self.length = length
        self.channel = channel
        self.angle_min = angle_min
        self.angle_max = angle_max
        self.servo_min = servo_min
        self.servo_max = servo_max
        self.invert = invert

    def set_angle(self, angle, speed=DEFAULT_SPEED, accel=DEFAULT_ACCEL):
        """
        Set the joint to a specific angle.

        Args:
            angle (float): Target angle in degrees.
            speed (int): Speed setting for the servo.
            accel (int): Acceleration setting for the servo.
        """
        # Invert the angle if necessary
        if self.invert:
            angle = -angle

        # Ensure the angle is within limits
        if angle < self.angle_min or angle > self.angle_max:
            raise ValueError(f"Angle {angle}° is out of limits ({self.angle_min}° to {self.angle_max}°).")

        # Convert angle to servo target
        target = self.angle_to_servo_target(angle)

        # Set speed and acceleration
        self.controller.set_speed(self.channel, speed)
        self.controller.set_acceleration(self.channel, accel)

        # Move the servo to the target position
        self.controller.set_target(self.channel, target)

    def angle_to_servo_target(self, angle):
        """
        Map a joint angle to the servo target value.

        Args:
            angle (float): Joint angle in degrees.

        Returns:
            int: Servo target value in quarter-microseconds.
        """
        # Map the angle to the servo's range
        angle_range = self.angle_max - self.angle_min
        servo_range = self.servo_max - self.servo_min
        target = self.servo_min + servo_range * ((angle - self.angle_min) / angle_range)
        return int(target)

    def update_calibration(self, servo_min, servo_max):
        """
        Update the servo_min and servo_max calibration values.

        Args:
            servo_min (int): New minimum servo target value.
            servo_max (int): New maximum servo target value.
        """
        self.servo_min = servo_min
        self.servo_max = servo_max
        print(f"Updated calibration for channel {self.channel}: servo_min={self.servo_min}, servo_max={self.servo_max}")