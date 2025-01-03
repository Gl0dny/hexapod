import threading
import abc
from typing import Optional
from lights import Lights
from .lights import ColorRGB

class Animation(abc.ABC):
    """
    Abstract base class for animations using Lights.

    Attributes:
        lights (Lights): The Lights object to control the LEDs.
        thread (threading.Thread): The thread running the animation.
        stop_event (threading.Event): Event to signal the animation to stop.
    """

    def __init__(self, lights: Lights) -> None:
        """
        Initialize the Animation object.

        Args:
            lights (Lights): The Lights object to control the LEDs.
        """
        self.lights: Lights = lights
        self.thread: threading.Thread = None
        self.stop_event: threading.Event = threading.Event()

    def start(self) -> None:
        """
        Start the animation in a separate thread.
        """
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    @abc.abstractmethod
    def run(self) -> None:
        """
        The method to be implemented by subclasses to define the animation logic.
        """
        pass

    def stop_animation(self) -> None:
        """
        Stop the animation and wait for the thread to finish.
        """
        self.stop_event.set()
        print(f"Animation {self.__class__.__name__} forcefully stopping.")
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.01)

    def __del__(self):
        """
        Destructor that informs which animation is stopping.
        """
        print(f"Animation {self.__class__.__name__} is being destroyed and stopping.")

class AlternateRotateAnimation(Animation):
    """
    Animation that alternates colors and rotates the LEDs.

    Attributes:
        color_even (ColorRGB): The color for even indexed LEDs.
        color_odd (ColorRGB): The color for odd indexed LEDs.
        delay (float): The delay between rotations.
        positions (int): The number of positions to rotate.
    """

    def __init__(self, lights: Lights, color_even: ColorRGB = ColorRGB.INDIGO, color_odd: ColorRGB = ColorRGB.GOLDEN, delay: float = 0.25, positions: int = 12) -> None:
        """
        Initialize the AlternateRotateAnimation object.

        Args:
            lights (Lights): The Lights object to control the LEDs.
            color_even (ColorRGB): The color for even indexed LEDs.
            color_odd (ColorRGB): The color for odd indexed LEDs.
            delay (float): The delay between rotations.
            positions (int): The number of positions to rotate.
        """
        super().__init__(lights)
        self.color_even: ColorRGB = color_even
        self.color_odd: ColorRGB = color_odd
        self.delay: float = delay
        self.positions: int = positions

    def run(self) -> None:
        """
        Run the animation logic.
        """
        while not self.stop_event.is_set():
            for i in range(self.lights.num_led):
                if self.stop_event.wait(self.delay):
                    return
                
                color = self.color_even if i % 2 == 0 else self.color_odd
                self.lights.set_color(color, led_index=i)


            for _ in range(self.positions):
                if self.stop_event.wait(self.delay):
                    return
                
                self.lights.rotate(1)
                
class WheelFillAnimation(Animation):
    """
    Animation that fills the LEDs with colors from a color wheel.

    Attributes:
        use_rainbow (bool): Whether to use rainbow colors.
        color (Optional[ColorRGB]): The color to use if not using rainbow colors.
        interval (float): The interval between filling LEDs.
    """

    def __init__(self, lights: Lights, use_rainbow: bool = True, color: Optional[ColorRGB] = None, interval: float = 0.2) -> None:
        """
        Initialize the WheelFillAnimation object.

        Args:
            lights (Lights): The Lights object to control the LEDs.
            use_rainbow (bool): Whether to use rainbow colors.
            color (Optional[ColorRGB]): The color to use if not using rainbow colors.
            interval (float): The interval between filling LEDs.
        
        Raises:
            ValueError: If `use_rainbow` is False and `color` is not provided.
        """
        super().__init__(lights)
        if not use_rainbow and color is None:
            raise ValueError("color must be provided when use_rainbow is False.")
        self.use_rainbow: bool = use_rainbow
        self.color: Optional[ColorRGB] = color
        self.interval: float = interval

    def run(self) -> None:
        """
        Run the animation logic.
        """
        for i in range(self.lights.num_led):
            if self.stop_event.wait(self.interval):
                return
            
            if self.use_rainbow:
                rgb = self.lights.get_wheel_color(int(256 / self.lights.num_led * i))
            else:
                rgb = self.color.rgb if self.color else (0, 0, 0)
            
            self.lights.set_color_rgb(rgb_tuple=rgb, led_index=i)

                
