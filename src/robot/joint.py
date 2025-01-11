import logging

logger = logging.getLogger("robot_logger")

class Joint:
    DEFAULT_SPEED = 32  # Speed setting for the servo in units of (0.25us/10ms). A speed of 32 means 0.8064us/ms.
    DEFAULT_ACCEL = 5   # Acceleration setting for the servo in units of (0.25us/10ms/80ms). A value of 5 means 0.0016128us/ms/ms.

    def __init__(self, controller, length, channel, angle_min, angle_max, servo_min=992*4, servo_max=2000*4, angle_limit_min=None, angle_limit_max=None, invert=False):
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
            angle_limit_min (float, optional): Custom minimum joint angle in degrees to limit joint movement.
            angle_limit_max (float, optional): Custom maximum joint angle in degrees to limit joint movement.
            invert (bool): Whether to invert the angle limits for the joint.
        """
        self.controller = controller
        self.length = length
        self.channel = channel
        self.angle_min = angle_min
        self.angle_max = angle_max
        self.servo_min = servo_min
        self.servo_max = servo_max
        self.angle_limit_min = angle_limit_min
        self.angle_limit_max = angle_limit_max
        self.invert = invert

    def _validate_angle(self, angle: float, check_custom_limits: bool) -> None:
        """
        Validate the angle against default and custom limits.

        Args:
            angle (float): The angle to validate.
            check_custom_limits (bool): Whether to enforce custom angle limits.

        Raises:
            ValueError: If the angle is outside the allowed limits.
        """
        logger.debug(f"Validating angle: {angle}°, Check custom limits: {check_custom_limits}")
        if not check_custom_limits:
            return

        if not (self.angle_min <= angle <= self.angle_max):
            logger.error(f"{self} angle {angle}° is out of bounds ({self.angle_min}° to {self.angle_max}°).")
            raise ValueError(f"{self} angle {angle}° is out of bounds ({self.angle_min}° to {self.angle_max}°).")
        
        if self.angle_limit_min is not None and angle < self.angle_limit_min:
            logger.error(f"{self} angle {angle}° is below custom limit ({self.angle_limit_min}°).")
            raise ValueError(f"{self} angle {angle}° is below custom limit ({self.angle_limit_min}°).")
        if self.angle_limit_max is not None and angle > self.angle_limit_max:
            logger.error(f"{self} angle {angle}° is above custom limit ({self.angle_limit_max}°).")
            raise ValueError(f"{self} angle {angle}° is above custom limit ({self.angle_limit_max}°).")

    def set_angle(self, angle, speed=DEFAULT_SPEED, accel=DEFAULT_ACCEL, check_custom_limits=True):
        """
        Set the joint to a specific angle.

        Args:
            angle (float): Target angle in degrees.
            speed (int): Speed setting for the servo.
            accel (int): Acceleration setting for the servo.
            check_custom_limits (bool): Whether to enforce angle limits.
        """
        logger.info(f"Setting angle to {angle}° with speed={speed} and accel={accel}. Invert: {self.invert}")
        if self.invert:
            angle = -angle
            logger.debug(f"Inverted angle: {angle}°")

        self._validate_angle(angle, check_custom_limits)

        target = self.angle_to_servo_target(angle)
        logger.debug(f"Calculated servo target: {target}")

        self.controller.set_speed(self.channel, speed)
        self.controller.set_acceleration(self.channel, accel)

        self.controller.set_target(self.channel, target)
        logger.info(f"Angle set to {angle}°, Servo target set to {target}.")

    def angle_to_servo_target(self, angle):
        """
        Map a joint angle to the servo target value.

        Args:
            angle (float): Joint angle in degrees.

        Returns:
            int: Servo target value in quarter-microseconds.
        """
        angle_range = self.angle_max - self.angle_min
        servo_range = self.servo_max - self.servo_min
        target = self.servo_min + servo_range * ((angle - self.angle_min) / angle_range)
        logger.debug(f"Mapping angle {angle}° to servo target {int(target)}")
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
        logger.debug(f"Updated calibration for channel {self.channel}: servo_min={self.servo_min}, servo_max={self.servo_max}")