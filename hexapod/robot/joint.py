"""
Joint control system for hexapod robot servos.

This module defines the Joint class which represents a single servo joint
in the hexapod robot. It handles servo control, position management,
and communication with the Maestro servo controller board.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import logging

from hexapod.utils import map_range
from hexapod.interface import get_custom_logger

if TYPE_CHECKING:
    from typing import Optional
    from hexapod.maestro import MaestroUART

logger = get_custom_logger("robot_logger")


class Joint:
    """
    Represents a servo motor joint in the hexapod robot.

    Attributes:
        servo_min (int): Minimum servo input value.
        servo_max (int): Maximum servo input value.
        angle_min (float): Minimum angle for the joint in degrees.
        angle_max (float): Maximum angle for the joint in degrees.
        invert (bool): Indicates if the joint is inverted.
        speed (int): Default speed for servo movements.
        accel (int): Default acceleration for servo movements.
    """

    DEFAULT_SPEED = 32  # Speed setting for the servo in units of (0.25us/10ms). A speed of 32 means 0.8064us/ms.
    DEFAULT_ACCEL = 5  # Acceleration setting for the servo in units of (0.25us/10ms/80ms). A value of 5 means 0.0016128us/ms/ms.

    SERVO_INPUT_MIN = 992  # Minimum servo pulse width in microseconds as defined by the Maestro controller.
    SERVO_INPUT_MAX = 2000  # Maximum servo pulse width in microseconds as defined by the Maestro controller.
    SERVO_UNIT_MULTIPLIER = (
        4  # Multiplier to convert microseconds to quarter-microseconds.
    )

    def __init__(
        self,
        controller: MaestroUART,
        length: float,
        channel: int,
        angle_min: float,
        angle_max: float,
        servo_min: int = SERVO_INPUT_MIN * SERVO_UNIT_MULTIPLIER,
        servo_max: int = SERVO_INPUT_MAX * SERVO_UNIT_MULTIPLIER,
        angle_limit_min: Optional[float] = None,
        angle_limit_max: Optional[float] = None,
        invert: bool = False,
    ) -> None:
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
        logger.debug(
            f"Validating angle: {angle}°, Check custom limits: {check_custom_limits}"
        )

        # Always check default limits
        if not (self.angle_min <= angle <= self.angle_max):
            logger.error(
                f"{self} angle {angle}° is out of bounds ({self.angle_min}° to {self.angle_max}°)."
            )
            raise ValueError(
                f"{self} angle {angle}° is out of bounds ({self.angle_min}° to {self.angle_max}°)."
            )

        # Only check custom limits if check_custom_limits=True
        if check_custom_limits:
            if self.angle_limit_min is not None and angle < self.angle_limit_min:
                logger.error(
                    f"{self} angle {angle}° is below custom limit ({self.angle_limit_min}°)."
                )
                raise ValueError(
                    f"{self} angle {angle}° is below custom limit ({self.angle_limit_min}°)."
                )
            if self.angle_limit_max is not None and angle > self.angle_limit_max:
                logger.error(
                    f"{self} angle {angle}° is above custom limit ({self.angle_limit_max}°)."
                )
                raise ValueError(
                    f"{self} angle {angle}° is above custom limit ({self.angle_limit_max}°)."
                )

    def set_angle(self, angle: float, check_custom_limits: bool = True) -> None:
        """
        Set the joint to a specific angle.

        Args:
            angle (float): Target angle in degrees.
            check_custom_limits (bool): Whether to enforce angle limits.
        """
        logger.debug(
            f"Setting angle to {angle}° with speed/accel set at hexapod level. Invert: {self.invert}"
        )
        if self.invert:
            angle = -angle
            logger.debug(f"Inverted angle: {angle}°")

        self._validate_angle(angle, check_custom_limits)

        target = self.angle_to_servo_target(angle)
        logger.debug(f"Calculated servo target: {target}")

        self.controller.set_target(self.channel, target)
        logger.debug(f"Angle set to {angle}°, Servo target set to {target}.")

    def angle_to_servo_target(self, angle: float) -> int:
        """
        Map a joint angle to the servo target value.

        Args:
            angle (float): Joint angle in degrees.

        Returns:
            int: Servo target value in quarter-microseconds.
        """
        target = map_range(
            int(angle),
            int(self.angle_min),
            int(self.angle_max),
            self.servo_min,
            self.servo_max,
        )
        logger.debug(f"Mapping angle {angle}° to servo target {int(target)}")
        return int(target)

    def update_calibration(self, servo_min: int, servo_max: int) -> None:
        """
        Update the servo_min and servo_max calibration values.

        Args:
            servo_min (int): New minimum servo target value.
            servo_max (int): New maximum servo target value.
        """
        self.servo_min = servo_min
        self.servo_max = servo_max
        logger.debug(
            f"Updated calibration for channel {self.channel}: servo_min={self.servo_min}, servo_max={self.servo_max}"
        )
