"""
Unit tests for WheelFillAnimation.
"""

import pytest
from unittest.mock import Mock, patch
from hexapod.lights.animations.wheel_fill_animation import WheelFillAnimation
from hexapod.lights.lights import ColorRGB


@pytest.fixture
def mock_lights():
    """Mock Lights object."""
    mock_lights = Mock()
    mock_lights.num_led = 12
    mock_lights.set_color_rgb = Mock()
    return mock_lights


@pytest.fixture
def animation_default(mock_lights):
    """WheelFillAnimation with default parameters."""
    return WheelFillAnimation(lights=mock_lights)


@pytest.fixture
def animation_custom(mock_lights):
    """WheelFillAnimation with custom parameters."""
    return WheelFillAnimation(
        lights=mock_lights, use_rainbow=False, color=ColorRGB.RED, interval=0.5
    )


class TestWheelFillAnimation:
    """Test cases for WheelFillAnimation class."""

    def test_init_default_parameters(self, mock_lights):
        """Test initialization with default parameters."""
        with patch(
            "hexapod.lights.animations.wheel_fill_animation.Animation.__init__"
        ) as mock_super_init:
            animation = WheelFillAnimation(lights=mock_lights)

            # Verify parent initialization
            mock_super_init.assert_called_once_with(mock_lights)

            # Verify default parameters
            assert animation.use_rainbow is True
            assert animation.color is None
            assert animation.interval == 1.0

    def test_init_custom_parameters(self, mock_lights):
        """Test initialization with custom parameters."""
        with patch(
            "hexapod.lights.animations.wheel_fill_animation.Animation.__init__"
        ) as mock_super_init:
            animation = WheelFillAnimation(
                lights=mock_lights, use_rainbow=False, color=ColorRGB.RED, interval=0.5
            )

            # Verify parent initialization
            mock_super_init.assert_called_once_with(mock_lights)

            # Verify custom parameters
            assert animation.use_rainbow is False
            assert animation.color == ColorRGB.RED
            assert animation.interval == 0.5

    def test_init_validation_error(self, mock_lights):
        """Test initialization validation error."""
        with (
            patch("hexapod.lights.animations.wheel_fill_animation.Animation.__init__"),
            patch(
                "hexapod.lights.animations.wheel_fill_animation.logger"
            ) as mock_logger,
        ):

            with pytest.raises(
                ValueError, match="color must be provided when use_rainbow is False."
            ):
                WheelFillAnimation(lights=mock_lights, use_rainbow=False, color=None)

            # Verify error was logged
            mock_logger.error.assert_called_once_with(
                "color must be provided when use_rainbow is False."
            )

    def test_execute_animation_rainbow_mode(self, animation_default, mock_lights):
        """Test execute_animation in rainbow mode."""
        # Mock stop_event to allow one complete fill
        call_count = 0

        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            # Allow one complete fill (12 LEDs), then stop
            return call_count > 12

        animation_default.stop_event.wait = Mock(side_effect=mock_wait)

        animation_default.execute_animation()

        # Verify all LEDs were processed
        assert mock_lights.set_color_rgb.call_count == 12
        assert mock_lights.get_wheel_color.call_count == 12

        # Verify get_wheel_color was called with correct parameters
        calls = mock_lights.get_wheel_color.call_args_list
        for i, call in enumerate(calls):
            expected_wheel_pos = int(256 / 12 * i)
            assert call[0][0] == expected_wheel_pos

    def test_execute_animation_single_color_mode(self, animation_custom, mock_lights):
        """Test execute_animation in single color mode."""
        # Mock stop_event to allow one complete fill
        call_count = 0

        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            # Allow one complete fill (12 LEDs), then stop
            return call_count > 12

        animation_custom.stop_event.wait = Mock(side_effect=mock_wait)

        animation_custom.execute_animation()

        # Verify all LEDs were processed
        assert mock_lights.set_color_rgb.call_count == 12
        assert (
            mock_lights.get_wheel_color.call_count == 0
        )  # Should not be called in single color mode

        # Verify set_color_rgb was called with the custom color
        calls = mock_lights.set_color_rgb.call_args_list
        for i, call in enumerate(calls):
            assert call[1]["rgb_tuple"] == ColorRGB.RED.rgb
            assert call[1]["led_index"] == i

    def test_execute_animation_stop_immediately(self, animation_default, mock_lights):
        """Test execute_animation when stopped immediately."""
        # Mock stop_event to return True immediately
        animation_default.stop_event.wait = Mock(return_value=True)

        animation_default.execute_animation()

        # Verify no LEDs were processed
        mock_lights.set_color_rgb.assert_not_called()
        mock_lights.get_wheel_color.assert_not_called()

    def test_execute_animation_stop_during_fill(self, animation_default, mock_lights):
        """Test stopping during fill."""
        # Mock stop_event to allow only 3 LEDs, then stop
        call_count = 0

        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            return call_count > 3

        animation_default.stop_event.wait = Mock(side_effect=mock_wait)

        animation_default.execute_animation()

        # Verify only 3 LEDs were processed
        assert mock_lights.set_color_rgb.call_count == 3
        assert mock_lights.get_wheel_color.call_count == 3

    def test_execute_animation_custom_interval(self, animation_custom):
        """Test that custom interval is used."""
        delays = []

        def mock_wait(delay):
            delays.append(delay)
            return True  # Stop immediately

        animation_custom.stop_event.wait = Mock(side_effect=mock_wait)

        animation_custom.execute_animation()

        # Verify custom interval was used
        assert all(delay == 0.5 for delay in delays)

    def test_execute_animation_rainbow_wheel_calculation(
        self, animation_default, mock_lights
    ):
        """Test rainbow wheel position calculation."""
        # Mock stop_event to allow one complete fill
        animation_default.stop_event.wait = Mock(side_effect=[False] * 12 + [True])

        animation_default.execute_animation()

        # Verify get_wheel_color was called with correct wheel positions
        calls = mock_lights.get_wheel_color.call_args_list
        expected_positions = [int(256 / 12 * i) for i in range(12)]
        actual_positions = [call[0][0] for call in calls]
        assert actual_positions == expected_positions

    def test_execute_animation_single_led(self, mock_lights):
        """Test execute_animation with single LED."""
        mock_lights.num_led = 1
        animation = WheelFillAnimation(lights=mock_lights)

        # Mock stop_event to allow one LED
        animation.stop_event.wait = Mock(side_effect=[False, True])

        animation.execute_animation()

        # Verify single LED was processed
        assert mock_lights.set_color_rgb.call_count == 1
        assert mock_lights.get_wheel_color.call_count == 1

    def test_execute_animation_zero_leds(self, mock_lights):
        """Test execute_animation with zero LEDs."""
        mock_lights.num_led = 0
        animation = WheelFillAnimation(lights=mock_lights)

        # Mock stop_event.is_set() to return True after first check to break the while loop
        call_count = 0

        def mock_is_set():
            nonlocal call_count
            call_count += 1
            return call_count > 1  # Return True after first check

        animation.stop_event.is_set = Mock(side_effect=mock_is_set)
        animation.stop_event.wait = Mock(return_value=False)

        animation.execute_animation()

        # Verify no LEDs were processed (for loop doesn't execute with 0 LEDs)
        mock_lights.set_color_rgb.assert_not_called()
        mock_lights.get_wheel_color.assert_not_called()

    def test_execute_animation_rainbow_with_custom_led_count(self, mock_lights):
        """Test rainbow mode with custom LED count."""
        mock_lights.num_led = 6
        animation = WheelFillAnimation(lights=mock_lights)

        # Mock stop_event to allow one complete fill
        animation.stop_event.wait = Mock(side_effect=[False] * 6 + [True])

        animation.execute_animation()

        # Verify 6 LEDs were processed
        assert mock_lights.set_color_rgb.call_count == 6
        assert mock_lights.get_wheel_color.call_count == 6

        # Verify wheel positions for 6 LEDs
        calls = mock_lights.get_wheel_color.call_args_list
        expected_positions = [int(256 / 6 * i) for i in range(6)]
        actual_positions = [call[0][0] for call in calls]
        assert actual_positions == expected_positions

    def test_execute_animation_single_color_with_none_color(self, mock_lights):
        """Test single color mode with None color (should not happen due to validation)."""
        # This test is for completeness, though the validation should prevent this
        # We need to bypass the validation by directly setting the attributes
        animation = WheelFillAnimation(
            lights=mock_lights, use_rainbow=True
        )  # Start with valid params
        animation.use_rainbow = False
        animation.color = None  # This would normally be caught by validation

        # Mock stop_event to allow one LED
        animation.stop_event.wait = Mock(side_effect=[False, True])

        animation.execute_animation()

        # Should use (0, 0, 0) as fallback
        assert mock_lights.set_color_rgb.call_count == 1
        call = mock_lights.set_color_rgb.call_args_list[0]
        assert call[1]["rgb_tuple"] == (0, 0, 0)

    def test_execute_animation_led_index_progression(
        self, animation_default, mock_lights
    ):
        """Test that LED indices progress correctly."""
        # Mock stop_event to allow one complete fill
        animation_default.stop_event.wait = Mock(side_effect=[False] * 12 + [True])

        animation_default.execute_animation()

        # Verify LED indices progress from 0 to 11
        calls = mock_lights.set_color_rgb.call_args_list
        for i, call in enumerate(calls):
            assert call[1]["led_index"] == i

    def test_execute_animation_fill_behavior(self, animation_default, mock_lights):
        """Test that LEDs are filled sequentially without clearing."""
        # Mock stop_event to allow one complete fill
        animation_default.stop_event.wait = Mock(side_effect=[False] * 12 + [True])

        animation_default.execute_animation()

        # Verify all LEDs were set
        assert mock_lights.set_color_rgb.call_count == 12

        # Verify each LED was set with the correct index
        calls = mock_lights.set_color_rgb.call_args_list
        for i, call in enumerate(calls):
            assert call[1]["led_index"] == i

    def test_execute_animation_rainbow_vs_single_color_difference(self, mock_lights):
        """Test the difference between rainbow and single color modes."""
        # Test rainbow mode
        animation_rainbow = WheelFillAnimation(lights=mock_lights)
        animation_rainbow.stop_event.wait = Mock(side_effect=[False] * 3 + [True])
        animation_rainbow.execute_animation()

        rainbow_calls = mock_lights.set_color_rgb.call_args_list
        rainbow_wheel_calls = mock_lights.get_wheel_color.call_args_list

        # Reset mocks
        mock_lights.reset_mock()

        # Test single color mode
        animation_single = WheelFillAnimation(
            lights=mock_lights, use_rainbow=False, color=ColorRGB.BLUE
        )
        animation_single.stop_event.wait = Mock(side_effect=[False] * 3 + [True])
        animation_single.execute_animation()

        single_calls = mock_lights.set_color_rgb.call_args_list
        single_wheel_calls = mock_lights.get_wheel_color.call_args_list

        # Verify differences
        assert len(rainbow_calls) == len(single_calls)  # Same number of LEDs
        assert len(rainbow_wheel_calls) > 0  # Rainbow mode calls get_wheel_color
        assert (
            len(single_wheel_calls) == 0
        )  # Single color mode doesn't call get_wheel_color

        # Verify single color mode uses the same color for all LEDs
        for call in single_calls:
            assert call[1]["rgb_tuple"] == ColorRGB.BLUE.rgb

    def test_execute_animation_interval_timing(self, animation_default):
        """Test that interval timing is respected."""
        delays = []

        def mock_wait(delay):
            delays.append(delay)
            return len(delays) > 3  # Stop after 3 delays

        animation_default.stop_event.wait = Mock(side_effect=mock_wait)

        animation_default.execute_animation()

        # Verify interval was used for each LED (4 delays due to while loop structure)
        assert len(delays) == 4
        assert all(delay == animation_default.interval for delay in delays)

    def test_execute_animation_different_intervals(self, mock_lights):
        """Test execute_animation with different intervals."""
        # Test with very fast interval
        animation_fast = WheelFillAnimation(lights=mock_lights, interval=0.01)

        delays = []

        def mock_wait(delay):
            delays.append(delay)
            return True  # Stop immediately

        animation_fast.stop_event.wait = Mock(side_effect=mock_wait)
        animation_fast.execute_animation()

        # Verify fast interval was used
        assert all(delay == 0.01 for delay in delays)

        # Test with very slow interval
        mock_lights.reset_mock()
        animation_slow = WheelFillAnimation(lights=mock_lights, interval=2.0)

        delays = []
        animation_slow.stop_event.wait = Mock(side_effect=mock_wait)
        animation_slow.execute_animation()

        # Verify slow interval was used
        assert all(delay == 2.0 for delay in delays)

    def test_attributes_after_init(self, animation_custom):
        """Test that all attributes are properly set after initialization."""
        assert animation_custom.use_rainbow is False
        assert animation_custom.color == ColorRGB.RED
        assert animation_custom.interval == 0.5
        assert hasattr(animation_custom, "lights")
        assert hasattr(animation_custom, "stop_event")

    def test_inheritance(self, animation_default):
        """Test that WheelFillAnimation inherits from Animation."""
        from hexapod.lights.animations.animation import Animation

        assert isinstance(animation_default, Animation)

    def test_override_decorator(self, animation_default):
        """Test that execute_animation has the @override decorator."""
        import inspect

        source = inspect.getsource(animation_default.execute_animation)
        assert "@override" in source

    def test_validation_error_message(self, mock_lights):
        """Test the exact validation error message."""
        with (
            patch("hexapod.lights.animations.wheel_fill_animation.Animation.__init__"),
            patch("hexapod.lights.animations.wheel_fill_animation.logger"),
        ):

            with pytest.raises(ValueError) as exc_info:
                WheelFillAnimation(lights=mock_lights, use_rainbow=False, color=None)

            assert (
                str(exc_info.value)
                == "color must be provided when use_rainbow is False."
            )

    def test_rainbow_mode_default_behavior(self, animation_default):
        """Test that rainbow mode is the default behavior."""
        assert animation_default.use_rainbow is True
        assert animation_default.color is None

    def test_single_color_mode_requires_color(self, mock_lights):
        """Test that single color mode requires a color to be provided."""
        with patch("hexapod.lights.animations.wheel_fill_animation.Animation.__init__"):
            # This should work
            animation = WheelFillAnimation(
                lights=mock_lights, use_rainbow=False, color=ColorRGB.RED
            )
            assert animation.use_rainbow is False
            assert animation.color == ColorRGB.RED

    def test_fill_animation_vs_wheel_animation_difference(self, mock_lights):
        """Test that WheelFillAnimation fills LEDs without clearing between them."""
        # WheelFillAnimation should not call clear between LEDs
        animation = WheelFillAnimation(lights=mock_lights)
        animation.stop_event.wait = Mock(side_effect=[False] * 3 + [True])
        animation.execute_animation()

        # Should not call clear (unlike WheelAnimation)
        mock_lights.clear.assert_not_called()

        # Should call set_color_rgb for each LED
        assert mock_lights.set_color_rgb.call_count == 3
