from __future__ import annotations
from typing import TYPE_CHECKING
import threading

if TYPE_CHECKING:
    from typing import Any

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

def parse_percentage(value: Any) -> int:
    """
    Parse a percentage value ensuring it's between 0 and 100.
    
    Args:
        value (Any): The value to parse.
    
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