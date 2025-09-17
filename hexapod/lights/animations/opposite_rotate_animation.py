from __future__ import annotations
from typing import TYPE_CHECKING, override
import logging

from hexapod.lights.animations import Animation
from hexapod.lights import ColorRGB

if TYPE_CHECKING:
    from hexapod.lights import Lights

logger = logging.getLogger("lights_logger")


class OppositeRotateAnimation(Animation):
    """
    Animation that lights up LEDs moving in opposite directions, creating a symmetrical effect.
    The animation lights up LEDs starting from a point and moves outward in opposite directions.
    After reaching the ends, it reverses direction and repeats the process.

    Attributes:
        FORWARD (int): Constant representing the forward direction.
        BACKWARD (int): Constant representing the backward direction.
        interval (float): Time interval between LED updates.
        color (ColorRGB): ColorRGB of the LEDs.
        direction (int): Current direction of the animation.
    """

    FORWARD: int = 1
    BACKWARD: int = -1

    def __init__(
        self, lights: Lights, interval: float = 0.1, color: ColorRGB = ColorRGB.WHITE
    ) -> None:
        """
        Initialize the OppositeRotateAnimation object.

        Args:
            lights (Lights): The Lights object to control the LEDs.
            interval (float): Time interval between LED updates.
            color (ColorRGB): ColorRGB of the LEDs.
        """
        super().__init__(lights)
        self.interval: float = interval
        self.color: ColorRGB = color
        self.direction: int = self.FORWARD

    @override
    def execute_animation(self) -> None:
        """
        Run the animation logic.
        """
        num_leds = self.lights.num_led
        start_index = 0
        while not self.stop_event.is_set():
            # Light up the starting LED
            if self.stop_event.wait(self.interval):
                return

            self.lights.clear()
            self.lights.set_color(self.color, led_index=start_index)

            # Fork into two LEDs moving in opposite directions
            max_offset = (num_leds + 1) // 2  # Handles even and odd numbers of LEDs
            for offset in range(1, max_offset):
                if self.stop_event.wait(self.interval):
                    return

                index1 = (start_index + offset * self.direction) % num_leds
                index2 = (start_index - offset * self.direction) % num_leds

                self.lights.clear()
                self.lights.set_color(self.color, led_index=index1)
                self.lights.set_color(self.color, led_index=index2)

            # Merge back into one LED at the opposite end
            end_index = (start_index + max_offset * self.direction) % num_leds
            self.lights.clear()
            self.lights.set_color(self.color, led_index=end_index)

            if self.stop_event.wait(self.interval):
                return

            # Switch direction and update starting index
            self.direction = (
                self.BACKWARD if self.direction == self.FORWARD else self.FORWARD
            )
            start_index = end_index
