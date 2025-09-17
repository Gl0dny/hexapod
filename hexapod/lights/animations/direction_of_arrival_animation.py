from __future__ import annotations
from typing import TYPE_CHECKING, override, Optional
import math

from hexapod.lights.animations import Animation
from hexapod.lights import ColorRGB

if TYPE_CHECKING:
    from typing import Dict
    from hexapod.lights import Lights


class DirectionOfArrivalAnimation(Animation):
    """
    Animation that visualizes Direction of Arrival (DoA) data using LEDs.
    The LEDs light up based on the calculated direction of sound sources.
    Each source (up to 4) gets a different color to distinguish between multiple sources.

    Attributes:
        base_color (ColorRGB): The default color for active sound sources.
        refresh_delay (float): The interval between updates.
        source_colors (list[ColorRGB]): List of distinct colors for different sources.
    """

    def __init__(
        self,
        lights: Lights,
        refresh_delay: float = 0.1,
        source_colors: list[ColorRGB] = [
            ColorRGB.TEAL,  # First source
            ColorRGB.INDIGO,  # Second source
            ColorRGB.YELLOW,  # Third source
            ColorRGB.LIME,  # Fourth source
        ],
    ) -> None:
        """
        Initialize the DirectionOfArrivalAnimation object.

        Args:
            lights (Lights): The Lights object to control the LEDs.
            refresh_delay (float): The interval between updates.
            source_colors (list[ColorRGB]): List of colors for different sound sources.
                Defaults to [TEAL, INDIGO, YELLOW, LIME].
        """
        super().__init__(lights)
        self.refresh_delay: float = refresh_delay
        self.tracked_sources: Dict[int, Dict] = {}
        self.active_leds: set[int] = set()  # Keep track of currently lit LEDs
        self.source_colors: list[ColorRGB] = source_colors

    def update_sources(self, azimuths: Dict[int, float]) -> None:
        """
        Update the current sound sources with their azimuths.

        Args:
            azimuths (Dict[int, float]): Dictionary of tracked sound sources with their azimuths (degrees).
        """
        self.azimuths = azimuths

    def _get_led_indices_from_azimuth(self, azimuth: float) -> set[int]:
        """
        Convert azimuth (degrees) to a set of LED indices, including adjacent LEDs.

        Args:
            azimuth (float): Azimuth angle in degrees (0-360).

        Returns:
            set[int]: Set of LED indices to light up (main direction and adjacent LEDs).
        """
        angle = math.radians(azimuth)
        # Adjust angle to match hexapod orientation (front at pi/2)
        angle = (math.pi / 2 - angle) % (2 * math.pi)
        main_index = int((angle / (2 * math.pi)) * self.lights.num_led)
        left_index = (main_index - 1) % self.lights.num_led
        right_index = (main_index + 1) % self.lights.num_led
        return {main_index, left_index, right_index}

    @override
    def execute_animation(self) -> None:
        """
        Run the animation logic.
        """
        while not self.stop_event.is_set():
            # Clear all LEDs first
            self.lights.clear()

            # Keep track of currently active LEDs
            current_active_leds: set[int] = set()

            # Light up LEDs for tracked sources
            for i, (source_id, azimuth) in enumerate(
                getattr(self, "azimuths", {}).items()
            ):
                # Get color for this source (cycle through colors if more than 4 sources)
                color = self.source_colors[i % len(self.source_colors)]
                led_indices = self._get_led_indices_from_azimuth(azimuth)
                for led_index in led_indices:
                    self.lights.set_color(color, led_index=led_index)
                    current_active_leds.add(led_index)

            # Update the set of active LEDs
            self.active_leds = current_active_leds

            # Wait for the next update
            if self.stop_event.wait(self.refresh_delay):
                return
