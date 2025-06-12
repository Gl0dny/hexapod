from __future__ import annotations
from typing import TYPE_CHECKING, override, Optional
import logging
import math

from lights.animations import Animation
from lights import ColorRGB

if TYPE_CHECKING:
    from typing import Dict
    from lights import Lights

logger = logging.getLogger("lights_logger")

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
            ColorRGB.TEAL,   # First source
            ColorRGB.INDIGO,   # Second source
            ColorRGB.YELLOW,     # Third source
            ColorRGB.LIME    # Fourth source
        ]
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

    def update_sources(self, tracked_sources: Dict[int, Dict]) -> None:
        """
        Update the current sound sources with their direction of arrival.

        Args:
            tracked_sources (Dict[int, Dict]): Dictionary of tracked sound sources with their DoA data.
        """
        self.tracked_sources = tracked_sources

    def _get_led_indices_from_angle(self, x: float, y: float) -> set[int]:
        """
        Convert sound source coordinates to a set of LED indices, including adjacent LEDs.

        Args:
            x (float): X coordinate (-1.0 to 1.0), where 1.0 is right.
            y (float): Y coordinate (-1.0 to 1.0), where 1.0 is front.

        Returns:
            set[int]: Set of LED indices to light up (main direction and adjacent LEDs).
        """
        # Convert Cartesian coordinates to angle
        angle = math.atan2(y, x)
        
        # Adjust angle to match hexapod orientation:
        # - Front of hexapod is at π/2 (positive y-axis)
        # - Right of hexapod is at 0 (positive x-axis)
        # - LED 12 is at the front (π/2)
        # - LED 3 is at the right (0)
        angle = (math.pi/2 - angle) % (2 * math.pi)  # Rotate and normalize angle
        
        # Convert angle to main LED index
        # Map 0 to 2π to 0 to num_led-1
        main_index = int((angle / (2 * math.pi)) * self.lights.num_led)
        
        # Get adjacent LED indices
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
            for i, (source_id, source) in enumerate(self.tracked_sources.items()):
                if source.get('id', 0) > 0:  # Only process active sources
                    # Get color for this source (cycle through colors if more than 4 sources)
                    color = self.source_colors[i % len(self.source_colors)]
                    led_indices = self._get_led_indices_from_angle(source.get('x', 0), source.get('y', 0))
                    for led_index in led_indices:
                        self.lights.set_color(color, led_index=led_index)
                        current_active_leds.add(led_index)

            # Update the set of active LEDs
            self.active_leds = current_active_leds

            # Wait for the next update
            if self.stop_event.wait(self.refresh_delay):
                return 