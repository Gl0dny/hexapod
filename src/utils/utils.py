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