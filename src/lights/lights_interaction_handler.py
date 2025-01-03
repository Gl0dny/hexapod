from typing import Callable, Any, Optional, Dict
from lights import Lights
from .animation import Animation, OppositeRotateAnimation, WheelFillAnimation, PulseSmoothlyAnimation
from .lights import ColorRGB

class LightsInteractionHandler:
    """
    A class to handle interactions with the Lights object, including animations.

    Attributes:
        lights (Lights): The Lights object to control the LEDs.
        animation (Animation): The current animation being played.
        leg_to_led (dict): Mapping from leg indices to LED indices.
    """

    def __init__(self, leg_to_led_map: Dict[int, int]) -> None:
        """
        Initialize the LightsInteractionHandler object.

        Args:
            leg_to_led_map (dict): Mapping from leg indices to LED indices.
        """
        self.lights: Lights = Lights()
        self.animation: Animation = None
        self.leg_to_led = leg_to_led_map

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
        self.stop_animation()
        self.animation = WheelFillAnimation(
            lights=self.lights,
            use_rainbow=use_rainbow,
            color=color if color else ColorRGB.WHITE,
            interval=interval,
        )
        self.animation.start()

    @animation
    def listen(
        self,
        base_color: ColorRGB = ColorRGB.BLUE,
        pulse_color: ColorRGB = ColorRGB.GREEN,
        pulse_speed: float = 0.05
    ) -> None:
        """
        Start the listen animation.

        Args:
            base_color (ColorRGB): The base color of the LEDs.
            pulse_color (ColorRGB): The color to pulse.
            pulse_speed (float): The speed of the pulse.
        """
        self.stop_animation()
        self.animation = PulseSmoothlyAnimation(
            lights=self.lights,
            base_color=base_color,
            pulse_color=pulse_color,
            pulse_speed=pulse_speed
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
        self.stop_animation()
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
        self.stop_animation()
        self.animation = None  # Ensure animation is set to avoid AttributeError
        raise NotImplementedError("The 'speak' method is not implemented yet.")

    def update_calibration_leds_status(self, calibration_status: Dict[int, str]) -> None:
        """
        Update each leg's LED color based on calibration status.
        
        Args:
            calibration_status (dict): Dictionary with leg indices as keys and their calibration status.
        """
        self.stop_animation()
        for leg_index, led_index in self.leg_to_led.items():
            status = calibration_status.get(leg_index, "not_calibrated")
            if status == "calibrating":
                self.lights.set_color(ColorRGB.YELLOW, led_index=led_index)
            elif status == "calibrated":
                self.lights.set_color(ColorRGB.GREEN, led_index=led_index)
            else:
                self.lights.set_color(ColorRGB.RED, led_index=led_index)