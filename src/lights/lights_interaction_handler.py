from lights import Lights
from .animation import AlternateRotateAnimation

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

    def off(self):
        """Turn off the lights."""
        self.stop_animation()
        self.lights.clear()
        self.is_listening = False
        self.is_speaking = False

    def wakeup(self):
        """Simulate wakeup behavior with an optional direction."""
        self.lights.wheel_fill()

    def listen(self):
        """Simulate listening behavior."""
        self.is_listening = True
        self.lights.pulse_smoothly(base_color='blue', pulse_color='green')

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

    def speak(self):
        """Simulate speaking behavior."""
        self.is_speaking = True
        pass