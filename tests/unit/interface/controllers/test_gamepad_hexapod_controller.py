"""
Unit tests for gamepad_hexapod_controller.py module.
"""

import pytest
import os
import time
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path

from hexapod.interface.controllers.gamepad_hexapod_controller import GamepadHexapodController
from hexapod.interface.input_mappings import DualSenseUSBMapping, DualSenseBluetoothMapping
from hexapod.interface.controllers.gamepad_led_controllers import GamepadLEDColor


class TestGamepadHexapodController:
    """Test cases for GamepadHexapodController class."""

    @pytest.fixture
    def mock_task_interface(self):
        """Create a mock task interface."""
        mock_interface = Mock()
        mock_interface.hexapod = Mock()
        mock_interface.hexapod.gait_generator = Mock()
        mock_interface.hexapod.gait_generator.is_running = False
        mock_interface.hexapod.gait_generator.is_gait_running.return_value = False
        mock_interface.hexapod.gait_generator.current_gait = None
        mock_interface.hexapod.gait_generator.create_gait = Mock()
        mock_interface.hexapod.gait_generator.start = Mock()
        mock_interface.hexapod.gait_generator.stop = Mock()
        mock_interface.hexapod.gait_generator.queue_direction = Mock()
        mock_interface.hexapod.gait_params = {
            "translation": {"stance_height": 0.0},
            "rotation": {"stance_height": 0.0}
        }
        mock_interface.hexapod.move_to_position = Mock()
        mock_interface.hexapod.wait_until_motion_complete = Mock()
        mock_interface.hexapod.move_body = Mock()
        mock_interface.hexapod.deactivate_all_servos = Mock()
        mock_interface.hexapod.current_leg_positions = [(0, 0, 0)] * 6
        mock_interface.lights_handler = Mock()
        mock_interface.lights_handler.off = Mock()
        mock_interface.request_unpause_voice_control = Mock()
        mock_interface.request_pause_voice_control = Mock()
        return mock_interface

    @pytest.fixture
    def mock_voice_control(self):
        """Create a mock voice control."""
        return Mock()

    @pytest.fixture
    def mock_gamepad(self):
        """Create a mock pygame joystick."""
        mock_gamepad = Mock()
        mock_gamepad.get_name.return_value = "Wireless Controller"
        mock_gamepad.get_axis.return_value = 0.0
        mock_gamepad.get_button.return_value = False
        mock_gamepad.get_hat.return_value = (0, 0)
        mock_gamepad.init = Mock()
        return mock_gamepad

    @pytest.fixture
    def mock_led_controller(self):
        """Create a mock LED controller."""
        mock_led = Mock()
        mock_led.is_available.return_value = True
        mock_led.pulse = Mock()
        mock_led.pulse_two_colors = Mock()
        mock_led.stop_animation = Mock()
        mock_led.turn_off = Mock()
        mock_led.cleanup = Mock()
        return mock_led

    @pytest.fixture
    def mock_pygame(self):
        """Create a mock pygame module."""
        mock_pygame = Mock()
        mock_pygame.init = Mock()
        mock_pygame.quit = Mock()
        mock_pygame.joystick = Mock()
        mock_pygame.joystick.init = Mock()
        mock_pygame.joystick.get_count.return_value = 1
        mock_pygame.joystick.Joystick = Mock()
        mock_pygame.event = Mock()
        mock_pygame.event.get.return_value = []
        return mock_pygame

    def test_led_controller_type_enum(self):
        """Test LEDControllerType enum values."""
        assert GamepadHexapodController.LEDControllerType.NONE.value == 0
        assert GamepadHexapodController.LEDControllerType.DUALSENSE.value == 1

    def test_input_mapping_type_enum(self):
        """Test InputMappingType enum values."""
        assert GamepadHexapodController.InputMappingType.DUALSENSE_USB.value == 1
        assert GamepadHexapodController.InputMappingType.DUALSENSE_BLUETOOTH.value == 2

    def test_button_debounce_interval(self):
        """Test BUTTON_DEBOUNCE_INTERVAL constant."""
        assert GamepadHexapodController.BUTTON_DEBOUNCE_INTERVAL == 0.3

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    def test_find_gamepad_success(self, mock_pygame, mock_task_interface):
        """Test finding a gamepad successfully."""
        mock_joystick = Mock()
        mock_joystick.get_name.return_value = "Wireless Controller"
        mock_pygame.joystick.Joystick.return_value = mock_joystick
        mock_pygame.joystick.get_count.return_value = 1
        
        input_mapping = DualSenseBluetoothMapping()
        result = GamepadHexapodController.find_gamepad(input_mapping, check_only=False)
        
        assert result == mock_joystick
        mock_joystick.init.assert_called_once()

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    def test_find_gamepad_check_only(self, mock_pygame, mock_task_interface):
        """Test checking gamepad availability only."""
        mock_joystick = Mock()
        mock_joystick.get_name.return_value = "Wireless Controller"
        mock_pygame.joystick.Joystick.return_value = mock_joystick
        mock_pygame.joystick.get_count.return_value = 1
        
        input_mapping = DualSenseBluetoothMapping()
        result = GamepadHexapodController.find_gamepad(input_mapping, check_only=True)
        
        assert result is True
        mock_pygame.quit.assert_called_once()

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', False)
    def test_find_gamepad_pygame_not_available(self, mock_task_interface):
        """Test finding gamepad when pygame is not available."""
        input_mapping = DualSenseBluetoothMapping()
        result = GamepadHexapodController.find_gamepad(input_mapping, check_only=False)
        assert result is None
        
        result = GamepadHexapodController.find_gamepad(input_mapping, check_only=True)
        assert result is False

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    def test_find_gamepad_no_joysticks(self, mock_pygame, mock_task_interface):
        """Test finding gamepad when no joysticks are available."""
        mock_pygame.joystick.get_count.return_value = 0
        
        input_mapping = DualSenseBluetoothMapping()
        result = GamepadHexapodController.find_gamepad(input_mapping, check_only=False)
        assert result is None

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    def test_find_gamepad_exception(self, mock_pygame, mock_task_interface, caplog):
        """Test finding gamepad when exception occurs."""
        mock_pygame.init.side_effect = Exception("Test error")
        
        input_mapping = DualSenseBluetoothMapping()
        result = GamepadHexapodController.find_gamepad(input_mapping, check_only=False)
        assert result is None
        assert "Error checking/finding gamepad: Test error" in caplog.text

    def test_get_gamepad_connection_type_bluetooth(self, mock_gamepad):
        """Test getting connection type for Bluetooth gamepad."""
        mock_gamepad.get_name.return_value = "Wireless Controller"
        
        result = GamepadHexapodController.get_gamepad_connection_type(mock_gamepad)
        assert result == "bluetooth"

    def test_get_gamepad_connection_type_usb(self, mock_gamepad):
        """Test getting connection type for USB gamepad."""
        mock_gamepad.get_name.return_value = "DualSense Controller"
        
        result = GamepadHexapodController.get_gamepad_connection_type(mock_gamepad)
        assert result == "usb"

    def test_get_gamepad_connection_type_none(self):
        """Test getting connection type for None gamepad."""
        result = GamepadHexapodController.get_gamepad_connection_type(None)
        assert result is None

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_init_default_parameters(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad):
        """Test initialization with default parameters."""
        mock_find_gamepad.return_value = mock_gamepad
        
        controller = GamepadHexapodController(task_interface=mock_task_interface)
        
        assert controller.task_interface == mock_task_interface
        assert controller.voice_control is None
        assert controller.shutdown_callback is None
        assert isinstance(controller.input_mapping, DualSenseBluetoothMapping)
        assert controller.gamepad == mock_gamepad
        assert controller.deadzone == 0.1
        assert controller.marching_enabled is False

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_init_custom_parameters(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_voice_control, mock_gamepad):
        """Test initialization with custom parameters."""
        mock_find_gamepad.return_value = mock_gamepad
        shutdown_callback = Mock()
        
        controller = GamepadHexapodController(
            task_interface=mock_task_interface,
            voice_control=mock_voice_control,
            input_mapping_type=GamepadHexapodController.InputMappingType.DUALSENSE_USB,
            led_controller_type=GamepadHexapodController.LEDControllerType.DUALSENSE,
            shutdown_callback=shutdown_callback
        )
        
        assert controller.voice_control == mock_voice_control
        assert controller.shutdown_callback == shutdown_callback
        assert isinstance(controller.input_mapping, DualSenseUSBMapping)

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', False)
    def test_init_pygame_not_available(self, mock_task_interface):
        """Test initialization when pygame is not available."""
        with pytest.raises(ImportError, match="pygame is required for gamepad support"):
            GamepadHexapodController(task_interface=mock_task_interface)

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_init_no_gamepad_found(self, mock_find_gamepad, mock_pygame, mock_task_interface, caplog):
        """Test initialization when no gamepad is found."""
        mock_find_gamepad.return_value = None
        
        with pytest.raises(RuntimeError, match="Gamepad not found"):
            GamepadHexapodController(task_interface=mock_task_interface)

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_init_fallback_to_usb(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad, caplog):
        """Test initialization with fallback to USB mapping."""
        # First call returns None (Bluetooth fails), second call returns gamepad (USB succeeds)
        mock_find_gamepad.side_effect = [None, mock_gamepad]
        
        controller = GamepadHexapodController(
            task_interface=mock_task_interface,
            input_mapping_type=GamepadHexapodController.InputMappingType.DUALSENSE_BLUETOOTH,
            led_controller_type=GamepadHexapodController.LEDControllerType.NONE  # Disable LED to avoid warnings
        )
        
        assert isinstance(controller.input_mapping, DualSenseUSBMapping)
        # Verify that find_gamepad was called twice (once for Bluetooth, once for USB)
        assert mock_find_gamepad.call_count == 2
        # The fallback logic worked correctly - we started with Bluetooth but ended up with USB
        assert controller.gamepad is mock_gamepad

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_init_with_led_controller_usb(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad):
        """Test initialization with LED controller for USB connection."""
        mock_find_gamepad.return_value = mock_gamepad
        mock_gamepad.get_name.return_value = "DualSense Controller"  # USB
        
        # Test that the controller tries to initialize LED controller for USB
        controller = GamepadHexapodController(
            task_interface=mock_task_interface,
            led_controller_type=GamepadHexapodController.LEDControllerType.DUALSENSE
        )
        
        # Due to mocking in conftest.py, DualSenseLEDController will fail to initialize
        # but the controller should still be created successfully
        assert controller.led_controller is not None  # It creates a DualSenseLEDController instance
        assert hasattr(controller, 'gamepad')
        assert controller.gamepad is mock_gamepad

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_init_with_led_controller_bluetooth_warning(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad, caplog):
        """Test initialization with LED controller for Bluetooth connection (should warn)."""
        mock_find_gamepad.return_value = mock_gamepad
        mock_gamepad.get_name.return_value = "Wireless Controller"  # Bluetooth
        
        controller = GamepadHexapodController(
            task_interface=mock_task_interface,
            led_controller_type=GamepadHexapodController.LEDControllerType.DUALSENSE
        )
        
        assert controller.led_controller is None
        assert "Gamepad is in Bluetooth mode: Gamepad LED controller is not supported" in caplog.text

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_apply_deadzone(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad):
        """Test applying deadzone to analog values."""
        mock_find_gamepad.return_value = mock_gamepad
        
        controller = GamepadHexapodController(task_interface=mock_task_interface)
        
        # Test values within deadzone
        assert controller._apply_deadzone(0.05) == 0.0
        assert controller._apply_deadzone(-0.05) == 0.0
        
        # Test values outside deadzone
        assert controller._apply_deadzone(0.5) == pytest.approx(0.444, rel=1e-2)
        assert controller._apply_deadzone(-0.5) == pytest.approx(-0.444, rel=1e-2)
        
        # Test edge values
        assert controller._apply_deadzone(1.0) == 1.0
        assert controller._apply_deadzone(-1.0) == -1.0

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_get_analog_inputs(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad):
        """Test getting analog inputs from gamepad."""
        mock_find_gamepad.return_value = mock_gamepad
        
        # Mock the axis values for each axis mapping
        def mock_get_axis(axis_index):
            axis_values = {
                0: 0.5,   # left_x
                1: -0.3,  # left_y
                2: 0.8,   # right_x
                3: -0.2,  # l2 (above deadzone)
                4: 0.2,   # r2 (above deadzone)
                5: 0.2    # right_y
            }
            return axis_values.get(axis_index, 0.0)
        
        mock_gamepad.get_axis.side_effect = mock_get_axis
        
        controller = GamepadHexapodController(task_interface=mock_task_interface)
        controller.input_mapping = DualSenseBluetoothMapping()
        
        result = controller._get_analog_inputs()
        
        expected = {
            "left_x": pytest.approx(0.444, rel=1e-2),
            "left_y": pytest.approx(-0.222, rel=1e-2),
            "right_x": pytest.approx(0.777, rel=1e-2),
            "right_y": pytest.approx(0.111, rel=1e-2),
            "l2": pytest.approx(-0.111, rel=1e-2),
            "r2": pytest.approx(0.111, rel=1e-2)
        }
        
        for key, value in expected.items():
            assert result[key] == pytest.approx(value, rel=1e-2)

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_get_analog_inputs_no_gamepad(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad):
        """Test getting analog inputs when no gamepad is available."""
        mock_find_gamepad.return_value = mock_gamepad
        
        controller = GamepadHexapodController(task_interface=mock_task_interface)
        controller.gamepad = None
        
        result = controller._get_analog_inputs()
        assert result == {}

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_get_button_states(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad):
        """Test getting button states from gamepad."""
        mock_find_gamepad.return_value = mock_gamepad
        mock_gamepad.get_button.side_effect = [True, False, True, False] * 4  # Various button states
        mock_gamepad.get_axis.side_effect = [0.8, 0.3]  # l2, r2 axes
        
        controller = GamepadHexapodController(task_interface=mock_task_interface)
        controller.input_mapping = DualSenseBluetoothMapping()
        
        result = controller._get_button_states()
        
        assert "square" in result
        assert "x" in result
        assert "circle" in result
        assert "triangle" in result
        assert "l1" in result
        assert "r1" in result
        assert "l2" in result
        assert "r2" in result
        assert result["l2"] is True  # 0.8 > 0.5
        assert result["r2"] is False  # 0.3 < 0.5

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_get_dpad_states_usb_mode(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad):
        """Test getting D-pad states in USB mode (buttons)."""
        mock_find_gamepad.return_value = mock_gamepad
        mock_gamepad.get_button.side_effect = [True, False, True, False]  # dpad buttons
        
        controller = GamepadHexapodController(task_interface=mock_task_interface)
        controller.input_mapping = DualSenseUSBMapping()
        
        result = controller._get_dpad_states(controller.input_mapping.get_button_mappings())
        
        assert "dpad_up" in result
        assert "dpad_down" in result
        assert "dpad_left" in result
        assert "dpad_right" in result

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_get_dpad_states_bluetooth_mode(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad):
        """Test getting D-pad states in Bluetooth mode (hat)."""
        mock_find_gamepad.return_value = mock_gamepad
        mock_gamepad.get_hat.return_value = (1, 0)  # Right pressed
        
        controller = GamepadHexapodController(task_interface=mock_task_interface)
        controller.input_mapping = DualSenseBluetoothMapping()
        
        result = controller._get_dpad_states(controller.input_mapping.get_button_mappings())
        
        assert result["dpad_right"] is True
        assert result["dpad_left"] is False
        assert result["dpad_up"] is False
        assert result["dpad_down"] is False

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_check_button_press(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad):
        """Test checking button press with debounce."""
        mock_find_gamepad.return_value = mock_gamepad
        
        controller = GamepadHexapodController(task_interface=mock_task_interface)
        controller.button_states = {"test_button": True}
        controller.last_button_states = {"test_button": False}
        controller._button_last_press_time = {}
        
        # First press should return True
        result = controller._check_button_press("test_button")
        assert result is True
        
        # Immediate second press should return False (debounced)
        result = controller._check_button_press("test_button")
        assert result is False

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_check_button_press_after_debounce(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad):
        """Test checking button press after debounce period."""
        mock_find_gamepad.return_value = mock_gamepad
        
        controller = GamepadHexapodController(task_interface=mock_task_interface)
        controller.button_states = {"test_button": True}
        controller.last_button_states = {"test_button": False}
        controller._button_last_press_time = {"test_button": time.time() - 1.0}  # Old timestamp
        
        result = controller._check_button_press("test_button")
        assert result is True

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_on_mode_toggled(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad, mock_led_controller):
        """Test mode toggled hook with LED feedback."""
        mock_find_gamepad.return_value = mock_gamepad
        
        controller = GamepadHexapodController(task_interface=mock_task_interface)
        controller.led_controller = mock_led_controller
        
        # Test body control mode
        controller._on_mode_toggled(controller.BODY_CONTROL_MODE)
        mock_led_controller.stop_animation.assert_called_once()
        mock_led_controller.pulse.assert_called_with(GamepadLEDColor.BLUE, duration=2.0, cycles=0)
        
        # Test gait control mode
        controller._on_mode_toggled(controller.GAIT_CONTROL_MODE)
        mock_led_controller.pulse.assert_called_with(GamepadLEDColor.INDIGO, duration=2.0, cycles=0)
        
        # Test voice control mode
        controller._on_mode_toggled(controller.VOICE_CONTROL_MODE)
        mock_led_controller.pulse_two_colors.assert_called_with(
            GamepadLEDColor.BLUE, GamepadLEDColor.GREEN, duration=2.0, cycles=0
        )

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_get_inputs_ps5_button(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad):
        """Test get_inputs with PS5 button press."""
        mock_find_gamepad.return_value = mock_gamepad
        
        controller = GamepadHexapodController(task_interface=mock_task_interface)
        controller.current_mode = controller.BODY_CONTROL_MODE
        controller._get_analog_inputs = Mock(return_value={
            "left_x": 0.0, "left_y": 0.0, "right_x": 0.0, "right_y": 0.0, "l2": 0.0, "r2": 0.0
        })
        controller._get_button_states = Mock(return_value={"ps5": True, "square": False})
        controller._check_button_press = Mock(side_effect=lambda btn: btn == "ps5")
        controller.trigger_shutdown = Mock()
        
        result = controller.get_inputs()
        
        controller.trigger_shutdown.assert_called_once()

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_get_inputs_options_button(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad):
        """Test get_inputs with Options button press."""
        mock_find_gamepad.return_value = mock_gamepad
        
        controller = GamepadHexapodController(task_interface=mock_task_interface)
        controller.current_mode = controller.BODY_CONTROL_MODE
        controller._get_analog_inputs = Mock(return_value={
            "left_x": 0.0, "left_y": 0.0, "right_x": 0.0, "right_y": 0.0, "l2": 0.0, "r2": 0.0
        })
        controller._get_button_states = Mock(return_value={"options": True, "ps5": False})
        controller._check_button_press = Mock(side_effect=lambda btn: btn == "options")
        controller.toggle_mode = Mock()
        
        result = controller.get_inputs()
        
        controller.toggle_mode.assert_called_once()

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_get_inputs_create_button(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad):
        """Test get_inputs with Create button press."""
        mock_find_gamepad.return_value = mock_gamepad
        
        controller = GamepadHexapodController(task_interface=mock_task_interface)
        controller.current_mode = controller.BODY_CONTROL_MODE
        controller._get_analog_inputs = Mock(return_value={
            "left_x": 0.0, "left_y": 0.0, "right_x": 0.0, "right_y": 0.0, "l2": 0.0, "r2": 0.0
        })
        controller._get_button_states = Mock(return_value={"create": True, "ps5": False})
        controller._check_button_press = Mock(side_effect=lambda btn: btn == "create")
        controller.toggle_voice_control_mode = Mock()
        
        result = controller.get_inputs()
        
        controller.toggle_voice_control_mode.assert_called_once()

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_get_inputs_voice_control_mode(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad):
        """Test get_inputs in voice control mode."""
        mock_find_gamepad.return_value = mock_gamepad
        
        controller = GamepadHexapodController(task_interface=mock_task_interface)
        controller.current_mode = controller.VOICE_CONTROL_MODE
        controller._get_analog_inputs = Mock(return_value={})
        controller._get_button_states = Mock(return_value={"ps5": False})
        controller._check_button_press = Mock(return_value=False)
        
        result = controller.get_inputs()
        
        assert result == {}

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_process_stance_height_l2_r2_single_click(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad, caplog):
        """Test L2/R2 stance height adjustment with single click."""
        mock_find_gamepad.return_value = mock_gamepad
        
        controller = GamepadHexapodController(task_interface=mock_task_interface)
        controller.gait_stance_height = 0.0
        controller.button_states = {"l2": True, "r2": False}
        controller._stance_height_hold_start = {"l2": None, "r2": None}
        controller._stance_height_last_increment = {"l2": None, "r2": None}
        
        # Simulate quick press and release
        with patch('time.time', side_effect=[0, 0.1]):  # Quick press
            result = controller._process_stance_height_l2_r2()
            assert result == 0.0  # No delta yet
            
            controller.button_states = {"l2": False, "r2": False}
            result = controller._process_stance_height_l2_r2()
            assert result == -controller.GAIT_STANCE_HEIGHT_STEP

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_get_body_control_inputs(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad):
        """Test getting body control inputs."""
        mock_find_gamepad.return_value = mock_gamepad
        
        controller = GamepadHexapodController(task_interface=mock_task_interface)
        controller.analog_inputs = {
            "left_x": 0.5,
            "left_y": -0.3,
            "right_x": 0.8,
            "right_y": -0.2,
            "l2": 0.6,
            "r2": 0.4
        }
        controller.button_states = {
            "l1": True,
            "r1": False,
            "triangle": False,
            "square": False,
            "circle": False,
            "dpad_left": False,
            "dpad_right": False,
            "dpad_up": False,
            "dpad_down": False
        }
        controller._check_button_press = Mock(return_value=False)
        controller.reset_position = Mock()
        controller.show_current_position = Mock()
        controller.print_help = Mock()
        
        result = controller._get_body_control_inputs()
        
        assert result["tx"] == 0.5
        assert result["ty"] == 0.3  # Inverted
        assert result["tz"] == pytest.approx(-0.2, rel=1e-10)  # r2 - l2
        assert result["roll"] == 0.8
        assert result["pitch"] == 0.2  # Inverted
        assert result["yaw"] == -1.0  # L1 pressed

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_get_gait_control_inputs(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad, caplog):
        """Test getting gait control inputs."""
        mock_find_gamepad.return_value = mock_gamepad
        
        controller = GamepadHexapodController(
            task_interface=mock_task_interface,
            led_controller_type=GamepadHexapodController.LEDControllerType.NONE  # Disable LED to avoid warnings
        )
        controller.analog_inputs = {
            "left_x": 0.5,
            "left_y": -0.3,
            "right_x": 0.8
        }
        controller.button_states = {
            "x": False,
            "triangle": False,
            "square": False,
            "circle": False,
            "dpad_left": False,
            "dpad_right": False,
            "dpad_up": False,
            "dpad_down": False
        }
        controller._check_button_press = Mock(side_effect=lambda btn: btn == "x")
        controller._process_stance_height_l2_r2 = Mock(return_value=0.0)
        controller.reset_position = Mock()
        controller.show_current_position = Mock()
        controller.print_help = Mock()
        
        result = controller._get_gait_control_inputs()
        
        assert result["direction_x"] == 0.5
        assert result["direction_y"] == 0.3  # Inverted
        assert result["rotation"] == 0.8
        # The test verifies that the gait control inputs are correctly processed
        # The marching enabled state is controlled by the reset_position mock

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_print_help(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad, caplog):
        """Test printing help information."""
        mock_find_gamepad.return_value = mock_gamepad
        
        controller = GamepadHexapodController(
            task_interface=mock_task_interface,
            led_controller_type=GamepadHexapodController.LEDControllerType.NONE  # Disable LED to avoid warnings
        )
        controller.input_mapping = DualSenseBluetoothMapping()
        
        # Test that print_help method executes without error
        controller.print_help()
        
        # Verify the method was called (it will log messages to the custom logger)
        # The method exists and executes successfully

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_cleanup_controller(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad, mock_led_controller):
        """Test cleaning up controller resources."""
        mock_find_gamepad.return_value = mock_gamepad
        
        controller = GamepadHexapodController(task_interface=mock_task_interface)
        controller.led_controller = mock_led_controller
        
        controller.cleanup_controller()
        
        mock_led_controller.turn_off.assert_called_once()
        mock_led_controller.cleanup.assert_called_once()
        mock_pygame.quit.assert_called_once()

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_cleanup_controller_exception(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad, mock_led_controller, caplog):
        """Test cleaning up controller resources with exception."""
        mock_find_gamepad.return_value = mock_gamepad
        mock_led_controller.turn_off.side_effect = Exception("Test error")
        
        controller = GamepadHexapodController(task_interface=mock_task_interface)
        controller.led_controller = mock_led_controller
        
        controller.cleanup_controller()
        
        assert "Error during LED cleanup: Test error" in caplog.text
        mock_pygame.quit.assert_called_once()

    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.PYGAME_AVAILABLE', True)
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame')
    @patch('hexapod.interface.controllers.gamepad_hexapod_controller.GamepadHexapodController.find_gamepad')
    def test_start_initial_animation(self, mock_find_gamepad, mock_pygame, mock_task_interface, mock_gamepad, mock_led_controller):
        """Test starting initial animation."""
        mock_find_gamepad.return_value = mock_gamepad
        
        controller = GamepadHexapodController(task_interface=mock_task_interface)
        controller.led_controller = mock_led_controller
        controller.current_mode = controller.BODY_CONTROL_MODE
        
        controller._start_initial_animation()
        
        # Should call parent method
        controller.task_interface.lights_handler.pulse_smoothly.assert_called_once()
        # Should also call LED controller
        mock_led_controller.pulse.assert_called_with(GamepadLEDColor.BLUE, duration=2.0, cycles=0)
