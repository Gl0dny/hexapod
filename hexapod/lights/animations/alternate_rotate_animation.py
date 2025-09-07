from __future__ import annotations
from typing import TYPE_CHECKING, override
import logging

from lights.animations import Animation
from lights import ColorRGB

if TYPE_CHECKING:
    from lights import Lights

logger = logging.getLogger("lights_logger")

class AlternateRotateAnimation(Animation):
    """
    Animation that alternates colors and rotates the LEDs.

    Attributes:
        color_even (ColorRGB): The color for even indexed LEDs.
        color_odd (ColorRGB): The color for odd indexed LEDs.
        delay (float): The delay between rotations.
        positions (int): The number of positions to rotate.
    """

    def __init__(self, lights: Lights, color_even: ColorRGB = ColorRGB.INDIGO, color_odd: ColorRGB = ColorRGB.GOLDEN, delay: float = 0.25, positions: int = 12) -> None:
        """
        Initialize the AlternateRotateAnimation object.

        Args:
            lights (Lights): The Lights object to control the LEDs.
            color_even (ColorRGB): The color for even indexed LEDs.
            color_odd (ColorRGB): The color for odd indexed LEDs.
            delay (float): The delay between rotations.
            positions (int): The number of positions to rotate.
        """
        super().__init__(lights)
        self.color_even: ColorRGB = color_even
        self.color_odd: ColorRGB = color_odd
        self.delay: float = delay
        self.positions: int = positions

    @override
    def execute_animation(self) -> None:
        """
        Run the animation logic.
        """
        for i in range(self.lights.num_led):
            if self.stop_event.wait(self.delay):
                return
            
            color = self.color_even if i % 2 == 0 else self.color_odd
            self.lights.set_color(color, led_index=i)
            
        while not self.stop_event.is_set():
            for _ in range(self.positions):
                if self.stop_event.wait(self.delay):
                    return
                
                self.lights.rotate(1)