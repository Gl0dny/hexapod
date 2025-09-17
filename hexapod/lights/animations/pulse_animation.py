from __future__ import annotations
from typing import TYPE_CHECKING, override

from hexapod.lights.animations import Animation
from hexapod.lights import ColorRGB

if TYPE_CHECKING:
    from hexapod.lights import Lights


class PulseAnimation(Animation):
    """
    Animation that pulses between two colors.

    Attributes:
        base_color (ColorRGB): The base color.
        pulse_color (ColorRGB): The pulse color.
        pulse_speed (float): The speed of the pulse.
    """

    def __init__(
        self,
        lights: Lights,
        base_color: ColorRGB = ColorRGB.BLUE,
        pulse_color: ColorRGB = ColorRGB.RED,
        pulse_speed: float = 0.3,
    ) -> None:
        """
        Initialize the PulseAnimation object.

        Args:
            lights (Lights): The Lights object to control the LEDs.
            base_color (ColorRGB): The base color.
            pulse_color (ColorRGB): The pulse color.
            pulse_speed (float): The speed of the pulse.
        """
        super().__init__(lights)
        self.base_color: ColorRGB = base_color
        self.pulse_color: ColorRGB = pulse_color
        self.pulse_speed: float = pulse_speed

    @override
    def execute_animation(self) -> None:
        """
        Run the animation logic.
        """
        while not self.stop_event.is_set():
            if self.stop_event.wait(self.pulse_speed):
                return

            self.lights.set_color(self.base_color)

            if self.stop_event.wait(self.pulse_speed):
                return

            self.lights.set_color(self.pulse_color)
