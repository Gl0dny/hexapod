from typing import Callable, Any, Optional, Dict
from functools import wraps
from lights import Lights, ColorRGB
from .animation import *

class LightsInteractionHandler:
    """
    A class to handle interactions with the Lights object, including animations.

    Attributes:
        lights (Lights): The Lights object to control the LEDs.
        animation (Animation): The current animation being played.
        leg_to_led (dict): Mapping from leg indices to LED indices.
    """

    def __init__(self, leg_to_led: Dict[int, int]) -> None:
        """
        Initialize the LightsInteractionHandler object.

        Args:
            leg_to_led (dict): Mapping from leg indices to LED indices.
        """
        self.lights: Lights = Lights()
        self.animation: Animation = None
        self.leg_to_led = leg_to_led

    def stop_animation(self) -> None:
        """
        Stop any running animation and reset the animation attribute.
        """
        if hasattr(self, 'animation') and self.animation:
            self.animation.stop_animation()
            self.animation = None

    def animation(method: Callable[..., Any]) -> Callable[..., Any]:
        """
        Decorator to ensure that a method sets the 'self.animation' attribute.

        Args:
            method (function): The method to wrap.

        Returns:
            function: Wrapped method.
        """
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            method(self, *args, **kwargs)
            if not hasattr(self, 'animation') or self.animation is None:
                raise AttributeError(
                    f"{method.__name__} must set 'self.animation' attribute")
        return wrapper

    def off(self) -> None:
        """
        Turn off the lights and stop any running animation.
        """
        self.stop_animation()
        self.lights.clear()

    def set_single_color(self, color: ColorRGB, led_index: Optional[int] = None) -> None:
        """
        Set a single LED or all LEDs to a single color.

        Args:
            color (ColorRGB): The color to set.
            led_index (int, optional): The index of the LED to set. If None, sets all LEDs.
        """
        self.lights.set_color(color, led_index=led_index)

    def set_brightness(self, brightness: int) -> None:
        """
        Set the brightness of the LEDs.

        Args:
            brightness (int): The brightness level (0-100).
        """
        self.lights.set_brightness(brightness)

    @animation
    def wakeup(
        self,
        use_rainbow: bool = True,
        color: Optional[ColorRGB] = None,
        interval: float = 0.2
    ) -> None:
        """
        Start the wakeup animation.

        Args:
            use_rainbow (bool): Whether to use rainbow colors.
            color (ColorRGB, optional): The color to use if not using rainbow colors.
            interval (float): The interval between filling LEDs.
        """
        self.off()
        self.animation = WheelFillAnimation(
            lights=self.lights,
            use_rainbow=use_rainbow,
            color=color if color else ColorRGB.WHITE,
            interval=interval,
        )
        self.animation.start()

    @animation
    def ready(
        self,
        base_color: ColorRGB = ColorRGB.BLUE,
        pulse_color: ColorRGB = ColorRGB.GREEN,
        pulse_speed: float = 0.05
        ) -> None:
        """
        Start the ready animation.

        Args:
            base_color (ColorRGB): The base color of the LEDs.
            pulse_color (ColorRGB): The color to pulse.
            pulse_speed (float): The speed of the pulse.
        """
        self.off()
        self.animation = PulseSmoothlyAnimation(
            lights=self.lights,
            base_color=base_color,
            pulse_color=pulse_color,
            pulse_speed=pulse_speed
        )
        self.animation.start()


    @animation
    def listen(
        self,
        color_even: ColorRGB = ColorRGB.INDIGO,
        color_odd: ColorRGB = ColorRGB.GREEN,
        delay: float = 0.15
    ) -> None:
        """
        Start the listen animation.

        Args:
            color_even (ColorRGB): Initial color for even LEDs.
            color_odd (ColorRGB): Initial color for odd LEDs.
            delay (float): Delay between rotations.
        """
        self.off()
        self.animation = AlternateRotateAnimation(
            lights=self.lights,
            color_even=color_even,
            color_odd=color_odd,
            delay=delay
        )
        self.animation.start()

    @animation
    def think(
        self,
        color: ColorRGB = ColorRGB.LIME,
        interval: float = 0.1
    ) -> None:
        """
        Start the think animation.

        Args:
            color (ColorRGB): The color of the LEDs.
            interval (float): The delay between updates.
        """
        self.off()
        self.animation = OppositeRotateAnimation(
            lights=self.lights,
            interval=interval,
            color=color,
        )
        self.animation.start()

    @animation
    def speak(self) -> None:
        """
        Start the speak animation.
        """
        self.off()
        self.animation = None  # Ensure animation is set to avoid AttributeError
        raise NotImplementedError("The 'speak' method is not implemented yet.")

    @animation
    def police(self, pulse_speed: float = 0.25) -> None:
        """
        Start the police pulsing animation.
        
        Args:
            pulse_speed (float): The speed of the pulse.
        """
        self.off()
        self.animation = PulseAnimation(
            lights=self.lights,
            base_color=ColorRGB.BLUE,
            pulse_color=ColorRGB.RED,
            pulse_speed=pulse_speed
        )
        self.animation.start()

    @animation
    def shutdown(self, interval: float = 1.2) -> None:
        """
        Start the shutdown animation using WheelFillAnimation with red color.
        """
        self.off()
        self.animation = WheelFillAnimation(
            lights=self.lights,
            use_rainbow=False,
            color=ColorRGB.RED,
            interval=interval
        )
        self.animation.start()

    def update_calibration_leds_status(self, calibration_status: Dict[int, str]) -> None:
        """
        Update each leg's LED color based on calibration status.
        
        Args:
            calibration_status (dict): Dictionary with leg indices as keys and their calibration status.
        """
        # Current animation in progress; skip updating LEDs.
        if self.animation:
            return
        
        for leg_index, led_index in self.leg_to_led.items():
            status = calibration_status.get(leg_index, "not_calibrated")
            if status == "calibrating":
                self.set_single_color(ColorRGB.YELLOW, led_index=led_index)
            elif status == "calibrated":
                self.set_single_color(ColorRGB.GREEN, led_index=led_index)
            else:
                self.set_single_color(ColorRGB.RED, led_index=led_index)