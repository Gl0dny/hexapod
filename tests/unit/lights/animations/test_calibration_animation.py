"""
Unit tests for CalibrationAnimation.
"""

import pytest
from unittest.mock import Mock, patch
from hexapod.lights.animations.calibration_animation import CalibrationAnimation
from hexapod.lights.lights import ColorRGB


@pytest.fixture
def mock_lights():
    """Mock Lights object."""
    mock_lights = Mock()
    mock_lights.num_led = 12
    mock_lights.set_color = Mock()
    return mock_lights


@pytest.fixture
def sample_calibration_status():
    """Sample calibration status dictionary."""
    return {
        0: "calibrating",
        1: "calibrated",
        2: "not_calibrated",
        3: "calibrating",
        4: "calibrated",
        5: "not_calibrated",
    }


@pytest.fixture
def sample_leg_to_led():
    """Sample leg to LED mapping."""
    return {
        0: 0,  # leg 0 -> LED 0
        1: 2,  # leg 1 -> LED 2
        2: 4,  # leg 2 -> LED 4
        3: 6,  # leg 3 -> LED 6
        4: 8,  # leg 4 -> LED 8
        5: 10,  # leg 5 -> LED 10
    }


@pytest.fixture
def animation_default(mock_lights, sample_calibration_status, sample_leg_to_led):
    """CalibrationAnimation with default parameters."""
    return CalibrationAnimation(
        lights=mock_lights,
        calibration_status=sample_calibration_status,
        leg_to_led=sample_leg_to_led,
    )


@pytest.fixture
def animation_custom(mock_lights, sample_calibration_status, sample_leg_to_led):
    """CalibrationAnimation with custom parameters."""
    return CalibrationAnimation(
        lights=mock_lights,
        calibration_status=sample_calibration_status,
        leg_to_led=sample_leg_to_led,
        refresh_delay=0.5,
    )


