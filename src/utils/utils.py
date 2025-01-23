from __future__ import annotations
from typing import TYPE_CHECKING
import threading

import numpy as np

if TYPE_CHECKING:
    from typing import Union

def map_range(value: int, in_min: int, in_max: int, out_min: int, out_max: int) -> int:
        """
        Maps a value from one range to another.
        
        Args:
            value (int): The input value to map.
            in_min (int): The minimum value of the input range.
            in_max (int): The maximum value of the input range.
            out_min (int): The minimum value of the output range.
            out_max (int): The maximum value of the output range.

        Returns:
            int: The mapped value, clamped to the output range.
        """
        if value < in_min:
            return out_min
        elif value > in_max:
            return out_max
        else:
            return (value - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

def parse_percentage(value: Union[str, int]) -> int:
    """
    Parse a percentage value ensuring it's between 0 and 100.
    
    Args:
        value (Union[str, int]): The value to parse, can be a string ending with '%' or an integer.
    
    Returns:
        int: The parsed percentage value.
    
    Raises:
        ValueError: If the value is not a valid percentage.
    """
    if isinstance(value, str) and value.endswith('%'):
        value = value.rstrip('%')
    int_value = int(value)
    if not 0 <= int_value <= 100:
        raise ValueError(f"The parameter for percentage parsing must be between 0 and 100.")
    return int_value
        
def rename_thread(thread: threading.Thread, custom_name: str) -> None:
    """
    Renames the given thread while preserving its original number.

    Args:
        thread (threading.Thread): The thread object to rename.
        custom_name (str): The custom base name for the thread.
    """
    original_name = thread.name

    thread_number = ""
    if original_name.startswith("Thread-"):
        thread_number = original_name.split('-')[1]

    if thread_number:
        thread.name = f"{custom_name}-{thread_number}"
    else:
        thread.name = f"{custom_name}"

def euler_rotation_matrix(roll: float, pitch: float, yaw: float) -> np.ndarray:
    """
    Create a combined rotation matrix from roll, pitch, and yaw angles.
    
    Args:
        roll (float): The roll angle in degrees.
        pitch (float): The pitch angle in degrees.
        yaw (float): The yaw angle in degrees.

    Returns:
        np.ndarray: The combined rotation matrix.
    """
    roll_rad = np.radians(roll)
    pitch_rad = np.radians(pitch)
    yaw_rad = np.radians(yaw)
    
    R_x = np.array([
        [1, 0, 0],
        [0, np.cos(roll_rad), -np.sin(roll_rad)],
        [0, np.sin(roll_rad), np.cos(roll_rad)]
    ])
    
    R_y = np.array([
        [np.cos(pitch_rad), 0, np.sin(pitch_rad)],
        [0, 1, 0],
        [-np.sin(pitch_rad), 0, np.cos(pitch_rad)]
    ])
    
    R_z = np.array([
        [np.cos(yaw_rad), -np.sin(yaw_rad), 0],
        [np.sin(yaw_rad), np.cos(yaw_rad), 0],
        [0, 0, 1]
    ])
    
    return R_z @ R_y @ R_x

def homogeneous_transformation_matrix(tx: float = 0, ty: float = 0, tz: float = 0, roll: float = 0, pitch: float = 0, yaw: float = 0) -> np.ndarray:
    """
    Create a homogeneous transformation matrix from translation and rotation parameters.
    
    Args:
        tx (float, optional): Translation along the x-axis. Defaults to 0.
        ty (float, optional): Translation along the y-axis. Defaults to 0.
        tz (float, optional): Translation along the z-axis. Defaults to 0.
        roll (float, optional): Roll angle in degrees. Defaults to 0.
        pitch (float, optional): Pitch angle in degrees. Defaults to 0.
        yaw (float, optional): Yaw angle in degrees. Defaults to 0.

    Returns:
        np.ndarray: The homogeneous transformation matrix.
    """
    # Create rotation matrix
    R = euler_rotation_matrix(roll, pitch, yaw)
    
    # Create homogeneous transformation matrix
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = [tx, ty, tz]
    
    return T