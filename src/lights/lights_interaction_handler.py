from lights import Lights
from .animation import OppositeRotateAnimation, WheelFillAnimation, PulseSmoothlyAnimation

class LightsInteractionHandler:
    """
    A class to handle interactions with the Lights object, including animations.

    Attributes:
        lights (Lights): The Lights object to control the LEDs.
        animation (Animation): The current animation being played.
    """

    def __init__(self):
        """
        Initialize the LightsInteractionHandler object.
        """
        self.lights = Lights()
        self.animation = None

    def stop_animation(self):
        """
        Stop the current animation if one is running.
        """
        if hasattr(self, 'animation') and self.animation:
            self.animation.stop_animation()
            self.animation = None

    def animation(method):
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

    def off(self):
        """
        Turn off the lights and stop any running animation.
        """
        self.stop_animation()
        self.lights.clear()

    @animation
    def wakeup(self, use_rainbow=True, color='white', interval=0.2):
        """
        Start the wakeup animation.

        Args:
            use_rainbow (bool): Whether to use rainbow colors.
            color (str): The color to use if not using rainbow colors.
            interval (float): The interval between filling LEDs.
        """
        self.stop_animation()
        self.animation = WheelFillAnimation(
            lights=self.lights,
            use_rainbow=use_rainbow,
            color=color,
            interval=interval,
        )
        self.animation.start()

    @animation
    def listen(self, base_color='blue', pulse_color='green', pulse_speed=0.05):
        """
        Start the listen animation.

        Args:
            base_color (str): The base color of the LEDs.
            pulse_color (str): The color to pulse.
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
    def think(self, color='white', interval=0.1):
        """
        Start the think animation.

        Args:
            color (str): The color of the LEDs.
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
    def speak(self):
        """
        Start the speak animation.
        """
        pass
