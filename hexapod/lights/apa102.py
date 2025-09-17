"""
APA102 LED Strip Driver Module.

This module provides a Python driver for controlling APA102 (DotStar) LED strips
via SPI communication. The APA102 is a programmable RGB LED with an integrated
driver chip that allows for individual pixel control and brightness adjustment.

Features:
- Individual pixel color control (RGB)
- Global and per-pixel brightness control
- Multiple color channel orderings (RGB, RBG, GRB, etc.)
- Color wheel functionality for smooth transitions
- Efficient SPI communication with hardware acceleration

Hardware Requirements:
- Raspberry Pi or compatible single-board computer
- APA102 LED strip
- SPI interface connection

Dependencies:
- spidev: For SPI communication (Linux only)
- math: For brightness calculations
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from math import ceil

import spidev

if TYPE_CHECKING:
    import List, Union

RGB_MAP = {
    "rgb": [3, 2, 1],
    "rbg": [3, 1, 2],
    "grb": [2, 3, 1],
    "gbr": [2, 1, 3],
    "brg": [1, 3, 2],
    "bgr": [1, 2, 3],
}


class APA102:
    """
    Driver for APA102 LEDS (aka "DotStar").

    Public methods are:
     - set_pixel
     - set_pixel_rgb
     - show
     - clear_strip
     - cleanup

    Helper methods for color manipulation are:
     - combine_color
     - wheel

    The rest of the methods are used internally and should not be used by the
    user of the library.

    Very brief overview of APA102: An APA102 LED is addressed with SPI. The bits
    are shifted in one by one, starting with the least significant bit.

    An LED usually just forwards everything that is sent to its data-in to
    data-out. While doing this, it remembers its own color and keeps glowing
    with that color as long as there is power.

    An LED can be switched to not forward the data, but instead use the data
    to change it's own color. This is done by sending (at least) 32 bits of
    zeroes to data-in. The LED then accepts the next correct 32 bit LED
    frame (with color information) as its new color setting.

    After having received the 32 bit color frame, the LED changes color,
    and then resumes to just copying data-in to data-out.

    The really clever bit is this: While receiving the 32 bit LED frame,
    the LED sends zeroes on its data-out line. Because a color frame is
    32 bits, the LED sends 32 bits of zeroes to the next LED.
    As we have seen above, this means that the next LED is now ready
    to accept a color frame and update its color.

    So that's really the entire protocol:
    - Start by sending 32 bits of zeroes. This prepares LED 1 to update
      its color.
    - Send color information one by one, starting with the color for LED 1,
      then LED 2 etc.
    - Finish off by cycling the clock line a few times to get all data
      to the very last LED on the strip

    The last step is necessary, because each LED delays forwarding the data
    a bit. Imagine ten people in a row. When you yell the last color
    information, i.e. the one for person ten, to the first person in
    the line, then you are not finished yet. Person one has to turn around
    and yell it to person 2, and so on. So it takes ten additional "dummy"
    cycles until person ten knows the color. When you look closer,
    you will see that not even person 9 knows its own color yet. This
    information is still with person 2. Essentially the driver sends additional
    zeroes to LED 1 as long as it takes for the last color frame to make it
    down the line to the last LED.
    """

    # Constants
    MAX_BRIGHTNESS = 0b11111  # Safeguard: Set to a value appropriate for your setup
    LED_START = 0b11100000  # Three "1" bits, followed by 5 brightness bits

    def __init__(
        self,
        num_led: int,
        global_brightness: int = MAX_BRIGHTNESS,
        order: str = "rgb",
        bus: int = 0,
        device: int = 1,
        max_speed_hz: int = 8000000,
    ) -> None:
        """Initialize the APA102 LED strip driver.

        Args:
            num_led (int): Number of LEDs in the strip.
            global_brightness (int, optional): Global brightness level (0-31). Defaults to MAX_BRIGHTNESS.
            order (str, optional): Color channel order ('rgb', 'rbg', 'grb', 'gbr', 'brg', 'bgr'). Defaults to 'rgb'.
            bus (int, optional): SPI bus number. Defaults to 0.
            device (int, optional): SPI device number. Defaults to 1.
            max_speed_hz (int, optional): Maximum SPI speed in Hz. Defaults to 8000000.

        Raises:
            ImportError: If spidev module is not available.
        """
        self.num_led: int = num_led  # The number of LEDs in the Strip
        order = order.lower()
        self.rgb: List[int] = RGB_MAP.get(order, RGB_MAP["rgb"])
        # Limit the brightness to the maximum if it's set higher
        self.global_brightness: int = min(global_brightness, self.MAX_BRIGHTNESS)

        self.leds: List[int] = [self.LED_START, 0, 0, 0] * self.num_led  # Pixel buffer
        if spidev is None:
            raise ImportError("spidev module is required but not available")
        self.spi = spidev.SpiDev()  # Init the SPI device
        self.spi.open(bus, device)  # Open SPI port 0, slave device (CS) 1
        # Up the speed a bit, so that the LEDs are painted faster
        if max_speed_hz:
            self.spi.max_speed_hz = max_speed_hz

    def clock_start_frame(self) -> None:
        """Sends a start frame to the LED strip.

        This method clocks out a start frame, telling the receiving LED
        that it must update its own color now.
        """
        self.spi.xfer2([0] * 4)  # Start frame, 32 zero bits

    def clock_end_frame(self) -> None:
        """Sends an end frame to the LED strip.

        As explained above, dummy data must be sent after the last real colour
        information so that all of the data can reach its destination down the line.
        The delay is not as bad as with the human example above.
        It is only 1/2 bit per LED. This is because the SPI clock line
        needs to be inverted.

        Say a bit is ready on the SPI data line. The sender communicates
        this by toggling the clock line. The bit is read by the LED
        and immediately forwarded to the output data line. When the clock goes
        down again on the input side, the LED will toggle the clock up
        on the output to tell the next LED that the bit is ready.

        After one LED the clock is inverted, and after two LEDs it is in sync
        again, but one cycle behind. Therefore, for every two LEDs, one bit
        of delay gets accumulated. For 300 LEDs, 150 additional bits must be fed to
        the input of LED one so that the data can reach the last LED.

        Ultimately, we need to send additional numLEDs/2 arbitrary data bits,
        in order to trigger numLEDs/2 additional clock changes. This driver
        sends zeroes, which has the benefit of getting LED one partially or
        fully ready for the next update to the strip. An optimized version
        of the driver could omit the "clockStartFrame" method if enough zeroes have
        been sent as part of "clockEndFrame".
        """

        self.spi.xfer2([0xFF] * 4)

        # Round up num_led/2 bits (or num_led/16 bytes)
        # for _ in range((self.num_led + 15) // 16):
        #    self.spi.xfer2([0x00])

    def clear_strip(self) -> None:
        """Turns off the strip and shows the result right away."""

        for led in range(self.num_led):
            self.set_pixel(led, 0, 0, 0)
        self.show()

    def set_pixel(
        self, led_num: int, red: int, green: int, blue: int, bright_percent: int = 100
    ) -> None:
        """Set the color of one pixel in the LED strip.

        The changed pixel is not shown yet on the strip, it is only
        written to the pixel buffer. Colors are passed individually.
        If brightness is not set the global brightness setting is used.

        Args:
            led_num (int): LED index (0-based).
            red (int): Red component (0-255).
            green (int): Green component (0-255).
            blue (int): Blue component (0-255).
            bright_percent (int, optional): Brightness percentage (0-100). Defaults to 100.

        Raises:
            ValueError: If color values are not integers between 0 and 255.
        """
        if not all(
            isinstance(val, int) and 0 <= val <= 255 for val in [red, green, blue]
        ):
            raise ValueError("red, green, and blue must be integers between 0 and 255.")

        if led_num < 0:
            return  # Pixel is invisible, so ignore
        if led_num >= self.num_led:
            return  # again, invisible

        # Calculate pixel brightness as a percentage of the
        # defined global_brightness. Round up to nearest integer
        # as we expect some brightness unless set to 0
        brightness = int(ceil(bright_percent * self.global_brightness / 100.0))

        # LED startframe is three "1" bits, followed by 5 brightness bits
        ledstart = (brightness & 0b00011111) | self.LED_START

        start_index = 4 * led_num
        self.leds[start_index] = ledstart
        self.leds[start_index + self.rgb[0]] = red
        self.leds[start_index + self.rgb[1]] = green
        self.leds[start_index + self.rgb[2]] = blue

    def set_pixel_rgb(
        self, led_num: int, rgb_color: int, bright_percent: int = 100
    ) -> None:
        """Set the color of one pixel in the LED strip using combined RGB value.

        The changed pixel is not shown yet on the strip, it is only
        written to the pixel buffer. Colors are passed as a combined
        24-bit integer value (3 bytes concatenated).
        If brightness is not set the global brightness setting is used.

        Args:
            led_num (int): LED index (0-based).
            rgb_color (int): Combined RGB color value (0x000000 to 0xFFFFFF).
            bright_percent (int, optional): Brightness percentage (0-100). Defaults to 100.

        Raises:
            ValueError: If rgb_color is not a valid 24-bit integer.
        """
        if rgb_color < 0 or rgb_color > 0xFFFFFF:
            raise ValueError(
                "rgb_color must be a 24-bit integer (0x000000 to 0xFFFFFF)."
            )

        self.set_pixel(
            led_num,
            (rgb_color & 0xFF0000) >> 16,
            (rgb_color & 0x00FF00) >> 8,
            rgb_color & 0x0000FF,
            bright_percent,
        )

    def rotate(self, positions: int = 1) -> None:
        """Rotate the LEDs by the specified number of positions.

        Treating the internal LED array as a circular buffer, rotate it by
        the specified number of positions. The number could be negative,
        which means rotating in the opposite direction.

        Args:
            positions (int, optional): Number of positions to rotate. Defaults to 1.
        """
        cutoff = 4 * (positions % self.num_led)
        self.leds = self.leds[cutoff:] + self.leds[:cutoff]

    def show(self) -> None:
        """Send the content of the pixel buffer to the strip.

        Transmits all LED data via SPI to update the physical LED strip.
        Note: More than 1024 LEDs requires more than one xfer operation.
        """
        self.clock_start_frame()
        # xfer2 kills the list, unfortunately. So it must be copied first
        # SPI takes up to 4096 Integers. So we are fine for up to 1024 LEDs.
        data = list(self.leds)
        while data:
            self.spi.xfer2(data[:32])
            data = data[32:]
        self.clock_end_frame()

    def cleanup(self) -> None:
        """Release the SPI device.

        Call this method at the end of your program to properly close
        the SPI connection and free system resources.
        """

        self.spi.close()  # Close SPI port

    @staticmethod
    def combine_color(red: int, green: int, blue: int) -> int:
        """Combine RGB components into a single 24-bit color value.

        Args:
            red (int): Red component (0-255).
            green (int): Green component (0-255).
            blue (int): Blue component (0-255).

        Returns:
            int: Combined 24-bit color value (0x000000 to 0xFFFFFF).
        """

        return (red << 16) + (green << 8) + blue

    def wheel(self, wheel_pos: int) -> int:
        """Get a color from a color wheel.

        Creates a smooth color transition: Green -> Red -> Blue -> Green.
        Useful for creating rainbow effects and smooth color transitions.

        Args:
            wheel_pos (int): Position on the color wheel (0-255).

        Returns:
            int: 24-bit RGB color value.
        """

        if wheel_pos > 255:
            wheel_pos = 255  # Safeguard
        if wheel_pos < 85:  # Green -> Red
            return self.combine_color(wheel_pos * 3, 255 - wheel_pos * 3, 0)
        if wheel_pos < 170:  # Red -> Blue
            wheel_pos -= 85
            return self.combine_color(255 - wheel_pos * 3, 0, wheel_pos * 3)
        # Blue -> Green
        wheel_pos -= 170
        return self.combine_color(0, wheel_pos * 3, 255 - wheel_pos * 3)

    def dump_array(self) -> None:
        """Dump the LED array to the console for debugging purposes.

        Prints the current state of the internal LED buffer to stdout.
        Useful for debugging color values and LED states.
        """

        print(self.leds)
