import threading

def map_range(value, in_min, in_max, out_min, out_max):
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
        
        import threading

def rename_thread(thread, custom_name, include_function_name=False):
    """
    Renames the given thread while preserving its original number and optionally appending the function name.

    Args:
        thread (threading.Thread): The thread object to rename.
        custom_name (str): The custom base name for the thread.
        include_function_name (bool): Whether to include the function name in the new thread name.
    """
    original_name = thread.name

    thread_number = ""
    if original_name.startswith("Thread-"):
        thread_number = original_name.split('-')[1]

    # function_name = f" ({thread._target.__name__})" if include_function_name and thread._target else ""

    if thread_number:
        thread.name = f"{custom_name}-{thread_number}"
    else:
        thread.name = f"{custom_name}"