import threading
import abc

class Animation(abc.ABC):
    """
    Abstract base class for animations using Lights.

    Attributes:
        lights (Lights): The Lights object to control the LEDs.
        thread (threading.Thread): The thread running the animation.
        stop_event (threading.Event): Event to signal the animation to stop.
    """

    def __init__(self, lights):
        """
        Initialize the Animation object.

        Args:
            lights (Lights): The Lights object to control the LEDs.
        """
        self.lights = lights
        self.thread = None
        self.stop_event = threading.Event()

    def start(self):
        """
        Start the animation in a separate thread.
        """
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    @abc.abstractmethod
    def run(self):
        """
        The method to be implemented by subclasses to define the animation logic.
        """
        pass

    def stop_animation(self):
        """
        Stop the animation and wait for the thread to finish.
        """
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.01)

class AlternateRotateAnimation(Animation):
    """
    Animation that alternates colors and rotates the LEDs.

    Attributes:
        color_even (str): The color for even indexed LEDs.
        color_odd (str): The color for odd indexed LEDs.
        delay (float): The delay between rotations.
        positions (int): The number of positions to rotate.
    """

    def __init__(self, lights, color_even='indigo', color_odd='golden', delay=0.25, positions=12):
        """
        Initialize the AlternateRotateAnimation object.

        Args:
            lights (Lights): The Lights object to control the LEDs.
            color_even (str): The color for even indexed LEDs.
            color_odd (str): The color for odd indexed LEDs.
            delay (float): The delay between rotations.
            positions (int): The number of positions to rotate.
        """
        super().__init__(lights)
        self.color_even = color_even
        self.color_odd = color_odd
        self.delay = delay
        self.positions = positions

    def run(self):
        """
        Run the animation logic.
        """
        while not self.stop_event.is_set():
            for i in range(self.lights.num_led):
                color = self.color_even if i % 2 == 0 else self.color_odd
                self.lights.set_color(color, led_index=i)

            for _ in range(self.positions):
                self.lights.rotate(1)
                if self.stop_event.wait(self.delay):
                    return
                
class WheelFillAnimation(Animation):
    """
    Animation that fills the LEDs with colors from a color wheel.

    Attributes:
        use_rainbow (bool): Whether to use rainbow colors.
        color (str): The color to use if not using rainbow colors.
        interval (float): The interval between filling LEDs.
    """

    def __init__(self, lights, use_rainbow=True, color='white', interval=0.2):
        """
        Initialize the WheelFillAnimation object.

        Args:
            lights (Lights): The Lights object to control the LEDs.
            use_rainbow (bool): Whether to use rainbow colors.
            color (str): The color to use if not using rainbow colors.
            interval (float): The interval between filling LEDs.
        """
        super().__init__(lights)
        self.use_rainbow = use_rainbow
        self.color = color
        self.interval = interval

    def run(self):
        """
        Run the animation logic.
        """
        for i in range(self.lights.num_led):
            if self.use_rainbow:
                rgb = self.lights.get_wheel_color(int(256 / self.lights.num_led * i))
            else:
                rgb = self.lights.COLORS_RGB.get(self.color.lower(), (0, 0, 0))
            
            self.lights.set_color_rgb(rgb_tuple=rgb, led_index=i)

            if self.stop_event.wait(self.interval):
                return
                
class PulseSmoothlyAnimation(Animation):
    """
    Animation that smoothly pulses between two colors.

    Attributes:
        base_color (str): The base color.
        pulse_color (str): The pulse color.
        pulse_speed (float): The speed of the pulse.
    """

    def __init__(self, lights, base_color='blue', pulse_color='green', pulse_speed=0.05):
        """
        Initialize the PulseSmoothlyAnimation object.

        Args:
            lights (Lights): The Lights object to control the LEDs.
            base_color (str): The base color.
            pulse_color (str): The pulse color.
            pulse_speed (float): The speed of the pulse.
        """
        super().__init__(lights)
        self.base_color = base_color
        self.pulse_color = pulse_color
        self.pulse_speed = pulse_speed

    def run(self):
        """
        Run the animation logic.
        """
        base_rgb = self.lights.COLORS_RGB.get(self.base_color.lower(), (0, 0, 0))
        pulse_rgb = self.lights.COLORS_RGB.get(self.pulse_color.lower(), (0, 0, 0))
        while not self.stop_event.is_set():
            for i in range(0, 100, 5):
                interp_rgb = (
                    int(base_rgb[0] + (pulse_rgb[0] - base_rgb[0]) * i / 100),
                    int(base_rgb[1] + (pulse_rgb[1] - base_rgb[1]) * i / 100),
                    int(base_rgb[2] + (pulse_rgb[2] - base_rgb[2]) * i / 100)
                )
                self.lights.set_color_rgb(interp_rgb)
                if self.stop_event.wait(self.pulse_speed):
                    return
            for i in range(100, 0, -5):
                interp_rgb = (
                    int(base_rgb[0] + (pulse_rgb[0] - base_rgb[0]) * i / 100),
                    int(base_rgb[1] + (pulse_rgb[1] - base_rgb[1]) * i / 100),
                    int(base_rgb[2] + (pulse_rgb[2] - base_rgb[2]) * i / 100)
                )
                self.lights.set_color_rgb(interp_rgb)
                if self.stop_event.wait(self.pulse_speed):
                    return
                
class PulseAnimation(Animation):
    """
    Animation that pulses between two colors.

    Attributes:
        base_color (str): The base color.
        pulse_color (str): The pulse color.
        pulse_speed (float): The speed of the pulse.
    """

    def __init__(self, lights, base_color='blue', pulse_color='red', pulse_speed=0.3):
        """
        Initialize the PulseAnimation object.

        Args:
            lights (Lights): The Lights object to control the LEDs.
            base_color (str): The base color.
            pulse_color (str): The pulse color.
            pulse_speed (float): The speed of the pulse.
        """
        super().__init__(lights)
        self.base_color = base_color
        self.pulse_color = pulse_color
        self.pulse_speed = pulse_speed

    def run(self):
        """
        Run the animation logic.
        """
        while not self.stop_event.is_set():
            self.lights.set_color(self.base_color)
            if self.stop_event.wait(self.pulse_speed):
                return
            self.lights.set_color(self.pulse_color)
            if self.stop_event.wait(self.pulse_speed):
                return

class WheelAnimation(Animation):
    """
    Animation that rotates through colors on a color wheel or rotates through LEDs with one specific color.

    Attributes:
        use_rainbow (bool): Whether to use rainbow colors.
        color (str): The color to use if not using rainbow colors.
        interval (float): The interval between changing colors.
    """

    def __init__(self, lights, use_rainbow=True, color='white', interval=0.2):
        """
        Initialize the WheelAnimation object.

        Args:
            lights (Lights): The Lights object to control the LEDs.
            use_rainbow (bool): Whether to use rainbow colors.
            color (str): The color to use if not using rainbow colors.
            interval (float): The interval between changing colors.
        """
        super().__init__(lights)
        self.use_rainbow = use_rainbow
        self.color = color
        self.interval = interval

    def run(self):
        """
        Run the animation logic.
        """
        while not self.stop_event.is_set():
            for i in range(self.lights.num_led):
                if self.use_rainbow:
                    rgb = self.lights.get_wheel_color(int(256 / self.lights.num_led * i))
                else:
                    rgb = self.lights.COLORS_RGB.get(self.color.lower(), (0, 0, 0))
                
                self.lights.clear()
                self.lights.set_color_rgb(rgb_tuple=rgb, led_index=i)
                
                if self.stop_event.wait(self.interval):
                    return