class PulseSmoothlyAnimation(Animation):
    """
    Animation that smoothly pulses between two colors.

    Attributes:
        base_color (ColorRGB): The base color.
        pulse_color (ColorRGB): The pulse color.
        pulse_speed (float): The speed of the pulse.
    """

    def __init__(self, lights: Lights, base_color: ColorRGB = ColorRGB.BLUE, pulse_color: ColorRGB = ColorRGB.GREEN, pulse_speed: float = 0.05) -> None:
        """
        Initialize the PulseSmoothlyAnimation object.

        Args:
            lights (Lights): The Lights object to control the LEDs.
            base_color (ColorRGB): The base color.
            pulse_color (ColorRGB): The pulse color.
            pulse_speed (float): The speed of the pulse.
        """
        super().__init__(lights)
        self.base_color: ColorRGB = base_color
        self.pulse_color: ColorRGB = pulse_color
        self.pulse_speed: float = pulse_speed

    def run(self) -> None:
        """
        Run the animation logic.
        """
        base_rgb = self.base_color.rgb
        pulse_rgb = self.pulse_color.rgb
        while not self.stop_event.is_set():
            for i in range(0, 100, 5):
                if self.stop_event.wait(self.pulse_speed):
                    return
        
                interp_rgb = (
                    int(base_rgb[0] + (pulse_rgb[0] - base_rgb[0]) * i / 100),
                    int(base_rgb[1] + (pulse_rgb[1] - base_rgb[1]) * i / 100),
                    int(base_rgb[2] + (pulse_rgb[2] - base_rgb[2]) * i / 100)
                )
                self.lights.set_color_rgb(interp_rgb)

            for i in range(100, 0, -5):
                if self.stop_event.wait(self.pulse_speed):
                    return
                
                interp_rgb = (
                    int(base_rgb[0] + (pulse_rgb[0] - base_rgb[0]) * i / 100),
                    int(base_rgb[1] + (pulse_rgb[1] - base_rgb[1]) * i / 100),
                    int(base_rgb[2] + (pulse_rgb[2] - base_rgb[2]) * i / 100)
                )
                self.lights.set_color_rgb(interp_rgb)
                
class PulseAnimation(Animation):
    """
    Animation that pulses between two colors.

    Attributes:
        base_color (ColorRGB): The base color.
        pulse_color (ColorRGB): The pulse color.
        pulse_speed (float): The speed of the pulse.
    """

    def __init__(self, lights: Lights, base_color: ColorRGB = ColorRGB.BLUE, pulse_color: ColorRGB = ColorRGB.RED, pulse_speed: float = 0.3) -> None:
        """
        Initialize the PulseAnimation object.

        Args:
            lights (Lights): The Lights object to control the LEDs.
            base_color (ColorRGB): The base color.
            pulse_color (ColorRGB): The pulse color.
            pulse_speed (float): The speed of the pulse.
        """
        super().__init__(lights)
        self.base_color: ColorRGB = base_color
        self.pulse_color: ColorRGB = pulse_color
        self.pulse_speed: float = pulse_speed

    def run(self) -> None:
        """
        Run the animation logic.
        """
        while not self.stop_event.is_set():
            if self.stop_event.wait(self.pulse_speed):
                return
    
            self.lights.set_color(self.base_color)

            if self.stop_event.wait(self.pulse_speed):
                return
            
            self.lights.set_color(self.pulse_color)

