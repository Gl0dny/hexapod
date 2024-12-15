from gpiozero import LED
from lights.apa102 import APA102


class Lights:
    """
    A class to control the LED lights based on APA102.

    Attributes:
        COLORS_RGB (dict): A dictionary mapping color names to their RGB values.
        num_led (int): The number of LEDs.
        driver (APA102): The driver for the APA102 LEDs.
        power (LED): The power control for the LEDs.
        led_color (str): The initial color of the LEDs.
        brightness (int): The brightness of the LEDs (0-100).
    """

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
        """
        Initialize the Lights object.

        Args:
            num_led (int): The number of LEDs.
            power_pin (int): The GPIO pin used to control the power.
            brightness (int): The initial brightness of the LEDs (0-100).
            initial_color (str): The initial color of the LEDs.
        """
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
        """
        Set the brightness of the LEDs.

        Args:
            brightness (int): The brightness level (0-100).
        """
        if brightness > 100:
            brightness = 100
        elif brightness < 0:
            brightness = 0
        self.brightness = brightness
        self.driver.global_brightness = int(0b11111 * self.brightness / 100)

    def set_color(self, color, num_led=None, led_index=None):
        """
        Set the color of the LEDs using COLORS_RGB dictionary.

        Args:
            color (str): The color name.
            num_led (int, optional): The number of LEDs to set.
            led_index (int, optional): The index of the LED to set.
        
        Raises:
            ValueError: If the color is unknown or the LED index is out of range.
        """
        if color.lower() not in self.COLORS_RGB:
            raise ValueError(f"Unknown color '{color}'. Please use a valid color name.")
        rgb = self.COLORS_RGB[color.lower()]

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
        """
        Set the color of the LEDs using an RGB tuple.

        Args:
            rgb_tuple (tuple): The RGB values.
            num_led (int, optional): The number of LEDs to set.
            led_index (int, optional): The index of the LED to set.
        
        Raises:
            ValueError: If the LED index is out of range.
        """
        if led_index is not None:
            if 0 <= led_index < self.driver.num_led:
                self.driver.set_pixel(
                    led_index, rgb_tuple[0], rgb_tuple[1], rgb_tuple[2])
            else:
                raise ValueError(f"LED index {led_index} is out of range.")
        else:
            if num_led is None:
                num_led = self.driver.num_led
            for i in range(num_led):
                self.driver.set_pixel(
                    i, rgb_tuple[0], rgb_tuple[1], rgb_tuple[2])
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

    def get_wheel_color(self, wheel_pos):
        """
        Get a color from a color wheel; Green -> Red -> Blue -> Green.

        The color wheel is divided into three main sections:
        - From 0 to 84: Green to Red transition.
        - From 85 to 169: Red to Blue transition.
        - From 170 to 255: Blue to Green transition.

        Args:
            wheel_pos (int): Position on the color wheel (0-255).

        Returns:
            tuple: (R, G, B) color values.
        """
        wheel_pos = wheel_pos % 256
        if wheel_pos < 85:
            # Green to Red transition
            return (wheel_pos * 3, 255 - wheel_pos * 3, 0)
        elif wheel_pos < 170:
            # Red to Blue transition
            wheel_pos -= 85
            return (255 - wheel_pos * 3, 0, wheel_pos * 3)
        else:
            # Blue to Green transition
            wheel_pos -= 170
            return (0, wheel_pos * 3, 255 - wheel_pos * 3)

    def clear(self, led_indices=None, count=None):
        """
        Clear specified LEDs, turning them off. If no indices are provided, clear all LEDs.
        If count is provided, clear the specified number of LEDs from the start.
        
        Args:
            led_indices (list, optional): List of LED indices to clear.
            count (int, optional): Number of LEDs to clear from the start.
        """
        if led_indices is not None:
            leds_to_clear = led_indices
        elif count is not None:
            leds_to_clear = range(count)
        else:
            leds_to_clear = range(self.num_led)
        for i in leds_to_clear:
            self.driver.set_pixel(i, 0, 0, 0)
        self.driver.show()
