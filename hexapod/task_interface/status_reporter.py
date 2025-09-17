"""
Status reporting system for hexapod robot tasks.

This module provides the StatusReporter class which handles real-time status
reporting for robot tasks and operations. It manages status updates, logging,
and provides a unified interface for reporting task progress and system state.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import logging
from datetime import datetime

if TYPE_CHECKING:
    from hexapod.robot import Hexapod

logger = logging.getLogger("task_interface_logger")


class StatusReporter:
    """
    Handles comprehensive system status reporting for the hexapod.

    This class provides methods to gather and format various types of status information
    including system info, movement status, calibration status, IMU data, gait status,
    and leg positions.
    """

    def __init__(self):
        """Initialize the StatusReporter."""
        pass

    def get_complete_status(self, hexapod: Hexapod) -> str:
        """
        Get a complete status report for the hexapod.

        Args:
            hexapod: The hexapod instance to get status from

        Returns:
            str: Complete formatted status report
        """
        # Get all status sections
        status_sections = [
            self._get_system_info(hexapod),
            self._get_calibration_status(hexapod),
            self._get_imu_status(hexapod),
            self._get_gait_status(hexapod),
            self._get_movement_status(hexapod),
            self._get_leg_positions_status(hexapod),
        ]

        # Combine all sections into one message
        status_report = "\n\n=== HEXAPOD SYSTEM STATUS ===\n\n"
        status_report += "\n\n".join(status_sections)
        status_report += "\n\n=== END STATUS REPORT ==="

        return status_report

    def _get_imu_status(self, hexapod: Hexapod) -> str:
        """Get current IMU sensor status."""
        try:
            accel_x, accel_y, accel_z = hexapod.imu.get_acceleration()
            gyro_x, gyro_y, gyro_z = hexapod.imu.get_gyroscope()
            temp = hexapod.imu.get_temperature()

            return (
                f"IMU Status:\n"
                f"  Acceleration: X={accel_x:+.2f} Y={accel_y:+.2f} Z={accel_z:+.2f} g\n"
                f"  Gyroscope: X={gyro_x:+.2f} Y={gyro_y:+.2f} Z={gyro_z:+.2f} °/s\n"
                f"  Temperature: {temp:.1f}°C"
            )
        except Exception as e:
            logger.error(f"Error reading IMU data: {e}")
            return "IMU Status: Error reading sensor data"

    def _get_movement_status(self, hexapod: Hexapod) -> str:
        """Get current movement and servo status."""
        try:
            is_moving = hexapod._get_moving_state()
            movement_status = "Moving" if is_moving else "Stationary"

            return (
                f"Movement Status:\n"
                f"  State: {movement_status}\n"
                f"  Servo Speed: {hexapod.speed}%\n"
                f"  Servo Acceleration: {hexapod.accel}%"
            )
        except Exception as e:
            logger.error(f"Error reading movement status: {e}")
            return "Movement Status: Error reading servo data"

    def _get_leg_positions_status(self, hexapod: Hexapod) -> str:
        """Get current leg positions and angles."""
        try:
            status_lines = ["Leg Positions:"]

            for i, (pos, angles) in enumerate(
                zip(hexapod.current_leg_positions, hexapod.current_leg_angles)
            ):
                x, y, z = pos
                coxa, femur, tibia = angles
                status_lines.append(
                    f"  Leg {i}: Pos({x:6.1f}, {y:6.1f}, {z:6.1f}) mm | "
                    f"Angles({coxa:5.1f}°, {femur:5.1f}°, {tibia:5.1f}°)"
                )

            return "\n".join(status_lines)
        except Exception as e:
            logger.error(f"Error reading leg positions: {e}")
            return "Leg Positions: Error reading position data"

    def _get_gait_status(self, hexapod: Hexapod) -> str:
        """Get current gait generator status if active."""
        try:
            gait_gen = hexapod.gait_generator

            if not hasattr(gait_gen, "current_state") or gait_gen.current_state is None:
                return "Gait Status: No active gait"

            current_state = gait_gen.current_state
            status_lines = ["Gait Status:"]

            # Get gait type
            gait_type = type(gait_gen).__name__
            status_lines.append(f"  Type: {gait_type}")

            # Get current phase if available
            if hasattr(current_state, "phase"):
                status_lines.append(f"  Phase: {current_state.phase}")

            # Get swing/stance legs if available
            if hasattr(current_state, "swing_legs"):
                status_lines.append(f"  Swing Legs: {current_state.swing_legs}")
            if hasattr(current_state, "stance_legs"):
                status_lines.append(f"  Stance Legs: {current_state.stance_legs}")

            # Get timing parameters if available
            if hasattr(current_state, "dwell_time"):
                status_lines.append(f"  Dwell Time: {current_state.dwell_time:.2f}s")

            return "\n".join(status_lines)
        except Exception as e:
            logger.error(f"Error reading gait status: {e}")
            return "Gait Status: Error reading gait data"

    def _get_calibration_status(self, hexapod: Hexapod) -> str:
        """Get calibration status with last calibration date."""
        try:
            calibration = hexapod.calibration
            calibration_file = calibration.calibration_data_path

            # Check if calibration file exists and get its modification time
            if calibration_file.exists():
                # Get file modification time
                mtime = calibration_file.stat().st_mtime
                last_calibration_date = datetime.fromtimestamp(mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                # Check calibration status
                if hasattr(calibration, "is_calibrated"):
                    status = (
                        "Calibrated" if calibration.is_calibrated else "Not calibrated"
                    )
                else:
                    status = "Calibrated"  # If file exists, assume it's calibrated

                return (
                    f"Calibration Status:\n"
                    f"  Status: {status}\n"
                    f"  Last Calibration: {last_calibration_date}\n"
                    f"  File: {calibration_file.name}"
                )
            else:
                return "Calibration Status: Not calibrated (no calibration file found)"

        except Exception as e:
            logger.error(f"Error reading calibration status: {e}")
            return "Calibration Status: Error reading calibration data"

    def _get_system_info(self, hexapod: Hexapod) -> str:
        """Get basic system information."""
        try:
            return (
                f"System Info:\n"
                f"  Hexagon Side Length: {hexapod.hexagon_side_length} mm\n"
                f"  Controller Channels: {hexapod.CONTROLLER_CHANNELS}\n"
                f"  End Effector Radius: {hexapod.end_effector_radius:.1f} mm"
            )
        except Exception as e:
            logger.error(f"Error reading system info: {e}")
            return "System Info: Error reading system data"