class WheelAnimation(Animation):
    """
    Animation that rotates through colors on a color wheel or rotates through LEDs with one specific color.

    Attributes:
        use_rainbow (bool): Whether to use rainbow colors.
        color (Optional[ColorRGB]): The color to use if not using rainbow colors.
        interval (float): The interval between changing colors.
    """

    def __init__(self, lights: Lights, use_rainbow: bool = True, color: Optional[ColorRGB] = None, interval: float = 0.2) -> None:
        """
        Initialize the WheelAnimation object.

        Args:
            lights (Lights): The Lights object to control the LEDs.
            use_rainbow (bool): Whether to use rainbow colors.
            color (Optional[ColorRGB]): The color to use if not using rainbow colors.
            interval (float): The interval between changing colors.
        
        Raises:
            ValueError: If `use_rainbow` is False and `color` is not provided.
        """
        super().__init__(lights)
        if not use_rainbow and color is None:
            raise ValueError("color must be provided when use_rainbow is False.")
        self.use_rainbow: bool = use_rainbow
        self.color: Optional[ColorRGB] = color
        self.interval: float = interval

    def run(self) -> None:
        """
        Run the animation logic.
        """
        while not self.stop_event.is_set():
            for i in range(self.lights.num_led):
                if self.stop_event.wait(self.interval):
                    return
        
                if self.use_rainbow:
                    rgb = self.lights.get_wheel_color(int(256 / self.lights.num_led * i))
                else:
                    rgb = self.color.rgb if self.color else (0, 0, 0)
                
                self.lights.clear()
                self.lights.set_color_rgb(rgb_tuple=rgb, led_index=i)
                
                
class OppositeRotateAnimation(Animation):
    """
    Animation that lights up LEDs moving in opposite directions, creating a symmetrical effect.
    The animation lights up LEDs starting from a point and moves outward in opposite directions.
    After reaching the ends, it reverses direction and repeats the process.

    Attributes:
        FORWARD (int): Constant representing the forward direction.
        BACKWARD (int): Constant representing the backward direction.
        interval (float): Time interval between LED updates.
        color (ColorRGB): ColorRGB of the LEDs.
        direction (int): Current direction of the animation.
    """
    FORWARD: int = 1
    BACKWARD: int = -1

    def __init__(self, lights: Lights, interval: float = 0.1, color: ColorRGB = ColorRGB.WHITE) -> None:
        """
        Initialize the OppositeRotateAnimation object.

        Args:
            lights (Lights): The Lights object to control the LEDs.
            interval (float): Time interval between LED updates.
            color (ColorRGB): ColorRGB of the LEDs.
        """
        super().__init__(lights)
        self.interval: float = interval
        self.color: ColorRGB = color
        self.direction: int = self.FORWARD

    def run(self) -> None:
        """
        Run the animation logic.
        """
        num_leds = self.lights.num_led
        start_index = 0
        while not self.stop_event.is_set():
            # Light up the starting LED
            if self.stop_event.wait(self.interval):
                return
    
            self.lights.clear()
            self.lights.set_color(self.color, led_index=start_index)

            # Fork into two LEDs moving in opposite directions
            max_offset = (num_leds + 1) // 2  # Handles even and odd numbers of LEDs
            for offset in range(1, max_offset):
                if self.stop_event.wait(self.interval):
                    return
        
                index1 = (start_index + offset * self.direction) % num_leds
                index2 = (start_index - offset * self.direction) % num_leds

                self.lights.clear()
                self.lights.set_color(self.color, led_index=index1)
                self.lights.set_color(self.color, led_index=index2)

            # Merge back into one LED at the opposite end
            end_index = (start_index + max_offset * self.direction) % num_leds
            self.lights.clear()
            self.lights.set_color(self.color, led_index=end_index)

            if self.stop_event.wait(self.interval):
                return
            
            # Switch direction and update starting index
            self.direction = self.BACKWARD if self.direction == self.FORWARD else self.FORWARD
            start_index = end_index