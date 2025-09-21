"""
Unit tests for PulseAnimation.
"""

import pytest
from unittest.mock import Mock, patch
from hexapod.lights.animations.pulse_animation import PulseAnimation
from hexapod.lights.lights import ColorRGB


@pytest.fixture
def mock_lights():
    """Mock Lights object."""
    mock_lights = Mock()
    mock_lights.num_led = 12
    mock_lights.set_color = Mock()
    return mock_lights


@pytest.fixture
def animation_default(mock_lights):
    """PulseAnimation with default parameters."""
    return PulseAnimation(lights=mock_lights)


@pytest.fixture
def animation_custom(mock_lights):
    """PulseAnimation with custom parameters."""
    return PulseAnimation(
        lights=mock_lights,
        base_color=ColorRGB.RED,
        pulse_color=ColorRGB.GREEN,
        pulse_speed=0.1,
    )


class TestPulseAnimation:
    """Test cases for PulseAnimation class."""

    def test_init_default_parameters(self, mock_lights):
        """Test initialization with default parameters."""
        with patch(
            "hexapod.lights.animations.pulse_animation.Animation.__init__"
        ) as mock_super_init:
            animation = PulseAnimation(lights=mock_lights)

            # Verify parent initialization
            mock_super_init.assert_called_once_with(mock_lights)

            # Verify default parameters
            assert animation.base_color == ColorRGB.BLUE
            assert animation.pulse_color == ColorRGB.RED
            assert animation.pulse_speed == 0.3

    def test_init_custom_parameters(self, mock_lights):
        """Test initialization with custom parameters."""
        with patch(
            "hexapod.lights.animations.pulse_animation.Animation.__init__"
        ) as mock_super_init:
            animation = PulseAnimation(
                lights=mock_lights,
                base_color=ColorRGB.RED,
                pulse_color=ColorRGB.GREEN,
                pulse_speed=0.1,
            )

            # Verify parent initialization
            mock_super_init.assert_called_once_with(mock_lights)

            # Verify custom parameters
            assert animation.base_color == ColorRGB.RED
            assert animation.pulse_color == ColorRGB.GREEN
            assert animation.pulse_speed == 0.1

    def test_execute_animation_single_pulse_cycle(self, animation_default, mock_lights):
        """Test execute_animation for a single pulse cycle."""
        # Mock stop_event to allow one complete pulse cycle
        call_count = 0

        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            # Allow base color, then pulse color, then stop
            return call_count > 2

        animation_default.stop_event.wait = Mock(side_effect=mock_wait)

        animation_default.execute_animation()

        # Verify both colors were set
        assert mock_lights.set_color.call_count == 2

        # Verify correct sequence: base color first, then pulse color
        calls = mock_lights.set_color.call_args_list
        assert calls[0][0][0] == ColorRGB.BLUE  # base color
        assert calls[1][0][0] == ColorRGB.RED  # pulse color

    def test_execute_animation_multiple_pulse_cycles(
        self, animation_default, mock_lights
    ):
        """Test execute_animation for multiple pulse cycles."""
        # Mock stop_event to allow multiple cycles
        call_count = 0

        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            # Allow 3 complete cycles (6 calls), then stop
            return call_count > 6

        animation_default.stop_event.wait = Mock(side_effect=mock_wait)

        animation_default.execute_animation()

        # Verify 3 complete cycles occurred
        assert mock_lights.set_color.call_count == 6

        # Verify alternating pattern
        calls = mock_lights.set_color.call_args_list
        for i, call in enumerate(calls):
            if i % 2 == 0:
                assert call[0][0] == ColorRGB.BLUE  # base color
            else:
                assert call[0][0] == ColorRGB.RED  # pulse color

    def test_execute_animation_stop_during_base_color(
        self, animation_default, mock_lights
    ):
        """Test stopping during base color phase."""
        # Mock stop_event to return True during base color phase
        animation_default.stop_event.wait = Mock(side_effect=[False, True])

        animation_default.execute_animation()

        # Verify only base color was set
        assert mock_lights.set_color.call_count == 1
        call = mock_lights.set_color.call_args_list[0]
        assert call[0][0] == ColorRGB.BLUE

    def test_execute_animation_stop_during_pulse_color(
        self, animation_default, mock_lights
    ):
        """Test stopping during pulse color phase."""
        # Mock stop_event to allow base color, then stop during pulse color
        animation_default.stop_event.wait = Mock(side_effect=[False, False, True])

        animation_default.execute_animation()

        # Verify both colors were set
        assert mock_lights.set_color.call_count == 2
        calls = mock_lights.set_color.call_args_list
        assert calls[0][0][0] == ColorRGB.BLUE  # base color
        assert calls[1][0][0] == ColorRGB.RED  # pulse color

    def test_execute_animation_stop_immediately(self, animation_default, mock_lights):
        """Test execute_animation when stopped immediately."""
        # Mock stop_event to return True immediately
        animation_default.stop_event.wait = Mock(return_value=True)

        animation_default.execute_animation()

        # Verify no LEDs were set
        mock_lights.set_color.assert_not_called()

    def test_execute_animation_custom_colors(self, animation_custom, mock_lights):
        """Test execute_animation with custom colors."""
        # Mock stop_event to allow one complete cycle
        animation_custom.stop_event.wait = Mock(side_effect=[False, False, True])

        animation_custom.execute_animation()

        # Verify custom colors were used
        assert mock_lights.set_color.call_count == 2
        calls = mock_lights.set_color.call_args_list
        assert calls[0][0][0] == ColorRGB.RED  # custom base color
        assert calls[1][0][0] == ColorRGB.GREEN  # custom pulse color

    def test_execute_animation_custom_pulse_speed(self, animation_custom):
        """Test that custom pulse speed is used."""
        delays = []

        def mock_wait(delay):
            delays.append(delay)
            return True  # Stop immediately

        animation_custom.stop_event.wait = Mock(side_effect=mock_wait)

        animation_custom.execute_animation()

        # Verify custom pulse speed was used
        assert all(delay == 0.1 for delay in delays)

    def test_execute_animation_continuous_pulsing(self, animation_default, mock_lights):
        """Test continuous pulsing without stopping."""
        # Mock stop_event to allow many cycles
        call_count = 0

        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            # Allow 10 complete cycles (20 calls), then stop
            return call_count > 20

        animation_default.stop_event.wait = Mock(side_effect=mock_wait)

        animation_default.execute_animation()

        # Verify 10 complete cycles occurred
        assert mock_lights.set_color.call_count == 20

        # Verify alternating pattern throughout
        calls = mock_lights.set_color.call_args_list
        for i, call in enumerate(calls):
            if i % 2 == 0:
                assert call[0][0] == ColorRGB.BLUE  # base color
            else:
                assert call[0][0] == ColorRGB.RED  # pulse color

    def test_execute_animation_same_colors(self, mock_lights):
        """Test execute_animation with same base and pulse colors."""
        animation = PulseAnimation(
            lights=mock_lights,
            base_color=ColorRGB.BLUE,
            pulse_color=ColorRGB.BLUE,
            pulse_speed=0.1,
        )

        # Mock stop_event to allow one complete cycle
        animation.stop_event.wait = Mock(side_effect=[False, False, True])

        animation.execute_animation()

        # Verify both calls used the same color
        assert mock_lights.set_color.call_count == 2
        calls = mock_lights.set_color.call_args_list
        assert calls[0][0][0] == ColorRGB.BLUE
        assert calls[1][0][0] == ColorRGB.BLUE

    def test_execute_animation_different_speeds(self, mock_lights):
        """Test execute_animation with different pulse speeds."""
        # Test with very fast pulse
        animation_fast = PulseAnimation(lights=mock_lights, pulse_speed=0.01)

        delays = []

        def mock_wait(delay):
            delays.append(delay)
            return True  # Stop immediately

        animation_fast.stop_event.wait = Mock(side_effect=mock_wait)
        animation_fast.execute_animation()

        # Verify fast speed was used
        assert all(delay == 0.01 for delay in delays)

        # Test with very slow pulse
        mock_lights.reset_mock()
        animation_slow = PulseAnimation(lights=mock_lights, pulse_speed=1.0)

        delays = []
        animation_slow.stop_event.wait = Mock(side_effect=mock_wait)
        animation_slow.execute_animation()

        # Verify slow speed was used
        assert all(delay == 1.0 for delay in delays)

    def test_execute_animation_zero_pulse_speed(self, mock_lights):
        """Test execute_animation with zero pulse speed."""
        animation = PulseAnimation(lights=mock_lights, pulse_speed=0.0)

        delays = []

        def mock_wait(delay):
            delays.append(delay)
            return True  # Stop immediately

        animation.stop_event.wait = Mock(side_effect=mock_wait)
        animation.execute_animation()

        # Verify zero speed was used
        assert all(delay == 0.0 for delay in delays)

    def test_execute_animation_negative_pulse_speed(self, mock_lights):
        """Test execute_animation with negative pulse speed."""
        animation = PulseAnimation(lights=mock_lights, pulse_speed=-0.1)

        delays = []

        def mock_wait(delay):
            delays.append(delay)
            return True  # Stop immediately

        animation.stop_event.wait = Mock(side_effect=mock_wait)
        animation.execute_animation()

        # Verify negative speed was used
        assert all(delay == -0.1 for delay in delays)

    def test_attributes_after_init(self, animation_custom):
        """Test that all attributes are properly set after initialization."""
        assert animation_custom.base_color == ColorRGB.RED
        assert animation_custom.pulse_color == ColorRGB.GREEN
        assert animation_custom.pulse_speed == 0.1
        assert hasattr(animation_custom, "lights")
        assert hasattr(animation_custom, "stop_event")

    def test_inheritance(self, animation_default):
        """Test that PulseAnimation inherits from Animation."""
        from hexapod.lights.animations.animation import Animation

        assert isinstance(animation_default, Animation)

    def test_override_decorator(self, animation_default):
        """Test that execute_animation has the @override decorator."""
        import inspect

        source = inspect.getsource(animation_default.execute_animation)
        assert "@override" in source

    def test_pulse_cycle_structure(self, animation_default, mock_lights):
        """Test the structure of a pulse cycle."""
        # Mock stop_event to allow exactly one cycle
        animation_default.stop_event.wait = Mock(side_effect=[False, False, True])

        animation_default.execute_animation()

        # Verify exactly 2 calls (base + pulse)
        assert mock_lights.set_color.call_count == 2

        # Verify the calls were made in the correct order
        calls = mock_lights.set_color.call_args_list
        assert calls[0][0][0] == animation_default.base_color
        assert calls[1][0][0] == animation_default.pulse_color

        # Verify both calls were made without led_index (all LEDs)
        for call in calls:
            assert call[1] == {}  # No keyword arguments

    def test_pulse_cycle_timing(self, animation_default):
        """Test that pulse cycle respects timing."""
        # Mock stop_event to track timing
        delays = []

        def mock_wait(delay):
            delays.append(delay)
            return len(delays) > 2  # Stop after 2 delays

        animation_default.stop_event.wait = Mock(side_effect=mock_wait)

        animation_default.execute_animation()

        # Verify both delays were the pulse_speed (3 delays due to while loop structure)
        assert len(delays) == 3
        assert all(delay == animation_default.pulse_speed for delay in delays)
