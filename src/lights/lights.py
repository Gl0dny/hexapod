from __future__ import annotations
from typing import TYPE_CHECKING
import logging
from enum import Enum

# Import gpiozero to configure the GPIO backend
import gpiozero
# Force GPIOZero to use RPi.GPIO backend instead of lgpio
# This is necessary because lgpio requires GLIBC 2.33+ which isn't available on the hexapod's system
# RPi.GPIO is more stable and compatible with older systems
from gpiozero.pins.rpigpio import RPiGPIOFactory
gpiozero.Device.pin_factory = RPiGPIOFactory()

from gpiozero import LED

from lights.apa102 import APA102

if TYPE_CHECKING:
    from typing import Optional, Tuple, List

logger = logging.getLogger("lights_logger")

class ColorRGB(Enum):
    """
    Enumeration of RGB colors for the Lights system.
    
    Each member represents a specific color with its corresponding RGB values.
    """
    BLACK = (0, 0, 0)
    BLUE = (0, 0, 255)
    TEAL = (0, 128, 128)
    GREEN = (0, 255, 0)
    LIME = (75, 180, 0)
    YELLOW = (255, 215, 0)
    GOLDEN = (255, 50, 0)
    ORANGE = (255, 25, 0)
    RED = (255, 0, 0)
    PINK = (255, 51, 183)
    PURPLE = (128, 0, 128)
    INDIGO = (75, 0, 130)
    GRAY = (139, 69, 19)
    WHITE = (255, 255, 255)
    
    @property
    def rgb(self) -> Tuple[int, int, int]:
        return self.value

class Lights:
    """
    A class to control the LED lights based on APA102.

    Attributes:
        num_led (int): The number of LEDs.
        driver (APA102): The driver for the APA102 LEDs.
        power (LED): The power control for the LEDs.
        led_color (ColorRGB): The initial color of the LEDs.
        brightness (int): The brightness of the LEDs (0-100).
    """

    DEFAULT_NUM_LED: int = 12 # Default number of LEDs in the hardware
    DEFAULT_POWER_PIN: int = 5 # Default GPIO pin number for LED power control

    def __init__(
        self,
        num_led: int = DEFAULT_NUM_LED,
        power_pin: int = DEFAULT_POWER_PIN,
        brightness: int = 50,
        initial_color: ColorRGB = ColorRGB.INDIGO
    ) -> None:
        """
        Initialize the Lights object.

        Args:
            num_led (int): The number of LEDs.
            power_pin (int): The GPIO pin used to control the power.
            brightness (int): The initial brightness of the LEDs (0-100).
            initial_color (ColorRGB): The initial color of the LEDs.
        """
        self.num_led: int = num_led
        self.driver: APA102 = APA102(num_led=self.num_led)
        self.power: LED = LED(power_pin)
        self.power.on()
        self.led_color: ColorRGB = initial_color
        self.brightness: int = brightness  # Percentage (0-100)

        self.set_brightness(self.brightness)
        logger.debug(f"Lights initialized successfully with {num_led} LEDs.")

    def set_brightness(self, brightness: int) -> None:
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
        logger.info(f"Brightness set to {brightness}%.")

    def set_color(self, color: ColorRGB, num_led: Optional[int] = None, led_index: Optional[int] = None) -> None:
        """
        Set the color of the LEDs using the ColorRGB enum.

        Args:
            color (ColorRGB): The color enum member to set.
            num_led (int, optional): The number of LEDs to set.
            led_index (int, optional): The index of the LED to set.
        
        Raises:
            ValueError: If the LED index is out of range, RGB tuple is invalid, or color is not a ColorRGB member.
        """
        # Validate that 'color' is an instance of ColorRGB
        if not isinstance(color, ColorRGB):
            logger.error(f"Invalid color: {color}. Available colors: {', '.join([c.name for c in ColorRGB])}")
            raise ValueError(f"Invalid color: {color}. Available colors: {', '.join([c.name for c in ColorRGB])}")

        rgb = color.rgb

        # Validate rgb_tuple
        if not (isinstance(rgb, tuple) and len(rgb) == 3 and
                all(isinstance(val, int) and 0 <= val <= 255 for val in rgb)):
            logger.error(f"Invalid RGB tuple: {rgb}. Must be a tuple of three integers between 0 and 255.")
            raise ValueError(f"Invalid RGB tuple: {rgb}. Must be a tuple of three integers between 0 and 255.")
        
        if led_index is not None:
            if 0 <= led_index < self.driver.num_led:
                self.driver.set_pixel(led_index, rgb[0], rgb[1], rgb[2])
            else:
                logger.error(f"LED index {led_index} is out of range.")
                raise ValueError(f"LED index {led_index} is out of range.")
        else:
            if num_led is None:
                num_led = self.driver.num_led
            for i in range(num_led):
                self.driver.set_pixel(i, rgb[0], rgb[1], rgb[2])

        self.driver.show()
        logger.debug(f"{'LED ' + str(led_index) if led_index is not None else 'All LEDs'} set to {color.name}.")

    def set_color_rgb(self, rgb_tuple: Tuple[int, int, int], num_led: Optional[int] = None, led_index: Optional[int] = None) -> None:
        """
        Set the color of the LEDs using an RGB tuple.

        Args:
            rgb_tuple (tuple): The RGB values.
            num_led (int, optional): The number of LEDs to set.
            led_index (int, optional): The index of the LED to set.
        
        Raises:
            ValueError: If the LED index is out of range or RGB values are invalid.
        """
        # Validate rgb_tuple
        if not (isinstance(rgb_tuple, tuple) and len(rgb_tuple) == 3 and
                all(isinstance(val, int) and 0 <= val <= 255 for val in rgb_tuple)):
            logger.error(f"Invalid RGB tuple: {rgb_tuple}. Must be a tuple of three integers between 0 and 255.")
            raise ValueError(f"Invalid RGB tuple: {rgb_tuple}. Must be a tuple of three integers between 0 and 255.")
        
        if led_index is not None:
            if 0 <= led_index < self.driver.num_led:
                self.driver.set_pixel(
                    led_index, rgb_tuple[0], rgb_tuple[1], rgb_tuple[2])
            else:
                logger.error(f"LED index {led_index} is out of range.")
                raise ValueError(f"LED index {led_index} is out of range.")
        else:
            if num_led is None:
                num_led = self.driver.num_led
            for i in range(num_led):
                self.driver.set_pixel(
                    i, rgb_tuple[0], rgb_tuple[1], rgb_tuple[2])
        self.driver.show()
        logger.debug(f"{'LED ' + str(led_index) if led_index is not None else 'All LEDs'} set to RGB {rgb_tuple}.")

    def rotate(self, positions: int = 1) -> None:
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
        logger.debug(f"Rotated LEDs by {positions} positions.")

    def get_wheel_color(self, wheel_pos: int) -> Tuple[int, int, int]:
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
            color = (wheel_pos * 3, 255 - wheel_pos * 3, 0)
        elif wheel_pos < 170:
            # Red to Blue transition
            wheel_pos -= 85
            color = (255 - wheel_pos * 3, 0, wheel_pos * 3)
        else:
            # Blue to Green transition
            wheel_pos -= 170
            color = (0, wheel_pos * 3, 255 - wheel_pos * 3)
        logger.debug(f"Wheel color obtained: {color}.")
        return color

    def clear(self, led_indices: Optional[List[int]] = None, count: Optional[int] = None) -> None:
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
        logger.info(f"{'LEDs ' + str(led_indices) if led_indices is not None else 'All LEDs'} cleared.")
