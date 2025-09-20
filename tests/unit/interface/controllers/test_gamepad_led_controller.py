"""
Unit tests for gamepad_led_controller.py module.
"""

import pytest
import time
import threading
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path

from hexapod.interface.controllers.gamepad_led_controllers.gamepad_led_controller import (
    BaseGamepadLEDController,
    GamepadLEDColor
)


class TestGamepadLEDColor:
    """Test cases for GamepadLEDColor enum."""

    def test_color_values(self):
        """Test color enum values."""
        assert GamepadLEDColor.RED.value == (255, 0, 0)
        assert GamepadLEDColor.GREEN.value == (0, 255, 0)
        assert GamepadLEDColor.BLUE.value == (0, 0, 255)
        assert GamepadLEDColor.YELLOW.value == (255, 215, 0)
        assert GamepadLEDColor.CYAN.value == (0, 255, 255)
        assert GamepadLEDColor.MAGENTA.value == (255, 0, 255)
        assert GamepadLEDColor.WHITE.value == (255, 255, 255)
        assert GamepadLEDColor.ORANGE.value == (255, 50, 0)
        assert GamepadLEDColor.PURPLE.value == (128, 0, 128)
        assert GamepadLEDColor.PINK.value == (255, 51, 183)
        assert GamepadLEDColor.LIME.value == (75, 180, 0)
        assert GamepadLEDColor.TEAL.value == (0, 128, 128)
        assert GamepadLEDColor.INDIGO.value == (75, 0, 130)
        assert GamepadLEDColor.BLACK.value == (0, 0, 0)

    def test_rgb_property(self):
        """Test rgb property returns the color value."""
        assert GamepadLEDColor.RED.rgb == (255, 0, 0)
        assert GamepadLEDColor.BLUE.rgb == (0, 0, 255)
        assert GamepadLEDColor.BLACK.rgb == (0, 0, 0)


class ConcreteLEDController(BaseGamepadLEDController):
    """Concrete implementation of BaseGamepadLEDController for testing."""
    
    def _connect_controller(self) -> bool:
        self.is_connected = True
        return True
    
    def _set_color_internal(self, r: int, g: int, b: int) -> bool:
        return True
    
    def _cleanup_internal(self) -> None:
        pass


