from __future__ import annotations
from typing import TYPE_CHECKING, override
import logging

from hexapod.lights.animations import Animation
from hexapod.lights import ColorRGB

if TYPE_CHECKING:
    from hexapod.lights import Lights

logger = logging.getLogger("lights_logger")


class PulseSmoothlyAnimation(Animation):
    """
    Animation that smoothly pulses between two colors.

    Attributes:
        base_color (ColorRGB): The base color.
        pulse_color (ColorRGB): The pulse color.
        pulse_speed (float): The speed of the pulse.
    """

    def __init__(
        self,
        lights: Lights,
        base_color: ColorRGB = ColorRGB.BLUE,
        pulse_color: ColorRGB = ColorRGB.GREEN,
        pulse_speed: float = 0.05,
    ) -> None:
        """
        Initialize the PulseSmoothlyAnimation object.

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
        base_rgb = self.base_color.rgb
        pulse_rgb = self.pulse_color.rgb
        while not self.stop_event.is_set():
            for i in range(0, 100, 5):
                if self.stop_event.wait(self.pulse_speed):
                    return

                interp_rgb = (
                    int(base_rgb[0] + (pulse_rgb[0] - base_rgb[0]) * i / 100),
                    int(base_rgb[1] + (pulse_rgb[1] - base_rgb[1]) * i / 100),
                    int(base_rgb[2] + (pulse_rgb[2] - base_rgb[2]) * i / 100),
                )
                self.lights.set_color_rgb(interp_rgb)

            for i in range(100, 0, -5):
                if self.stop_event.wait(self.pulse_speed):
                    return

                interp_rgb = (
                    int(base_rgb[0] + (pulse_rgb[0] - base_rgb[0]) * i / 100),
                    int(base_rgb[1] + (pulse_rgb[1] - base_rgb[1]) * i / 100),
                    int(base_rgb[2] + (pulse_rgb[2] - base_rgb[2]) * i / 100),
                )
                self.lights.set_color_rgb(interp_rgb)
