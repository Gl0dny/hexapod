from __future__ import annotations
from typing import TYPE_CHECKING, override
import logging

from hexapod.lights.animations import Animation
from hexapod.lights import ColorRGB

if TYPE_CHECKING:
    from typing import Dict
    from hexapod.lights import Lights

logger = logging.getLogger("lights_logger")


class CalibrationAnimation(Animation):
    """
    Animation that updates LED colors based on the calibration status of each leg.

    This animation sets LEDs to:
        - Yellow when a leg is calibrating.
        - Green when a leg is calibrated.
        - Red when a leg is not calibrated.
    """

    def __init__(
        self,
        lights: Lights,
        calibration_status: Dict[int, str],
        leg_to_led: Dict[int, int],
        refresh_delay: float = 1.0,
    ) -> None:
        """
        Initialize the CalibrationAnimation.

        Args:
            lights (Lights): The Lights object to control the LEDs.
            calibration_status (Dict[int, str]): Current calibration status of each leg.
            leg_to_led (Dict[int, int]): Mapping from leg indices to LED indices.
            refresh_delay (float): The interval between updates.
        """
        super().__init__(lights)
        self.calibration_status = calibration_status
        self.leg_to_led = leg_to_led
        self.refresh_delay: float = refresh_delay

    @override
    def execute_animation(self) -> None:
        """
        Run the animation logic.
        """
        while not self.stop_event.is_set():
            status_color_map = {
                "calibrating": ColorRGB.YELLOW,
                "calibrated": ColorRGB.GREEN,
                "not_calibrated": ColorRGB.RED,
            }
            for leg_index, led_index in self.leg_to_led.items():
                status = self.calibration_status.get(leg_index)
                if status is None:
                    continue  # Skip if no status available
                color = status_color_map.get(status)
                if color is None:
                    raise ValueError(f"Invalid calibration status: {status}")
                self.lights.set_color(color, led_index=led_index)
            if self.stop_event.wait(self.refresh_delay):
                return
