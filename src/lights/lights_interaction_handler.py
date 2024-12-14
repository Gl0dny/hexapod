from lights import Lights
from .animation import AlternateRotateAnimation, WheelFillAnimation, PulseSmoothlyAnimation
import logging
class LightsInteractionHandler:
    def __init__(self):
        self.lights = Lights()
        self.is_listening = False
        self.is_speaking = False

    def stop_animation(self):
        """Stop any ongoing LED animations."""
        if hasattr(self, 'animation') and self.animation:
            self.animation.stop_animation()
            self.animation = None
        else:
            logging.warning("stop_animation called, but no 'animation' attribute found.")

    def animation(method):
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, 'animation') or self.animation is None:
                raise AttributeError(f"{method.__name__} must set 'self.animation'")
            method(self, *args, **kwargs)
        return wrapper

    def off(self):
        """Turn off the lights."""
        self.stop_animation()
        self.lights.clear()
        self.is_listening = False
        self.is_speaking = False

    @animation
    def wakeup(self):
        self.stop_animation()
        self.animation = WheelFillAnimation(
            lights=self.lights,
            use_rainbow=True,
            color='white',
            interval=0.2,
        )
        self.animation.start()

    @animation
    def listen(self):
        """Simulate listening behavior."""
        self.is_listening = True

        self.stop_animation()
        self.animation = PulseSmoothlyAnimation(
            lights=self.lights,
            base_color='blue',
            pulse_color='green',
            pulse_speed=0.05
        )
        self.animation.start()

    @animation
    def think(self, color_even='indigo', color_odd='golden', delay=0.25, positions=12):
        """Simulate thinking behavior.
            Alternate colors in a rotating pattern."""
        self.stop_animation()
        self.animation = AlternateRotateAnimation(
            lights=self.lights,
            color_even=color_even,
            color_odd=color_odd,
            delay=delay,
            positions=positions,
        )
        self.animation.start()

    @animation
    def speak(self):
        """Simulate speaking behavior."""
        self.is_speaking = True
        pass