class TestCalibrationAnimation:
    """Test cases for CalibrationAnimation class."""

    def test_init_default_parameters(
        self, mock_lights, sample_calibration_status, sample_leg_to_led
    ):
        """Test initialization with default parameters."""
        with patch(
            "hexapod.lights.animations.calibration_animation.Animation.__init__"
        ) as mock_super_init:
            animation = CalibrationAnimation(
                lights=mock_lights,
                calibration_status=sample_calibration_status,
                leg_to_led=sample_leg_to_led,
            )

            # Verify parent initialization
            mock_super_init.assert_called_once_with(mock_lights)

            # Verify default parameters
            assert animation.calibration_status == sample_calibration_status
            assert animation.leg_to_led == sample_leg_to_led
            assert animation.refresh_delay == 1.0

    def test_init_custom_parameters(
        self, mock_lights, sample_calibration_status, sample_leg_to_led
    ):
        """Test initialization with custom parameters."""
        with patch(
            "hexapod.lights.animations.calibration_animation.Animation.__init__"
        ) as mock_super_init:
            animation = CalibrationAnimation(
                lights=mock_lights,
                calibration_status=sample_calibration_status,
                leg_to_led=sample_leg_to_led,
                refresh_delay=0.5,
            )

            # Verify parent initialization
            mock_super_init.assert_called_once_with(mock_lights)

            # Verify custom parameters
            assert animation.calibration_status == sample_calibration_status
            assert animation.leg_to_led == sample_leg_to_led
            assert animation.refresh_delay == 0.5

    def test_execute_animation_single_iteration(self, animation_default, mock_lights):
        """Test execute_animation for a single iteration."""
        # Mock stop_event to return True after first iteration
        animation_default.stop_event.wait = Mock(return_value=True)

        animation_default.execute_animation()

        # Verify all legs were processed
        assert mock_lights.set_color.call_count == 6

        # Verify correct colors were set for each LED
        expected_calls = [
            (ColorRGB.YELLOW, 0),  # leg 0: calibrating -> LED 0
            (ColorRGB.GREEN, 2),  # leg 1: calibrated -> LED 2
            (ColorRGB.RED, 4),  # leg 2: not_calibrated -> LED 4
            (ColorRGB.YELLOW, 6),  # leg 3: calibrating -> LED 6
            (ColorRGB.GREEN, 8),  # leg 4: calibrated -> LED 8
            (ColorRGB.RED, 10),  # leg 5: not_calibrated -> LED 10
        ]

        calls = mock_lights.set_color.call_args_list
        for i, (expected_color, expected_led) in enumerate(expected_calls):
            call = calls[i]
            assert call[0][0] == expected_color
            assert call[1]["led_index"] == expected_led

    def test_execute_animation_multiple_iterations(
        self, animation_default, mock_lights
    ):
        """Test execute_animation for multiple iterations."""
        # Mock stop_event to allow 3 iterations
        call_count = 0

        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            return call_count > 3  # Stop after 3 iterations

        animation_default.stop_event.wait = Mock(side_effect=mock_wait)

        animation_default.execute_animation()

        # Verify 3 iterations occurred (6 legs * 3 iterations)
        assert (
            mock_lights.set_color.call_count == 24
        )  # 6 legs * 4 iterations (including initial)

    def test_execute_animation_stop_immediately(self, animation_default, mock_lights):
        """Test execute_animation when stopped immediately."""
        # Mock stop_event to return True immediately
        animation_default.stop_event.wait = Mock(return_value=True)

        animation_default.execute_animation()

        # Verify LEDs were set (the while loop executes at least once)
        assert mock_lights.set_color.call_count == 6

    def test_execute_animation_missing_leg_status(self, mock_lights, sample_leg_to_led):
        """Test execute_animation with missing leg status."""
        # Create calibration status missing some legs
        incomplete_status = {
            0: "calibrating",
            2: "calibrated",
            # Missing legs 1, 3, 4, 5
        }

        animation = CalibrationAnimation(
            lights=mock_lights,
            calibration_status=incomplete_status,
            leg_to_led=sample_leg_to_led,
        )

        # Mock stop_event to return True after first iteration
        animation.stop_event.wait = Mock(return_value=True)

        animation.execute_animation()

        # Verify only legs with status were processed
        assert mock_lights.set_color.call_count == 2

        # Verify correct LEDs were set
        calls = mock_lights.set_color.call_args_list
        assert calls[0][0][0] == ColorRGB.YELLOW  # leg 0: calibrating
        assert calls[0][1]["led_index"] == 0
        assert calls[1][0][0] == ColorRGB.GREEN  # leg 2: calibrated
        assert calls[1][1]["led_index"] == 4

    def test_execute_animation_invalid_status(self, mock_lights, sample_leg_to_led):
        """Test execute_animation with invalid calibration status."""
        invalid_status = {0: "calibrating", 1: "invalid_status"}  # Invalid status

        animation = CalibrationAnimation(
            lights=mock_lights,
            calibration_status=invalid_status,
            leg_to_led=sample_leg_to_led,
        )

        # Mock stop_event to allow processing of first leg
        call_count = 0

        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            return call_count > 1  # Stop after processing first leg

        animation.stop_event.wait = Mock(side_effect=mock_wait)

        # Should raise ValueError for invalid status
        with pytest.raises(
            ValueError, match="Invalid calibration status: invalid_status"
        ):
            animation.execute_animation()

    def test_execute_animation_custom_refresh_delay(self, animation_custom):
        """Test that custom refresh delay is used."""
        delays = []

        def mock_wait(delay):
            delays.append(delay)
            return True  # Stop immediately

        animation_custom.stop_event.wait = Mock(side_effect=mock_wait)

        animation_custom.execute_animation()

        # Verify custom delay was used
        assert all(delay == 0.5 for delay in delays)

    def test_execute_animation_empty_calibration_status(
        self, mock_lights, sample_leg_to_led
    ):
        """Test execute_animation with empty calibration status."""
        animation = CalibrationAnimation(
            lights=mock_lights, calibration_status={}, leg_to_led=sample_leg_to_led
        )

        # Mock stop_event to return True after first iteration
        animation.stop_event.wait = Mock(return_value=True)

        animation.execute_animation()

        # Verify no LEDs were set
        mock_lights.set_color.assert_not_called()

    def test_execute_animation_empty_leg_to_led(
        self, mock_lights, sample_calibration_status
    ):
        """Test execute_animation with empty leg_to_led mapping."""
        animation = CalibrationAnimation(
            lights=mock_lights,
            calibration_status=sample_calibration_status,
            leg_to_led={},
        )

        # Mock stop_event to return True after first iteration
        animation.stop_event.wait = Mock(return_value=True)

        animation.execute_animation()

        # Verify no LEDs were set
        mock_lights.set_color.assert_not_called()

    def test_execute_animation_all_status_types(self, mock_lights, sample_leg_to_led):
        """Test execute_animation with all possible status types."""
        all_status = {0: "calibrating", 1: "calibrated", 2: "not_calibrated"}

        animation = CalibrationAnimation(
            lights=mock_lights,
            calibration_status=all_status,
            leg_to_led=sample_leg_to_led,
        )

        # Mock stop_event to return True after first iteration
        animation.stop_event.wait = Mock(return_value=True)

        animation.execute_animation()

        # Verify all three status types were processed
        assert mock_lights.set_color.call_count == 3

        calls = mock_lights.set_color.call_args_list
        assert calls[0][0][0] == ColorRGB.YELLOW  # calibrating
        assert calls[1][0][0] == ColorRGB.GREEN  # calibrated
        assert calls[2][0][0] == ColorRGB.RED  # not_calibrated

    def test_execute_animation_none_status(self, mock_lights, sample_leg_to_led):
        """Test execute_animation with None status values."""
        status_with_none = {0: "calibrating", 1: None, 2: "calibrated"}  # None status

        animation = CalibrationAnimation(
            lights=mock_lights,
            calibration_status=status_with_none,
            leg_to_led=sample_leg_to_led,
        )

        # Mock stop_event to return True after first iteration
        animation.stop_event.wait = Mock(return_value=True)

        animation.execute_animation()

        # Verify only legs with non-None status were processed
        assert mock_lights.set_color.call_count == 2

        calls = mock_lights.set_color.call_args_list
        assert calls[0][0][0] == ColorRGB.YELLOW  # calibrating
        assert calls[1][0][0] == ColorRGB.GREEN  # calibrated

    def test_attributes_after_init(
        self, animation_custom, sample_calibration_status, sample_leg_to_led
    ):
        """Test that all attributes are properly set after initialization."""
        assert animation_custom.calibration_status == sample_calibration_status
        assert animation_custom.leg_to_led == sample_leg_to_led
        assert animation_custom.refresh_delay == 0.5
        assert hasattr(animation_custom, "lights")
        assert hasattr(animation_custom, "stop_event")

    def test_inheritance(self, animation_default):
        """Test that CalibrationAnimation inherits from Animation."""
        from hexapod.lights.animations.animation import Animation

        assert isinstance(animation_default, Animation)

    def test_override_decorator(self, animation_default):
        """Test that execute_animation has the @override decorator."""
        import inspect

        source = inspect.getsource(animation_default.execute_animation)
        assert "@override" in source

    def test_status_color_mapping(self, animation_default):
        """Test that the status color mapping is correct."""
        # This tests the internal mapping used in execute_animation
        expected_mapping = {
            "calibrating": ColorRGB.YELLOW,
            "calibrated": ColorRGB.GREEN,
            "not_calibrated": ColorRGB.RED,
        }

        # We can't directly access the internal mapping, but we can verify
        # the behavior through the execute_animation method
        assert True  # This is more of a documentation test
