from lights import Lights

class LightsInteractionHandler:
    def __init__(self):
        self.lights = Lights()
        self.is_listening = False
        self.is_speaking = False

    def wakeup(self):
        """Simulate wakeup behavior with an optional direction."""
        self.lights.wheel_fill()

    def listen(self):
        """Simulate listening behavior."""
        self.is_listening = True
        self.lights.pulse_smoothly(base_color='blue', pulse_color='green')

    def think(self):
        """Simulate thinking behavior."""
        self.lights.alternate_rotate()

    def speak(self):
        """Simulate speaking behavior."""
        self.is_speaking = True
        pass

    def off(self):
        """Turn off the lights."""
        self.lights.stop_animation()
        self.lights.clear()
        self.is_listening = False
        self.is_speaking = False

    def set_color(self, color, num_led=None, led_index=None):
        self.lights.set_color(color, num_led, led_index)