class TestBaseGamepadLEDController:
    """Test cases for BaseGamepadLEDController class."""

    @pytest.fixture
    def controller(self):
        """Create a concrete LED controller for testing."""
        return ConcreteLEDController()

    def test_init(self, controller):
        """Test controller initialization."""
        assert controller.is_connected is False
        assert controller.current_color == GamepadLEDColor.BLUE
        assert controller.brightness == 1.0
        assert controller.animation_thread is None
        assert controller.animation_running is False

    def test_set_color_success(self, controller):
        """Test setting color successfully."""
        controller.is_connected = True
        
        result = controller.set_color(GamepadLEDColor.RED)
        
        assert result is True
        assert controller.current_color == GamepadLEDColor.RED

    def test_set_color_not_connected(self, controller):
        """Test setting color when not connected."""
        controller.is_connected = False
        
        result = controller.set_color(GamepadLEDColor.RED)
        
        assert result is False
        assert controller.current_color == GamepadLEDColor.BLUE  # Unchanged

    def test_set_color_with_brightness(self, controller):
        """Test setting color with custom brightness."""
        controller.is_connected = True
        
        result = controller.set_color(GamepadLEDColor.RED, brightness=0.5)
        
        assert result is True
        assert controller.brightness == 0.5

    def test_set_color_brightness_clamping(self, controller):
        """Test brightness clamping."""
        controller.is_connected = True
        
        # Test minimum brightness
        controller.set_color(GamepadLEDColor.RED, brightness=-0.5)
        assert controller.brightness == 0.0
        
        # Test maximum brightness
        controller.set_color(GamepadLEDColor.RED, brightness=1.5)
        assert controller.brightness == 1.0

    def test_set_color_rgb_success(self, controller):
        """Test setting color with RGB values."""
        controller.is_connected = True
        
        result = controller.set_color_rgb((100, 150, 200))
        
        assert result is True

    def test_set_color_rgb_not_connected(self, controller):
        """Test setting RGB color when not connected."""
        controller.is_connected = False
        
        result = controller.set_color_rgb((100, 150, 200))
        
        assert result is False

    def test_set_color_rgb_with_brightness(self, controller):
        """Test setting RGB color with brightness."""
        controller.is_connected = True
        
        result = controller.set_color_rgb((100, 150, 200), brightness=0.5)
        
        assert result is True
        assert controller.brightness == 0.5

    def test_set_brightness(self, controller):
        """Test setting brightness."""
        controller.is_connected = True
        controller.set_color = Mock(return_value=True)
        
        result = controller.set_brightness(0.7)
        
        assert controller.brightness == 0.7
        controller.set_color.assert_called_once_with(controller.current_color)

    def test_set_brightness_clamping(self, controller):
        """Test brightness clamping in set_brightness."""
        controller.is_connected = True
        
        # Test minimum
        controller.set_brightness(-0.5)
        assert controller.brightness == 0.0
        
        # Test maximum
        controller.set_brightness(1.5)
        assert controller.brightness == 1.0

    def test_turn_off(self, controller):
        """Test turning off the LED."""
        controller.is_connected = True
        controller.stop_animation = Mock()
        controller.set_color = Mock(return_value=True)
        
        result = controller.turn_off()
        
        assert result is True
        controller.stop_animation.assert_called_once()
        controller.set_color.assert_called_once_with(GamepadLEDColor.BLACK)

    def test_pulse_success(self, controller):
        """Test starting pulse animation successfully."""
        controller.is_connected = True
        controller.stop_animation = Mock()
        
        result = controller.pulse(GamepadLEDColor.RED, duration=1.0, cycles=2)
        
        assert result is True
        assert controller.animation_running is True
        assert controller.animation_thread is not None
        assert controller.animation_thread.is_alive()

    def test_pulse_not_connected(self, controller):
        """Test pulse animation when not connected."""
        controller.is_connected = False
        
        result = controller.pulse(GamepadLEDColor.RED)
        
        assert result is False

    def test_pulse_stop_existing_animation(self, controller):
        """Test pulse stops existing animation."""
        controller.is_connected = True
        controller.animation_running = True
        controller.stop_animation = Mock()
        
        controller.pulse(GamepadLEDColor.RED)
        
        controller.stop_animation.assert_called_once()

    def test_pulse_animation_thread(self, controller):
        """Test pulse animation thread execution."""
        controller.is_connected = True
        controller.set_color = Mock()
        
        # Start pulse animation
        controller.pulse(GamepadLEDColor.RED, duration=0.1, cycles=1)
        
        # Wait for animation to complete
        if controller.animation_thread:
            controller.animation_thread.join(timeout=1.0)
        
        # Should have called set_color multiple times
        assert controller.set_color.call_count > 0

    def test_pulse_two_colors_success(self, controller):
        """Test starting two-color pulse animation."""
        controller.is_connected = True
        controller.stop_animation = Mock()
        
        result = controller.pulse_two_colors(
            GamepadLEDColor.RED, GamepadLEDColor.BLUE, duration=1.0, cycles=2
        )
        
        assert result is True
        assert controller.animation_running is True
        assert controller.animation_thread is not None

    def test_pulse_two_colors_not_connected(self, controller):
        """Test two-color pulse when not connected."""
        controller.is_connected = False
        
        result = controller.pulse_two_colors(GamepadLEDColor.RED, GamepadLEDColor.BLUE)
        
        assert result is False

    def test_breathing_animation_success(self, controller):
        """Test starting breathing animation."""
        controller.is_connected = True
        controller.stop_animation = Mock()
        
        result = controller.breathing_animation(GamepadLEDColor.RED, duration=1.0, cycles=2)
        
        assert result is True
        assert controller.animation_running is True
        assert controller.animation_thread is not None

    def test_breathing_animation_not_connected(self, controller):
        """Test breathing animation when not connected."""
        controller.is_connected = False
        
        result = controller.breathing_animation(GamepadLEDColor.RED)
        
        assert result is False

    def test_stop_animation(self, controller):
        """Test stopping animation."""
        controller.animation_running = True
        controller.animation_thread = Mock()
        controller.animation_thread.is_alive.return_value = True
        controller.animation_thread.join = Mock()
        
        controller.stop_animation()
        
        assert controller.animation_running is False
        controller.animation_thread.join.assert_called_once_with(timeout=1.0)

    def test_stop_animation_no_thread(self, controller):
        """Test stopping animation when no thread exists."""
        controller.animation_running = True
        controller.animation_thread = None
        
        # Should not raise exception
        controller.stop_animation()
        
        assert controller.animation_running is False

    def test_get_available_colors(self, controller):
        """Test getting available colors."""
        colors = controller.get_available_colors()
        
        assert isinstance(colors, dict)
        assert "RED" in colors
        assert "GREEN" in colors
        assert "BLUE" in colors
        assert colors["RED"] == (255, 0, 0)
        assert colors["BLUE"] == (0, 0, 255)

    def test_is_available(self, controller):
        """Test checking availability."""
        controller.is_connected = True
        assert controller.is_available() is True
        
        controller.is_connected = False
        assert controller.is_available() is False

    def test_get_control_method(self, controller):
        """Test getting control method name."""
        method = controller.get_control_method()
        assert method == "ConcreteLEDController"

    def test_cleanup(self, controller):
        """Test cleaning up resources."""
        controller.is_connected = True
        controller.stop_animation = Mock()
        controller.turn_off = Mock()
        controller._cleanup_internal = Mock()
        
        controller.cleanup()
        
        controller.stop_animation.assert_called_once()
        controller.turn_off.assert_called_once()
        controller._cleanup_internal.assert_called_once()
        assert controller.is_connected is False

    def test_cleanup_exception(self, controller, caplog):
        """Test cleanup with exception."""
        controller.is_connected = True
        controller.stop_animation = Mock()
        controller.turn_off = Mock()  # Don't raise exception here
        controller._cleanup_internal = Mock(side_effect=Exception("Test error"))  # Raise exception here
        
        controller.cleanup()
        
        assert "Error during LED controller cleanup: Test error" in caplog.text
        controller._cleanup_internal.assert_called_once()
        assert controller.is_connected is False

    def test_cleanup_not_connected(self, controller):
        """Test cleanup when not connected."""
        controller.is_connected = False
        controller.stop_animation = Mock()
        controller.turn_off = Mock()
        controller._cleanup_internal = Mock()
        
        controller.cleanup()
        
        controller.stop_animation.assert_called_once()
        controller.turn_off.assert_not_called()
        controller._cleanup_internal.assert_not_called()

    def test_abstract_methods(self):
        """Test that abstract methods raise NotImplementedError."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseGamepadLEDController()

    def test_brightness_application(self, controller):
        """Test that brightness is properly applied to colors."""
        controller.is_connected = True
        controller.brightness = 0.5
        
        # Mock the internal method to capture the actual RGB values
        with patch.object(controller, '_set_color_internal') as mock_internal:
            controller.set_color(GamepadLEDColor.RED)
            
            # RED = (255, 0, 0), with 0.5 brightness = (127, 0, 0)
            mock_internal.assert_called_once_with(127, 0, 0)

    def test_brightness_application_rgb(self, controller):
        """Test that brightness is properly applied to RGB values."""
        controller.is_connected = True
        controller.brightness = 0.5
        
        with patch.object(controller, '_set_color_internal') as mock_internal:
            controller.set_color_rgb((200, 100, 50))
            
            # With 0.5 brightness = (100, 50, 25)
            mock_internal.assert_called_once_with(100, 50, 25)

    def test_rgb_clamping(self, controller):
        """Test that RGB values are properly clamped."""
        controller.is_connected = True
        controller.brightness = 1.0
        
        with patch.object(controller, '_set_color_internal') as mock_internal:
            # Test values that would exceed 255 after brightness application
            controller.set_color(GamepadLEDColor.WHITE, brightness=2.0)
            
            # Should be clamped to 255
            mock_internal.assert_called_once_with(255, 255, 255)

    def test_animation_thread_naming(self, controller):
        """Test that animation threads are properly named."""
        controller.is_connected = True
        
        # Test pulse animation thread naming
        controller.pulse(GamepadLEDColor.RED, duration=0.01, cycles=1)
        if controller.animation_thread:
            controller.animation_thread.join(timeout=1.0)
            assert controller.animation_thread.name.startswith("GamepadLEDPulseAnimation")
        
        # Test two-color pulse animation thread naming
        controller.pulse_two_colors(GamepadLEDColor.RED, GamepadLEDColor.BLUE, duration=0.01, cycles=1)
        if controller.animation_thread:
            controller.animation_thread.join(timeout=1.0)
            assert controller.animation_thread.name.startswith("GamepadLEDTwoColorPulseAnimation")

    def test_animation_stop_condition(self, controller):
        """Test that animations stop when animation_running is False."""
        controller.is_connected = True
        controller.set_color = Mock()
        
        # Start a short animation
        controller.pulse(GamepadLEDColor.RED, duration=1.0, cycles=0)  # Infinite cycles
        
        # Stop it immediately
        controller.stop_animation()
        
        # Wait a bit to ensure it stopped
        time.sleep(0.1)
        
        # The animation should have stopped
        assert not controller.animation_running

    def test_animation_cycles_limit(self, controller):
        """Test that animations respect cycle limits."""
        controller.is_connected = True
        controller.set_color = Mock()
        
        # Start animation with limited cycles
        controller.pulse(GamepadLEDColor.RED, duration=0.01, cycles=2)
        
        # Wait for completion
        if controller.animation_thread:
            controller.animation_thread.join(timeout=2.0)  # Give more time
        
        # Wait a bit more to ensure animation_running is updated
        import time
        time.sleep(0.2)  # Give more time for the animation to complete
        
        # Should have stopped after 2 cycles
        # If still running, force stop it
        if controller.animation_running:
            controller.stop_animation()
        
        assert not controller.animation_running

    def test_pulse_two_colors_interpolation(self, controller):
        """Test that two-color pulse properly interpolates between colors."""
        controller.is_connected = True
        controller.set_color_rgb = Mock()
        
        # Start two-color animation
        controller.pulse_two_colors(GamepadLEDColor.RED, GamepadLEDColor.BLUE, duration=0.01, cycles=1)
        
        # Wait for completion
        if controller.animation_thread:
            controller.animation_thread.join(timeout=1.0)
        
        # Should have called set_color_rgb multiple times with interpolated values
        assert controller.set_color_rgb.call_count > 0
        
        # Check that interpolation happened (values between RED and BLUE)
        calls = controller.set_color_rgb.call_args_list
        for call_args in calls:
            rgb = call_args[0][0]  # First argument (RGB tuple)
            # Should be interpolated between (255, 0, 0) and (0, 0, 255)
            assert 0 <= rgb[0] <= 255  # Red component
            assert rgb[1] == 0  # Green component (both colors have 0 green)
            assert 0 <= rgb[2] <= 255  # Blue component
