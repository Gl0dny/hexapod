from gpiozero import LED
from .apa102 import APA102
import threading
import time

class Lights:
    COLORS_RGB = {
        'blue': (0, 0, 255),
        'teal': (0, 128, 128),
        'green': (0, 255, 0),
        'lime': (75, 180, 0),
        'yellow': (255, 215, 0),
        'golden': (255, 50, 0),
        'orange': (255, 25, 0),
        'red': (255, 0, 0),
        'pink': (255, 51, 183),
        'purple': (128, 0, 128),
        'indigo': (75, 0, 130),
        'gray': (139, 69, 19),
        'white': (255, 255, 255)
    }

    def __init__(self, num_led=12, power_pin=5, brightness=50, initial_color='indigo'):
        self.num_led = num_led
        self.driver = APA102(num_led=self.num_led)
        self.power = LED(power_pin)
        self.power.on()
        self.led_color = initial_color
        self.brightness = brightness  # Percentage (0-100)
        self.thread = None
        self.running = False

        self.set_brightness(self.brightness)

    def set_brightness(self, brightness):
        """Set the global brightness of the LEDs (0-100%)."""
        if brightness > 100:
            brightness = 100
        elif brightness < 0:
            brightness = 0
        self.brightness = brightness
        self.driver.global_brightness = int(0b11111 * self.brightness / 100)

    def set_color(self, color, num_led=None, led_index=None):
        """Set all LEDs to a specific color or a specific LED's color."""
        rgb = self.COLORS_RGB.get(color.lower(), (0, 0, 0))
        
        if led_index is not None:
            if 0 <= led_index < self.driver.num_led:
                self.driver.set_pixel(led_index, rgb[0], rgb[1], rgb[2])
            else:
                raise ValueError(f"LED index {led_index} is out of range.")
        else:
            if num_led is None:
                num_led = self.driver.num_led
            for i in range(num_led):
                self.driver.set_pixel(i, rgb[0], rgb[1], rgb[2])
        
        self.driver.show()

    def set_color_rgb(self, rgb_tuple, num_led=None, led_index=None):
        """Set all LEDs to a specific RGB color or a specific LED's color."""
        if led_index is not None:
            if 0 <= led_index < self.driver.num_led:
                self.driver.set_pixel(led_index, rgb_tuple[0], rgb_tuple[1], rgb_tuple[2])
            else:
                raise ValueError(f"LED index {led_index} is out of range.")
        else:
            if num_led is None:
                num_led = self.driver.num_led
            for i in range(num_led):
                self.driver.set_pixel(i, rgb_tuple[0], rgb_tuple[1], rgb_tuple[2])
        self.driver.show()

    def rotate(self, positions=1):
        """
        Rotate the LEDs by the specified number of positions.

        Treating the LED strip as a circular buffer, this method rotates the LEDs
        by the given number of positions. A positive value rotates the LEDs forward,
        while a negative value rotates them backward.

        Args:
            positions (int): Number of positions to rotate. Positive values rotate
                            forward, negative values rotate backward.
        """
        self.driver.rotate(positions)
        self.driver.show()

    def _get_wheel_color(self, wheel_pos):
        """Get a color from a color wheel; Green -> Red -> Blue -> Green."""
        wheel_pos = wheel_pos % 256
        if wheel_pos < 85:
            return (wheel_pos * 3, 255 - wheel_pos * 3, 0)
        elif wheel_pos < 170:
            wheel_pos -= 85
            return (255 - wheel_pos * 3, 0, wheel_pos * 3)
        else:
            wheel_pos -= 170
            return (0, wheel_pos * 3, 255 - wheel_pos * 3)

    def clear(self):
        """Clear all LEDs without turning them off."""
        for i in range(self.num_led):
            self.driver.set_pixel(i, 0, 0, 0)
        self.driver.show()

    def wheel(self, use_rainbow=True, color='white', interval=0.2):
        self.stop_animation()
        self.running = True

        def _run():
            while self.running:
                for i in range(self.num_led):
                    if use_rainbow:
                        rgb = self._get_wheel_color(int(256 / self.num_led * i))
                    else:
                        rgb = self.COLORS_RGB.get(color.lower(), (0, 0, 0))
                    
                    self.clear()  # Clears all LEDs before lighting up the next one
                    self.driver.set_pixel(i, rgb[0], rgb[1], rgb[2])
                    self.driver.show()
                    time.sleep(interval)
            self.clear()
            self.running = False

        self.thread = threading.Thread(target=_run)
        self.thread.start()

    def wheel_fill(self, use_rainbow=True, color='white', interval=0.2):
        self.stop_animation()

        def _run():
                for i in range(self.num_led):
                    if use_rainbow:
                        rgb = self._get_wheel_color(int(256 / self.num_led * i))
                    else:
                        rgb = self.COLORS_RGB.get(color.lower(), (0, 0, 0))
                    
                    self.driver.set_pixel(i, rgb[0], rgb[1], rgb[2])  # Does not clear LEDs
                    self.driver.show()
                    time.sleep(interval)

        self.thread = threading.Thread(target=_run)
        self.thread.start()

    def pulse(self, base_color='blue', pulse_color='red', pulse_speed=0.3):
        """Pulse the LEDs between base color and pulse color to simulate speaking."""
        self.stop_animation()
        self.running = True

        def _run():
            while self.running:
                self.set_color(base_color)
                time.sleep(pulse_speed)
                self.set_color(pulse_color)
                time.sleep(pulse_speed)

        self.thread = threading.Thread(target=_run)
        self.thread.start()

    def pulse_smoothly(self, base_color='blue', pulse_color='green', pulse_speed=0.05):
        """Pulse the LEDs smoothly between base color and pulse color."""
        self.stop_animation()
        self.running = True

        def _run():
            base_rgb = self.COLORS_RGB.get(base_color.lower(), (0, 0, 0))
            pulse_rgb = self.COLORS_RGB.get(pulse_color.lower(), (0, 0, 0))
            while self.running:
                for i in range(0, 100, 5):
                    interp_rgb = (
                        int(base_rgb[0] + (pulse_rgb[0] - base_rgb[0]) * i / 100),
                        int(base_rgb[1] + (pulse_rgb[1] - base_rgb[1]) * i / 100),
                        int(base_rgb[2] + (pulse_rgb[2] - base_rgb[2]) * i / 100)
                    )
                    self.set_color_rgb(interp_rgb)
                    time.sleep(pulse_speed)
                for i in range(100, 0, -5):
                    interp_rgb = (
                        int(base_rgb[0] + (pulse_rgb[0] - base_rgb[0]) * i / 100),
                        int(base_rgb[1] + (pulse_rgb[1] - base_rgb[1]) * i / 100),
                        int(base_rgb[2] + (pulse_rgb[2] - base_rgb[2]) * i / 100)
                    )
                    self.set_color_rgb(interp_rgb)
                    time.sleep(pulse_speed)

        self.thread = threading.Thread(target=_run)
        self.thread.start()

