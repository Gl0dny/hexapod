import logging
from typing import Callable, Any, Optional, Dict
from functools import wraps
from lights import Lights, ColorRGB
from .animation import *

logger = logging.getLogger("lights_logger")

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
        logger.debug(f"Initializing LightsInteractionHandler with leg_to_led: {leg_to_led}")
        self.lights: Lights = Lights()
        self.animation: Animation = None
        self.leg_to_led = leg_to_led
        logger.debug("LightsInteractionHandler initialized successfully.")

    def stop_animation(self) -> None:
        """
        Stop any running animation and reset the animation attribute.
        """
        logger.debug("Stopping any running animation.")
        if hasattr(self, 'animation') and self.animation:
            logger.debug("An animation is currently running. Stopping it.")
            self.animation.stop_animation()
            self.animation = None
            logger.info("Animation stopped.")
        else:
            logger.debug("No active animation to stop.")

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
            logger.debug(f"Entering {method.__name__} method.")
            method(self, *args, **kwargs)
            if not hasattr(self, 'animation') or self.animation is None:
                logger.error(f"{method.__name__} must set 'self.animation' attribute.")
                raise AttributeError(f"{method.__name__} must set 'self.animation' attribute")
            logger.debug(f"Exiting {method.__name__} method.")
        return wrapper

    def off(self) -> None:
        """
        Turn off the lights and stop any running animation.
        """
        logger.debug("Turning off lights and stopping any running animation.")
        self.stop_animation()
        self.lights.clear()
        logger.info("Lights turned off.")

    def set_single_color(self, color: ColorRGB, led_index: Optional[int] = None) -> None:
        """
        Set a single LED or all LEDs to a single color.

        Args:
            color (ColorRGB): The color to set.
            led_index (int, optional): The index of the LED to set. If None, sets all LEDs.
        """
        if led_index is not None:
            logger.debug(f"Setting LED {led_index} to color {color.name}.")
            self.lights.set_color(color, led_index=led_index)
            logger.info(f"LED {led_index} set to {color.name}.")
        else:
            logger.debug(f"Setting all LEDs to color {color.name}.")
            self.lights.set_color(color)
            logger.info(f"All LEDs set to {color.name}.")

    def set_brightness(self, brightness: int) -> None:
        """
        Set the brightness of the LEDs.

        Args:
            brightness (int): The brightness level (0-100).
        """
        logger.debug(f"Setting brightness to {brightness}%.")
        self.lights.set_brightness(brightness)
        logger.info(f"Brightness set to {brightness}%.")

    @animation
    def rainbow(
        self,
        use_rainbow: bool = True,
        color: Optional[ColorRGB] = None,
        interval: float = 0.2
    ) -> None:
        """
        Start the rainbow animation.

        Args:
            use_rainbow (bool): Whether to use rainbow colors.
            color (ColorRGB, optional): The color to use if not using rainbow colors.
            interval (float): The interval between filling LEDs.
        """
        logger.debug("Starting rainbow animation.")
        self.off()
        self.animation = WheelFillAnimation(
            lights=self.lights,
            use_rainbow=use_rainbow,
            color=color if color else ColorRGB.WHITE,
            interval=interval,
        )
        self.animation.start()
        logger.info("Rainbow animation started.")
        logger.debug("rainbow method execution completed.")

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
        logger.debug("Starting ready animation.")
        self.off()
        self.animation = PulseSmoothlyAnimation(
            lights=self.lights,
            base_color=base_color,
            pulse_color=pulse_color,
            pulse_speed=pulse_speed
        )
        self.animation.start()
        logger.info("Ready animation started.")
        logger.debug("ready method execution completed.")
        print('[Listening ...]')

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
        logger.debug("Starting listen animation.")
        self.off()
        self.animation = AlternateRotateAnimation(
            lights=self.lights,
            color_even=color_even,
            color_odd=color_odd,
            delay=delay
        )
        self.animation.start()
        logger.info("Listen animation started.")
        logger.debug("listen method execution completed.")

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
        logger.debug(f"Starting think animation with color: {color.name}, interval: {interval}")
        self.off()
        logger.debug("Turning off lights before starting think animation.")
        self.animation = OppositeRotateAnimation(
            lights=self.lights,
            interval=interval,
            color=color,
        )
        logger.debug("OppositeRotateAnimation instance created.")
        self.animation.start()
        logger.info("Think animation started.")
        logger.debug("think method execution completed.")

    @animation
    def speak(self) -> None:
        """
        Start the speak animation.
        """
        logger.debug("Starting speak animation.")
        self.off()
        self.animation = None  # Ensure animation is set to avoid AttributeError
        logger.info("Speak animation initiated.")
        logger.debug("speak method execution completed.")
        raise NotImplementedError("The 'speak' method is not implemented yet.")

    @animation
    def police(self, pulse_speed: float = 0.25) -> None:
        """
        Start the police pulsing animation.

        Args:
            pulse_speed (float): The speed of the pulse.
        """
        logger.debug(f"Starting police animation with pulse_speed: {pulse_speed}")
        self.off()
        logger.debug("Turning off lights before starting police animation.")
        self.animation = PulseAnimation(
            lights=self.lights,
            base_color=ColorRGB.BLUE,
            pulse_color=ColorRGB.RED,
            pulse_speed=pulse_speed
        )
        logger.debug("PulseAnimation instance created.")
        self.animation.start()
        logger.info("Police animation started.")
        logger.debug("police method execution completed.")

    @animation
    def shutdown(self, interval: float = 1.2) -> None:
        """
        Start the shutdown animation using WheelFillAnimation with red color.

        Args:
            interval (float): The interval between filling LEDs.
        """
        logger.debug(f"Starting shutdown animation with interval: {interval}")
        self.off()
        logger.debug("Turning off lights before starting shutdown animation.")
        self.animation = WheelFillAnimation(
            lights=self.lights,
            use_rainbow=False,
            color=ColorRGB.RED,
            interval=interval
        )
        logger.debug("WheelFillAnimation instance created.")
        self.animation.start()
        logger.info("Shutdown animation initiated.")
        logger.debug("shutdown method execution completed.")

    def update_calibration_leds_status(self, calibration_status: Dict[int, str]) -> None:
        """
        Update each leg's LED color based on calibration status.
        
        Args:
            calibration_status (dict): Dictionary with leg indices as keys and their calibration status.
        """
        logger.debug(f"Updating calibration LED statuses with calibration_status: {calibration_status}")
        # Current animation in progress; skip updating LEDs.
        if self.animation:
            logger.debug("An animation is currently running. Skipping calibration LED update.")
            return
        
        for leg_index, led_index in self.leg_to_led.items():
            status = calibration_status.get(leg_index, "not_calibrated")
            if status == "calibrating":
                logger.debug(f"Calibrating: Setting LED {led_index} to YELLOW.")
                self.set_single_color(ColorRGB.YELLOW, led_index=led_index)
            elif status == "calibrated":
                logger.debug(f"Calibrated: Setting LED {led_index} to GREEN.")
                self.set_single_color(ColorRGB.GREEN, led_index=led_index)
            else:
                logger.debug(f"Not calibrated: Setting LED {led_index} to RED.")
                self.set_single_color(ColorRGB.RED, led_index=led_index)
        logger.info("Calibration LED statuses updated.")
        logger.debug("update_calibration_leds_status method execution completed.")