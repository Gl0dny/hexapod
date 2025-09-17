from __future__ import annotations
from typing import TYPE_CHECKING, override
import logging

from hexapod.lights.animations import Animation
from hexapod.lights import ColorRGB

if TYPE_CHECKING:
    from typing import Optional
    from hexapod.lights import Lights

logger = logging.getLogger("lights_logger")


class WheelFillAnimation(Animation):
    """
    Animation that fills the LEDs with colors from a color wheel.

    Attributes:
        use_rainbow (bool): Whether to use rainbow colors.
        color (Optional[ColorRGB]): The color to use if not using rainbow colors.
        interval (float): The interval between filling LEDs.
    """

    def __init__(
        self,
        lights: Lights,
        use_rainbow: bool = True,
        color: Optional[ColorRGB] = None,
        interval: float = 1,
    ) -> None:
        """
        Initialize the WheelFillAnimation object.

        Args:
            lights (Lights): The Lights object to control the LEDs.
            use_rainbow (bool): Whether to use rainbow colors.
            color (Optional[ColorRGB]): The color to use if not using rainbow colors.
            interval (float): The interval between filling LEDs.

        Raises:
            ValueError: If `use_rainbow` is False and `color` is not provided.
        """
        super().__init__(lights)
        if not use_rainbow and color is None:
            logger.error("color must be provided when use_rainbow is False.")
            raise ValueError("color must be provided when use_rainbow is False.")
        self.use_rainbow: bool = use_rainbow
        self.color: Optional[ColorRGB] = color
        self.interval: float = interval

    @override
    def execute_animation(self) -> None:
        """
        Run the animation logic.
        """
        for i in range(self.lights.num_led):
            if self.stop_event.wait(self.interval):
                return

            if self.use_rainbow:
                rgb = self.lights.get_wheel_color(int(256 / self.lights.num_led * i))
            else:
                rgb = self.color.rgb if self.color else (0, 0, 0)

            self.lights.set_color_rgb(rgb_tuple=rgb, led_index=i)
