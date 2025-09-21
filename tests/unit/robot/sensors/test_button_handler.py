"""
Unit tests for button handler system.
"""

import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from hexapod.robot.sensors.button_handler import ButtonHandler


class TestButtonHandler:
    """Test cases for ButtonHandler class."""

    @pytest.fixture
    def mock_gpio(self):
        """Mock RPi.GPIO module."""
        with patch("hexapod.robot.sensors.button_handler.GPIO") as mock_gpio:
            mock_gpio.LOW = 0
            mock_gpio.HIGH = 1
            mock_gpio.BCM = 0
            mock_gpio.IN = 0
            mock_gpio.PUD_UP = 0
            mock_gpio.input = Mock(return_value=1)  # Default to not pressed
            mock_gpio.setmode = Mock()
            mock_gpio.setup = Mock()
            mock_gpio.cleanup = Mock()
            yield mock_gpio

    @pytest.fixture
    def button_handler_default(self, mock_gpio):
        """Create ButtonHandler with default parameters."""
        return ButtonHandler()

    @pytest.fixture
    def button_handler_custom(self, mock_gpio):
        """Create ButtonHandler with custom parameters."""
        event = threading.Event()
        return ButtonHandler(
            pin=18, long_press_time=2.0, external_control_paused_event=event
        )

    def test_init_default_parameters(self, button_handler_default):
        """Test ButtonHandler initialization with default parameters."""
        assert button_handler_default.pin == 26
        assert button_handler_default.is_running is True
        assert button_handler_default.long_press_time == 3.0
        assert button_handler_default.press_start_time == 0
        assert button_handler_default.is_pressed is False
        assert button_handler_default.long_press_detected is False
        assert button_handler_default.external_control_paused_event is None

    def test_init_custom_parameters(self, button_handler_custom):
        """Test ButtonHandler initialization with custom parameters."""
        assert button_handler_custom.pin == 18
        assert button_handler_custom.is_running is True
        assert button_handler_custom.long_press_time == 2.0
        assert button_handler_custom.press_start_time == 0
        assert button_handler_custom.is_pressed is False
        assert button_handler_custom.long_press_detected is False
        assert button_handler_custom.external_control_paused_event is not None

    def test_gpio_setup(self, mock_gpio):
        """Test GPIO setup during initialization."""
        ButtonHandler(pin=15, long_press_time=1.5)

        mock_gpio.setmode.assert_called_once_with(mock_gpio.BCM)
        mock_gpio.setup.assert_called_once_with(
            15, mock_gpio.IN, pull_up_down=mock_gpio.PUD_UP
        )

    def test_get_state_pressed(self, button_handler_default, mock_gpio):
        """Test get_state when button is pressed."""
        mock_gpio.input.return_value = 0  # Button pressed (LOW)

        result = button_handler_default.get_state()

        assert result is True
        mock_gpio.input.assert_called_once_with(26)

    def test_get_state_not_pressed(self, button_handler_default, mock_gpio):
        """Test get_state when button is not pressed."""
        mock_gpio.input.return_value = 1  # Button not pressed (HIGH)

        result = button_handler_default.get_state()

        assert result is False
        mock_gpio.input.assert_called_once_with(26)

    def test_toggle_state_from_running_to_stopped(self, button_handler_default):
        """Test toggle_state from running to stopped."""
        assert button_handler_default.is_running is True

        result = button_handler_default.toggle_state()

        assert result is False
        assert button_handler_default.is_running is False

    def test_toggle_state_from_stopped_to_running(self, button_handler_default):
        """Test toggle_state from stopped to running."""
        button_handler_default.is_running = False

        result = button_handler_default.toggle_state()

        assert result is True
        assert button_handler_default.is_running is True

    def test_check_button_no_action(self, button_handler_default, mock_gpio):
        """Test check_button when no action occurs."""
        mock_gpio.input.return_value = 1  # Button not pressed

        action, is_running = button_handler_default.check_button()

        assert action is None
        assert is_running is True

    def test_check_button_short_press_toggle(self, button_handler_default, mock_gpio):
        """Test check_button for short press toggle."""
        # Simulate button press and release
        mock_gpio.input.side_effect = [0, 1]  # Pressed then released

        # First call - button pressed
        action, is_running = button_handler_default.check_button()
        assert action is None
        assert is_running is True
        assert button_handler_default.is_pressed is True

        # Second call - button released
        action, is_running = button_handler_default.check_button()
        assert action == "toggle"
        assert is_running is False  # Should be toggled
        assert button_handler_default.is_pressed is False

    def test_check_button_long_press(self, button_handler_default, mock_gpio):
        """Test check_button for long press."""
        # Simulate long press
        mock_gpio.input.return_value = 0  # Button pressed

        # Mock time to simulate long press
        with patch("hexapod.robot.sensors.button_handler.time.time") as mock_time:
            mock_time.side_effect = [0, 4.0]  # Start time, then 4 seconds later

            # First call - button pressed
            action, is_running = button_handler_default.check_button()
            assert action is None
            assert button_handler_default.is_pressed is True

            # Second call - long press detected
            action, is_running = button_handler_default.check_button()
            assert action == "long_press"
            assert is_running is True
            assert button_handler_default.long_press_detected is True

    def test_check_button_long_press_with_external_control_paused(
        self, button_handler_custom, mock_gpio
    ):
        """Test long press when external control is paused."""
        button_handler_custom.external_control_paused_event.set()
        mock_gpio.input.return_value = 0  # Button pressed

        with patch("hexapod.robot.sensors.button_handler.time.time") as mock_time:
            mock_time.side_effect = [0, 4.0]  # Start time, then 4 seconds later

            # First call - button pressed
            action, is_running = button_handler_custom.check_button()
            assert action is None
            assert button_handler_custom.is_pressed is True

            # Second call - long press detected but external control is paused
            action, is_running = button_handler_custom.check_button()
            assert action is None  # Should not return long_press
            assert is_running is True

    def test_check_button_short_press_stop_task(self, button_handler_custom, mock_gpio):
        """Test short press when external control is paused (stop_task)."""
        button_handler_custom.external_control_paused_event.set()
        mock_gpio.input.side_effect = [0, 1]  # Pressed then released

        # First call - button pressed
        action, is_running = button_handler_custom.check_button()
        assert action is None
        assert button_handler_custom.is_pressed is True

        # Second call - button released, should return stop_task
        action, is_running = button_handler_custom.check_button()
        assert action == "stop_task"
        assert is_running is True

    def test_check_button_long_press_then_release(
        self, button_handler_default, mock_gpio
    ):
        """Test button release after long press."""
        mock_gpio.input.side_effect = [0, 0, 1]  # Pressed, still pressed, released

        with patch("hexapod.robot.sensors.button_handler.time.time") as mock_time:
            mock_time.side_effect = [0, 4.0, 4.1]  # Start, long press, release

            # First call - button pressed
            action, is_running = button_handler_default.check_button()
            assert action is None

            # Second call - long press detected
            action, is_running = button_handler_default.check_button()
            assert action == "long_press"
            assert button_handler_default.long_press_detected is True

            # Third call - button released
            action, is_running = button_handler_default.check_button()
            assert action is None  # Should not return toggle after long press
            assert button_handler_default.is_pressed is False
            assert button_handler_default.long_press_detected is False

    def test_check_button_multiple_presses(self, button_handler_default, mock_gpio):
        """Test multiple button press cycles."""
        mock_gpio.input.side_effect = [0, 1, 0, 1]  # Press, release, press, release

        # First press-release cycle
        action, is_running = button_handler_default.check_button()  # Press
        assert action is None
        action, is_running = button_handler_default.check_button()  # Release
        assert action == "toggle"
        assert is_running is False

        # Second press-release cycle
        action, is_running = button_handler_default.check_button()  # Press
        assert action is None
        action, is_running = button_handler_default.check_button()  # Release
        assert action == "toggle"
        assert is_running is True

    def test_cleanup(self, button_handler_default, mock_gpio):
        """Test cleanup method."""
        button_handler_default.cleanup()

        mock_gpio.cleanup.assert_called_once_with(26)

    def test_cleanup_custom_pin(self, button_handler_custom, mock_gpio):
        """Test cleanup with custom pin."""
        button_handler_custom.cleanup()

        mock_gpio.cleanup.assert_called_once_with(18)

    def test_external_control_paused_event_none(
        self, button_handler_default, mock_gpio
    ):
        """Test behavior when external_control_paused_event is None."""
        mock_gpio.input.side_effect = [0, 1]  # Pressed then released

        # First call - button pressed
        action, is_running = button_handler_default.check_button()
        assert action is None

        # Second call - button released, should return toggle
        action, is_running = button_handler_default.check_button()
        assert action == "toggle"
        assert is_running is False

    def test_external_control_paused_event_not_set(
        self, button_handler_custom, mock_gpio
    ):
        """Test behavior when external_control_paused_event is not set."""
        # Don't set the event
        mock_gpio.input.side_effect = [0, 1]  # Pressed then released

        # First call - button pressed
        action, is_running = button_handler_custom.check_button()
        assert action is None

        # Second call - button released, should return toggle
        action, is_running = button_handler_custom.check_button()
        assert action == "toggle"
        assert is_running is False

    def test_long_press_time_custom(self, button_handler_custom, mock_gpio):
        """Test custom long press time."""
        mock_gpio.input.return_value = 0  # Button pressed

        with patch("hexapod.robot.sensors.button_handler.time.time") as mock_time:
            mock_time.side_effect = [
                0,
                1.5,
                2.5,
            ]  # Start, before threshold, after threshold

            # First call - button pressed
            action, is_running = button_handler_custom.check_button()
            assert action is None

            # Second call - before long press threshold
            action, is_running = button_handler_custom.check_button()
            assert action is None

            # Third call - after long press threshold
            action, is_running = button_handler_custom.check_button()
            assert action == "long_press"

    def test_press_state_tracking(self, button_handler_default, mock_gpio):
        """Test that press state is properly tracked."""
        mock_gpio.input.return_value = 0  # Button pressed

        # First call - should set is_pressed to True
        action, is_running = button_handler_default.check_button()
        assert button_handler_default.is_pressed is True
        assert button_handler_default.press_start_time > 0

        # Second call - should not change is_pressed
        action, is_running = button_handler_default.check_button()
        assert button_handler_default.is_pressed is True

    def test_release_state_reset(self, button_handler_default, mock_gpio):
        """Test that release properly resets state."""
        mock_gpio.input.side_effect = [0, 1]  # Pressed then released

        # Press
        button_handler_default.check_button()
        assert button_handler_default.is_pressed is True

        # Release
        action, is_running = button_handler_default.check_button()
        assert button_handler_default.is_pressed is False
        assert button_handler_default.long_press_detected is False

    def test_threading_lock_usage(self, button_handler_default):
        """Test that threading lock is properly used in toggle_state."""
        original_lock = button_handler_default.lock

        result = button_handler_default.toggle_state()

        # Verify the lock is still the same object (not replaced)
        assert button_handler_default.lock is original_lock
        assert result is False

    def test_initialization_values(self, button_handler_default):
        """Test all initialization values."""
        assert button_handler_default.press_start_time == 0
        assert button_handler_default.long_press_detected is False
        assert button_handler_default.is_pressed is False
        assert button_handler_default.is_running is True
        assert button_handler_default.pin == 26
        assert button_handler_default.long_press_time == 3.0
