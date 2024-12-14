from lights import Lights
from .animation import AlternateRotateAnimation, WheelFillAnimation, PulseSmoothlyAnimation

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
        self.stop_animation()
        self.animation = WheelFillAnimation(
            lights=self.lights,
            use_rainbow=True,
            color='white',
            interval=0.2,
        )
        self.animation.start()

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