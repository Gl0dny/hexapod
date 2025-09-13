"""
Balance compensation system for the hexapod robot.

This module provides real-time balance compensation using IMU data to maintain
stable posture during movement. It continuously monitors the robot's orientation
and adjusts leg positions to counteract tilting and maintain balance.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import threading
import time

import numpy as np

if TYPE_CHECKING:
    from typing import Tuple, Optional
    from hexapod.robot import Hexapod

class BalanceCompensator:
    """Handles IMU-based balance compensation for the hexapod robot.
    
    This class implements a compensation system that counteracts IMU readings
    by adjusting the robot's body orientation to maintain stability.
    """
    
    def __init__(self, hexapod: Hexapod, compensation_factor: float = 0.1, update_rate: float = 0.1,
                 min_movement_threshold: float = 0.5):
        """
        Initialize the balance compensator.
        
        Args:
            hexapod: The hexapod instance to control
            compensation_factor: Base scaling factor for compensation (0.0 to 1.0)
            update_rate: How often to update compensation (seconds)
            min_movement_threshold: Minimum angle to trigger movement (degrees)
        """
        self.hexapod = hexapod
        self.compensation_factor = compensation_factor
        self.update_rate = update_rate
        self.min_movement_threshold = min_movement_threshold
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.last_compensation = (0.0, 0.0, 0.0)  # (roll, pitch, yaw)
        self.max_compensation_angle = 5.0  # Maximum compensation angle in degrees
        
    def start(self) -> None:
        """Start the balance compensation thread."""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._compensation_loop)
            self.thread.daemon = True
            self.thread.start()
            print("Balance compensation started")
    
    def stop(self) -> None:
        """Stop the balance compensation thread."""
        self.is_running = False
        if self.thread:
            self.thread.join()
            self.thread = None
        print("Balance compensation stopped")
    
    def _get_tilt_angles(self) -> Tuple[float, float, float]:
        """Get current tilt angles from IMU."""
        accel_x, accel_y, accel_z = self.hexapod.imu.get_acceleration()
        
        # Calculate tilt angles (in radians)
        roll = np.arctan2(accel_y, accel_z)
        pitch = np.arctan2(-accel_x, np.sqrt(accel_y**2 + accel_z**2))
        yaw = 0.0  # Yaw can't be determined from accelerometer alone
        
        return roll, pitch, yaw
    
    def _apply_compensation(self, roll: float, pitch: float, yaw: float) -> None:
        """Apply compensation to the hexapod."""
        try:
            # Convert to degrees and apply compensation factor
            roll_deg = np.degrees(roll) * self.compensation_factor
            pitch_deg = np.degrees(pitch) * self.compensation_factor
            yaw_deg = np.degrees(yaw) * self.compensation_factor
            
            # Limit the compensation angles
            roll_deg = np.clip(roll_deg, -self.max_compensation_angle, self.max_compensation_angle)
            pitch_deg = np.clip(pitch_deg, -self.max_compensation_angle, self.max_compensation_angle)
            yaw_deg = np.clip(yaw_deg, -self.max_compensation_angle, self.max_compensation_angle)
            
            # Get gyroscope readings to detect movement
            gyro_x, gyro_y, gyro_z = self.hexapod.imu.get_gyroscope()
            gyro_magnitude = np.sqrt(gyro_x**2 + gyro_y**2 + gyro_z**2)
            
            # Calculate how far we are from the last compensation
            roll_diff = abs(roll_deg - self.last_compensation[0])
            pitch_diff = abs(pitch_deg - self.last_compensation[1])
            
            # Only consider returning to stable position if:
            # 1. The tilt angles are small (based on accelerometer)
            # 2. We're not moving (based on gyroscope)
            if (abs(roll_deg) < 1.0 and abs(pitch_deg) < 1.0 and 
                gyro_magnitude < 5.0):  # 5.0 degrees/second threshold for movement
                # Gradually return to zero
                target_roll = self.last_compensation[0] * 0.8  # Reduce by 20%
                target_pitch = self.last_compensation[1] * 0.8
                print(f"Returning to stable position: roll={target_roll:.1f}°, pitch={target_pitch:.1f}°")
                self.hexapod.move_body(
                    tx=0.0,
                    ty=0.0,
                    tz=0.0,
                    roll=target_roll,
                    pitch=target_pitch,
                    yaw=0.0
                )
                self.last_compensation = (target_roll, target_pitch, 0.0)
            # For significant tilts or movement, apply proportional compensation
            elif (abs(roll_deg) > self.min_movement_threshold or 
                  abs(pitch_deg) > self.min_movement_threshold or 
                  gyro_magnitude > 5.0):  # Only compensate if actually moving
                print(f"Applying compensation: roll={roll_deg:.1f}°, pitch={pitch_deg:.1f}°, yaw={yaw_deg:.1f}°")
                self.hexapod.move_body(
                    tx=0.0,
                    ty=0.0,
                    tz=0.0,
                    roll=roll_deg,
                    pitch=pitch_deg,
                    yaw=yaw_deg
                )
                self.last_compensation = (roll_deg, pitch_deg, yaw_deg)
        except Exception as e:
            print(f"Error in balance compensation: {e}")
            # If we hit an error, try to return to last known good position
            try:
                self.hexapod.move_body(
                    tx=0.0,
                    ty=0.0,
                    tz=0.0,
                    roll=self.last_compensation[0],
                    pitch=self.last_compensation[1],
                    yaw=self.last_compensation[2]
                )
            except Exception as e2:
                print(f"Error recovering from compensation error: {e2}")
    
    def _compensation_loop(self) -> None:
        """Main compensation loop."""
        while self.is_running:
            try:
                roll, pitch, yaw = self._get_tilt_angles()
                self._apply_compensation(roll, pitch, yaw)
            except Exception as e:
                print(f"Error in compensation loop: {e}")
            time.sleep(self.update_rate) 