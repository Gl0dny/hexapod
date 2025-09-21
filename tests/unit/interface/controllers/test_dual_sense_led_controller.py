"""
Unit tests for dual_sense_led_controller.py module.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path

from hexapod.interface.controllers.gamepad_led_controllers.dual_sense_led_controller import (
    DualSenseLEDController,
)


class TestDualSenseLEDController:
    """Test cases for DualSenseLEDController class."""

    @pytest.fixture
    def controller(self):
        """Create a DualSenseLEDController instance for testing."""
        return DualSenseLEDController()

    @patch("dualsense_controller.DualSenseController")
    def test_init_success(self, mock_dualsense_class):
        """Test successful initialization."""
        mock_controller = Mock()
        mock_controller.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]
        mock_dualsense_class.return_value = mock_controller
        mock_dualsense_class.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]

        controller = DualSenseLEDController()

        assert controller.DualSenseController == mock_dualsense_class
        assert controller.dualsense_controller == mock_controller
        assert controller.is_connected is True

    def test_init_import_error(self):
        """Test initialization when DualSenseController import fails."""
        # Since dualsense_controller is mocked in conftest.py, we can't easily test the import error
        # This test verifies the fallback behavior when DualSenseController is None
        with patch("dualsense_controller.DualSenseController", None):
            controller = DualSenseLEDController()

            assert controller.DualSenseController is None
            assert controller.dualsense_controller is None
            assert controller.is_connected is False

    @patch("dualsense_controller.DualSenseController")
    def test_connect_controller_success(self, mock_dualsense_class):
        """Test successful controller connection."""
        mock_controller = Mock()
        mock_controller.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]
        mock_dualsense_class.return_value = mock_controller
        mock_dualsense_class.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]

        controller = DualSenseLEDController()

        assert controller.is_connected is True
        # The methods are called during initialization, so we check they were called
        assert mock_controller._core.init.call_count >= 1
        assert mock_controller._properties.microphone.set_muted.call_count >= 1
        assert mock_controller.wait_until_updated.call_count >= 1

    @patch("dualsense_controller.DualSenseController")
    def test_connect_controller_no_devices(self, mock_dualsense_class, caplog):
        """Test controller connection when no devices are available."""
        mock_dualsense_class.enumerate_devices.return_value = []

        controller = DualSenseLEDController()

        assert controller._connect_controller() is False
        assert controller.is_connected is False
        assert "No DualSense devices found" in caplog.text

    @patch("dualsense_controller.DualSenseController")
    def test_connect_controller_exception(self, mock_dualsense_class, caplog):
        """Test controller connection when exception occurs."""
        mock_dualsense_class.enumerate_devices.side_effect = Exception(
            "Connection failed"
        )

        controller = DualSenseLEDController()

        assert controller._connect_controller() is False
        assert controller.is_connected is False
        assert (
            "Failed to connect to DualSense controller: Connection failed"
            in caplog.text
        )
        assert (
            "Make sure the controller is connected via USB or Bluetooth" in caplog.text
        )

    @patch("dualsense_controller.DualSenseController")
    def test_connect_controller_none_class(self, mock_dualsense_class):
        """Test controller connection when DualSenseController class is None."""
        controller = DualSenseLEDController()
        controller.DualSenseController = None

        result = controller._connect_controller()

        assert result is False

    @patch("dualsense_controller.DualSenseController")
    def test_set_color_internal_success(self, mock_dualsense_class):
        """Test successful color setting."""
        mock_controller = Mock()
        mock_controller.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]
        mock_dualsense_class.return_value = mock_controller
        mock_dualsense_class.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]

        controller = DualSenseLEDController()

        # Reset the mock to ignore the call during initialization
        mock_controller.lightbar.set_color.reset_mock()

        result = controller._set_color_internal(255, 0, 0)

        assert result is True
        mock_controller.lightbar.set_color.assert_called_once_with(255, 0, 0)

    @patch("dualsense_controller.DualSenseController")
    def test_set_color_internal_no_controller(self, mock_dualsense_class):
        """Test color setting when no controller is available."""
        mock_controller = Mock()
        mock_controller.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]
        mock_dualsense_class.return_value = mock_controller
        mock_dualsense_class.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]

        controller = DualSenseLEDController()
        controller.dualsense_controller = None

        result = controller._set_color_internal(255, 0, 0)

        assert result is False

    @patch("dualsense_controller.DualSenseController")
    def test_set_color_internal_exception(self, mock_dualsense_class, caplog):
        """Test color setting when exception occurs."""
        mock_controller = Mock()
        mock_controller.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]
        mock_controller.lightbar.set_color.side_effect = Exception(
            "Color setting failed"
        )
        mock_dualsense_class.return_value = mock_controller
        mock_dualsense_class.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]

        controller = DualSenseLEDController()

        result = controller._set_color_internal(255, 0, 0)

        assert result is False
        assert "Failed to set DualSense LED color: Color setting failed" in caplog.text

    @patch("dualsense_controller.DualSenseController")
    def test_cleanup_internal_success(self, mock_dualsense_class):
        """Test successful cleanup."""
        mock_controller = Mock()
        mock_controller.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]
        mock_dualsense_class.return_value = mock_controller
        mock_dualsense_class.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]

        controller = DualSenseLEDController()

        controller._cleanup_internal()

        mock_controller.deactivate.assert_called_once()

    @patch("dualsense_controller.DualSenseController")
    def test_cleanup_internal_no_controller(self, mock_dualsense_class):
        """Test cleanup when no controller is available."""
        mock_controller = Mock()
        mock_controller.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]
        mock_dualsense_class.return_value = mock_controller
        mock_dualsense_class.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]

        controller = DualSenseLEDController()
        controller.dualsense_controller = None

        # Should not raise exception
        controller._cleanup_internal()

    @patch("dualsense_controller.DualSenseController")
    def test_cleanup_internal_exception(self, mock_dualsense_class, caplog):
        """Test cleanup when exception occurs."""
        mock_controller = Mock()
        mock_controller.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]
        mock_controller.deactivate.side_effect = Exception("Deactivation failed")
        mock_dualsense_class.return_value = mock_controller
        mock_dualsense_class.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]

        controller = DualSenseLEDController()

        controller._cleanup_internal()

        assert (
            "Error deactivating DualSense controller: Deactivation failed"
            in caplog.text
        )

    @patch("dualsense_controller.DualSenseController")
    def test_inheritance(self, mock_dualsense_class):
        """Test that DualSenseLEDController inherits from BaseGamepadLEDController."""
        from hexapod.interface.controllers.gamepad_led_controllers.gamepad_led_controller import (
            BaseGamepadLEDController,
        )

        controller = DualSenseLEDController()

        assert isinstance(controller, BaseGamepadLEDController)

    @patch("dualsense_controller.DualSenseController")
    def test_controller_initialization_parameters(self, mock_dualsense_class):
        """Test that DualSenseController is initialized with correct parameters."""
        mock_controller = Mock()
        mock_controller.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]
        mock_dualsense_class.return_value = mock_controller
        mock_dualsense_class.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]

        DualSenseLEDController()

        mock_dualsense_class.assert_called_once_with(
            microphone_invert_led=True, microphone_initially_muted=True
        )

    @patch("dualsense_controller.DualSenseController")
    def test_controller_activation_sequence(self, mock_dualsense_class):
        """Test the sequence of controller activation calls."""
        mock_controller = Mock()
        mock_controller.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]
        mock_dualsense_class.return_value = mock_controller
        mock_dualsense_class.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]

        controller = DualSenseLEDController()

        # Verify the sequence of calls
        mock_controller._core.init.assert_called_once()
        mock_controller._properties.microphone.set_muted.assert_called_once()
        mock_controller.wait_until_updated.assert_called_once()

    @patch("dualsense_controller.DualSenseController")
    def test_initial_color_setting(self, mock_dualsense_class):
        """Test that initial color is set after connection."""
        mock_controller = Mock()
        mock_controller.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]
        mock_dualsense_class.return_value = mock_controller
        mock_dualsense_class.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]

        controller = DualSenseLEDController()

        # Should have called set_color with the default color (BLUE)
        mock_controller.lightbar.set_color.assert_called_with(0, 0, 255)

    @patch("dualsense_controller.DualSenseController")
    def test_controller_properties_access(self, mock_dualsense_class):
        """Test that controller properties are accessed correctly."""
        mock_controller = Mock()
        mock_controller.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]
        mock_dualsense_class.return_value = mock_controller
        mock_dualsense_class.enumerate_devices.return_value = [
            {"name": "DualSense Controller"}
        ]

        controller = DualSenseLEDController()

        # Test that we can access the controller's properties
        assert hasattr(controller.dualsense_controller, "_core")
        assert hasattr(controller.dualsense_controller, "_properties")
        assert hasattr(controller.dualsense_controller, "lightbar")
        assert hasattr(controller.dualsense_controller, "deactivate")

    @patch("dualsense_controller.DualSenseController")
    def test_multiple_device_handling(self, mock_dualsense_class):
        """Test handling when multiple devices are available."""
        mock_controller = Mock()
        mock_controller.enumerate_devices.return_value = [
            {"name": "DualSense Controller 1"},
            {"name": "DualSense Controller 2"},
        ]
        mock_dualsense_class.return_value = mock_controller
        mock_dualsense_class.enumerate_devices.return_value = [
            {"name": "DualSense Controller 1"},
            {"name": "DualSense Controller 2"},
        ]

        controller = DualSenseLEDController()

        assert controller._connect_controller() is True
        assert controller.is_connected is True

    @patch("dualsense_controller.DualSenseController")
    def test_controller_connection_failure_recovery(self, mock_dualsense_class, caplog):
        """Test recovery from controller connection failure."""
        # First call fails, second call succeeds
        mock_dualsense_class.enumerate_devices.side_effect = [
            [],  # No devices first time
            [{"name": "DualSense Controller"}],  # Device available second time
        ]

        controller = DualSenseLEDController()

        # The first connection attempt during initialization should fail
        assert controller.is_connected is False
        assert "No DualSense devices found" in caplog.text

        # Second connection attempt should succeed
        result = controller._connect_controller()
        assert result is True
        assert controller.is_connected is True
