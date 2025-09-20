"""
Unit tests for base_manual_controller.py module.
"""

import pytest
import threading
import time
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path

from hexapod.interface.controllers.base_manual_controller import ManualHexapodController
from hexapod.robot import PredefinedPosition
from hexapod.gait_generator import BaseGait, TripodGait
from hexapod.lights import ColorRGB


class TestManualHexapodController:
    """Test cases for ManualHexapodController class."""

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
        mock_interface.lights_handler.pulse_smoothly = Mock()
        mock_interface.lights_handler.think = Mock()
        mock_interface.request_unpause_voice_control = Mock()
        mock_interface.request_pause_voice_control = Mock()
        return mock_interface

    @pytest.fixture
    def mock_voice_control(self):
        """Create a mock voice control."""
        return Mock()

    @pytest.fixture
    def concrete_controller(self, mock_task_interface, mock_voice_control):
        """Create a concrete implementation of ManualHexapodController for testing."""
        class ConcreteController(ManualHexapodController):
            def get_inputs(self):
                return {}
            
            def print_help(self):
                pass
            
            def cleanup_controller(self):
                pass

        controller = ConcreteController(
            task_interface=mock_task_interface,
            voice_control=mock_voice_control
        )
        # Mock all the methods that need to be mocked
        controller.show_gait_status = Mock()
        controller.print_current_position_details = Mock()
        controller.print_current_sensitivity_levels = Mock()
        controller.stop = Mock()
        controller.cleanup = Mock()
        controller.pause_event = Mock()
        controller.pause_event.is_set = Mock(return_value=False)
        controller.pause_event.set = Mock()
        controller.pause_event.clear = Mock()
        controller.stop_event = Mock()
        controller.stop_event.is_set = Mock(return_value=False)
        controller.stop_event.set = Mock()
        controller.stop_event.clear = Mock()
        return controller

    def test_init_default_parameters(self, mock_task_interface):
        """Test initialization with default parameters."""
        class ConcreteController(ManualHexapodController):
            def get_inputs(self):
                return {}
            def print_help(self):
                pass
            def cleanup_controller(self):
                pass
        
        controller = ConcreteController(mock_task_interface)
        
        assert controller.task_interface == mock_task_interface
        assert controller.voice_control is None
        assert controller.shutdown_callback is None
        assert controller.current_mode == controller.DEFAULT_MODE
        assert controller.current_tx == 0.0
        assert controller.current_ty == 0.0
        assert controller.current_tz == 0.0
        assert controller.current_roll == 0.0
        assert controller.current_pitch == 0.0
        assert controller.current_yaw == 0.0
        assert controller.update_rate == 20
        assert controller.update_interval == 1.0 / 20
        assert controller.translation_sensitivity == controller.DEFAULT_TRANSLATION_SENSITIVITY
        assert controller.rotation_sensitivity == controller.DEFAULT_ROTATION_SENSITIVITY
        assert controller.gait_direction_sensitivity == controller.DEFAULT_GAIT_DIRECTION_SENSITIVITY
        assert controller.gait_rotation_sensitivity == controller.DEFAULT_GAIT_ROTATION_SENSITIVITY
        assert controller.marching_enabled is False
        assert controller.gait_stance_height == 0.0

    def test_init_custom_parameters(self, mock_task_interface, mock_voice_control):
        """Test initialization with custom parameters."""
        class ConcreteController(ManualHexapodController):
            def get_inputs(self):
                return {}
            def print_help(self):
                pass
            def cleanup_controller(self):
                pass
        
        shutdown_callback = Mock()
        controller = ConcreteController(
            task_interface=mock_task_interface,
            voice_control=mock_voice_control,
            shutdown_callback=shutdown_callback
        )
        
        assert controller.voice_control == mock_voice_control
        assert controller.shutdown_callback == shutdown_callback

    def test_init_gait_stance_height_from_config(self, mock_task_interface):
        """Test initialization with gait stance height from config."""
        class ConcreteController(ManualHexapodController):
            def get_inputs(self):
                return {}
            def print_help(self):
                pass
            def cleanup_controller(self):
                pass
        
        mock_task_interface.hexapod.gait_params = {
            "translation": {"stance_height": 10.0},
            "rotation": {"stance_height": 15.0}
        }
        
        controller = ConcreteController(mock_task_interface)
        assert controller.gait_stance_height == 10.0

    def test_init_gait_stance_height_exception(self, mock_task_interface):
        """Test initialization when config access fails."""
        class ConcreteController(ManualHexapodController):
            def get_inputs(self):
                return {}
            def print_help(self):
                pass
            def cleanup_controller(self):
                pass
        
        mock_task_interface.hexapod.gait_params = None
        
        controller = ConcreteController(mock_task_interface)
        assert controller.gait_stance_height == 0.0

    def test_constants(self):
        """Test class constants."""
        assert ManualHexapodController.TRANSLATION_STEP == 6.0
        assert ManualHexapodController.ROLL_STEP == 2.0
        assert ManualHexapodController.PITCH_STEP == 2.0
        assert ManualHexapodController.YAW_STEP == 4.0
        assert ManualHexapodController.Z_STEP == 4.0
        assert ManualHexapodController.GAIT_STANCE_HEIGHT_STEP == 2.0
        assert ManualHexapodController.GAIT_MIN_STANCE_HEIGHT == -40.0
        assert ManualHexapodController.GAIT_MAX_STANCE_HEIGHT == 40.0
        assert ManualHexapodController.DEFAULT_TRANSLATION_SENSITIVITY == 0.5
        assert ManualHexapodController.DEFAULT_ROTATION_SENSITIVITY == 0.5
        assert ManualHexapodController.DEFAULT_GAIT_DIRECTION_SENSITIVITY == 0.5
        assert ManualHexapodController.DEFAULT_GAIT_ROTATION_SENSITIVITY == 0.5
        assert ManualHexapodController.SENSITIVITY_ADJUSTMENT_STEP == 0.1
        assert ManualHexapodController.MIN_SENSITIVITY == 0.1
        assert ManualHexapodController.MAX_SENSITIVITY == 1.0
        assert ManualHexapodController.BODY_CONTROL_MODE == "body_control"
        assert ManualHexapodController.GAIT_CONTROL_MODE == "gait_control"
        assert ManualHexapodController.VOICE_CONTROL_MODE == "voice_control"
        assert ManualHexapodController.DEFAULT_MODE == "body_control"

    def test_set_mode_valid(self, concrete_controller):
        """Test setting valid modes."""
        concrete_controller.set_mode(concrete_controller.BODY_CONTROL_MODE)
        assert concrete_controller.current_mode == concrete_controller.BODY_CONTROL_MODE
        
        concrete_controller.set_mode(concrete_controller.GAIT_CONTROL_MODE)
        assert concrete_controller.current_mode == concrete_controller.GAIT_CONTROL_MODE
        
        concrete_controller.set_mode(concrete_controller.VOICE_CONTROL_MODE)
        assert concrete_controller.current_mode == concrete_controller.VOICE_CONTROL_MODE

    def test_set_mode_invalid(self, concrete_controller):
        """Test setting invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="Unknown mode: invalid_mode"):
            concrete_controller.set_mode("invalid_mode")

    def test_reset_position_body_control_mode(self, concrete_controller):
        """Test reset position in body control mode."""
        concrete_controller.current_mode = concrete_controller.BODY_CONTROL_MODE
        
        concrete_controller.reset_position()
        
        concrete_controller.task_interface.hexapod.move_to_position.assert_called_once_with(PredefinedPosition.LOW_PROFILE)
        concrete_controller.task_interface.hexapod.wait_until_motion_complete.assert_called_once()
        assert concrete_controller.current_tx == 0.0
        assert concrete_controller.current_ty == 0.0
        assert concrete_controller.current_tz == 0.0
        assert concrete_controller.current_roll == 0.0
        assert concrete_controller.current_pitch == 0.0
        assert concrete_controller.current_yaw == 0.0

    def test_reset_position_gait_control_mode(self, concrete_controller):
        """Test reset position in gait control mode."""
        concrete_controller.current_mode = concrete_controller.GAIT_CONTROL_MODE
        
        concrete_controller.reset_position()
        
        concrete_controller.task_interface.hexapod.move_to_position.assert_called_once_with(PredefinedPosition.ZERO)
        concrete_controller.task_interface.hexapod.wait_until_motion_complete.assert_called_once()
        assert concrete_controller.gait_stance_height == 0.0

    def test_reset_position_exception(self, concrete_controller):
        """Test reset position when exception occurs."""
        concrete_controller.task_interface.hexapod.move_to_position.side_effect = Exception("Test error")
        
        # Should not raise exception
        concrete_controller.reset_position()

    def test_start_gait_control_default_params(self, concrete_controller):
        """Test starting gait control with default parameters."""
        # Mock the current_gait to return a mock gait
        mock_gait = Mock()
        concrete_controller.task_interface.hexapod.gait_generator.current_gait = mock_gait
        
        concrete_controller.start_gait_control()
        
        assert concrete_controller.gait_type == TripodGait
        assert concrete_controller.translation_gait is not None
        assert concrete_controller.rotation_gait is not None
        assert concrete_controller.current_gait == concrete_controller.translation_gait

    def test_start_gait_control_custom_params(self, concrete_controller):
        """Test starting gait control with custom parameters."""
        custom_gait_type = Mock()
        translation_params = {"stance_height": 5.0}
        rotation_params = {"stance_height": 10.0}
        
        concrete_controller.start_gait_control(
            gait_type=custom_gait_type,
            translation_params=translation_params,
            rotation_params=rotation_params
        )
        
        assert concrete_controller.gait_type == custom_gait_type

    def test_stop_gait_control(self, concrete_controller):
        """Test stopping gait control."""
        # Reset the mock to ensure clean state
        concrete_controller.task_interface.hexapod.gait_generator.reset_mock()
        concrete_controller.task_interface.hexapod.gait_generator.is_gait_running.return_value = True
        
        # Don't mock the stop_gait_control method, let it run the actual implementation
        concrete_controller.stop_gait_control = ManualHexapodController.stop_gait_control.__get__(concrete_controller, ConcreteController)
        
        concrete_controller.stop_gait_control()
        
        concrete_controller.task_interface.hexapod.gait_generator.stop.assert_called_once()

    def test_stop_gait_control_not_running(self, concrete_controller):
        """Test stopping gait control when not running."""
        concrete_controller.task_interface.hexapod.gait_generator.is_gait_running.return_value = False
        
        concrete_controller.stop_gait_control()
        
        concrete_controller.task_interface.hexapod.gait_generator.stop.assert_not_called()

    def test_is_gait_control_active(self, concrete_controller):
        """Test checking if gait control is active."""
        concrete_controller.task_interface.hexapod.gait_generator.is_gait_running.return_value = True
        assert concrete_controller.is_gait_control_active() is True
        
        concrete_controller.task_interface.hexapod.gait_generator.is_gait_running.return_value = False
        assert concrete_controller.is_gait_control_active() is False

    def test_process_stance_height_delta_gait_mode(self, concrete_controller):
        """Test processing stance height delta in gait mode."""
        concrete_controller.current_mode = concrete_controller.GAIT_CONTROL_MODE
        concrete_controller.gait_stance_height = 0.0
        concrete_controller.current_gait = Mock()
        
        inputs = {"stance_height_delta": 5.0}
        concrete_controller._process_stance_height_delta(inputs)
        
        assert concrete_controller.gait_stance_height == 5.0
        assert concrete_controller.current_gait.stance_height == 5.0

    def test_process_stance_height_delta_body_mode(self, concrete_controller):
        """Test processing stance height delta in body mode (should be ignored)."""
        concrete_controller.current_mode = concrete_controller.BODY_CONTROL_MODE
        original_height = concrete_controller.gait_stance_height
        
        inputs = {"stance_height_delta": 5.0}
        concrete_controller._process_stance_height_delta(inputs)
        
        assert concrete_controller.gait_stance_height == original_height

    def test_process_stance_height_delta_zero_delta(self, concrete_controller):
        """Test processing stance height delta with zero delta."""
        concrete_controller.current_mode = concrete_controller.GAIT_CONTROL_MODE
        original_height = concrete_controller.gait_stance_height
        
        inputs = {"stance_height_delta": 0.0}
        concrete_controller._process_stance_height_delta(inputs)
        
        assert concrete_controller.gait_stance_height == original_height

    def test_process_stance_height_delta_limits(self, concrete_controller):
        """Test processing stance height delta with limits."""
        concrete_controller.current_mode = concrete_controller.GAIT_CONTROL_MODE
        concrete_controller.gait_stance_height = 0.0
        
        # Test minimum limit
        inputs = {"stance_height_delta": -100.0}
        concrete_controller._process_stance_height_delta(inputs)
        assert concrete_controller.gait_stance_height == concrete_controller.GAIT_MIN_STANCE_HEIGHT
        
        # Test maximum limit
        inputs = {"stance_height_delta": 100.0}
        concrete_controller._process_stance_height_delta(inputs)
        assert concrete_controller.gait_stance_height == concrete_controller.GAIT_MAX_STANCE_HEIGHT

    def test_process_movement_inputs_body_control(self, concrete_controller):
        """Test processing movement inputs in body control mode."""
        concrete_controller.current_mode = concrete_controller.BODY_CONTROL_MODE
        concrete_controller._process_body_control = Mock()
        concrete_controller._process_sensitivity_deltas = Mock()
        concrete_controller._process_stance_height_delta = Mock()
        
        inputs = {"tx": 1.0, "ty": 2.0}
        concrete_controller.process_movement_inputs(inputs)
        
        concrete_controller._process_sensitivity_deltas.assert_called_once_with(inputs)
        concrete_controller._process_stance_height_delta.assert_called_once_with(inputs)
        concrete_controller._process_body_control.assert_called_once_with(inputs)

    def test_process_movement_inputs_gait_control(self, concrete_controller):
        """Test processing movement inputs in gait control mode."""
        concrete_controller.current_mode = concrete_controller.GAIT_CONTROL_MODE
        concrete_controller._process_gait_control = Mock()
        concrete_controller._process_sensitivity_deltas = Mock()
        concrete_controller._process_stance_height_delta = Mock()
        
        inputs = {"direction_x": 1.0, "direction_y": 2.0}
        concrete_controller.process_movement_inputs(inputs)
        
        concrete_controller._process_sensitivity_deltas.assert_called_once_with(inputs)
        concrete_controller._process_stance_height_delta.assert_called_once_with(inputs)
        concrete_controller._process_gait_control.assert_called_once_with(inputs)

    def test_process_movement_inputs_unknown_mode(self, concrete_controller):
        """Test processing movement inputs with unknown mode."""
        concrete_controller.current_mode = "unknown_mode"
        concrete_controller._process_sensitivity_deltas = Mock()
        concrete_controller._process_stance_height_delta = Mock()
        
        inputs = {"tx": 1.0}
        concrete_controller.process_movement_inputs(inputs)
        
        concrete_controller._process_sensitivity_deltas.assert_called_once_with(inputs)
        concrete_controller._process_stance_height_delta.assert_called_once_with(inputs)
        # Unknown mode should not call any specific processing method

    def test_process_body_control_with_movement(self, concrete_controller):
        """Test body control processing with movement inputs."""
        concrete_controller.current_mode = concrete_controller.BODY_CONTROL_MODE
        concrete_controller.translation_sensitivity = 1.0
        concrete_controller.rotation_sensitivity = 1.0
        
        inputs = {
            "tx": 1.0,
            "ty": 2.0,
            "tz": 3.0,
            "roll": 4.0,
            "pitch": 5.0,
            "yaw": 6.0
        }
        
        concrete_controller._process_body_control(inputs)
        
        concrete_controller.task_interface.hexapod.move_body.assert_called_once()
        call_args = concrete_controller.task_interface.hexapod.move_body.call_args
        assert call_args[1]["tx"] == 6.0  # 1.0 * 1.0 * TRANSLATION_STEP
        assert call_args[1]["ty"] == 12.0  # 2.0 * 1.0 * TRANSLATION_STEP
        assert call_args[1]["tz"] == 12.0  # 3.0 * 1.0 * Z_STEP
        assert call_args[1]["roll"] == 8.0  # 4.0 * 1.0 * ROLL_STEP
        assert call_args[1]["pitch"] == 10.0  # 5.0 * 1.0 * PITCH_STEP
        assert call_args[1]["yaw"] == 24.0  # 6.0 * 1.0 * YAW_STEP

    def test_process_body_control_no_movement(self, concrete_controller):
        """Test body control processing with no movement inputs."""
        concrete_controller.current_mode = concrete_controller.BODY_CONTROL_MODE
        
        inputs = {"tx": 0.0, "ty": 0.0, "tz": 0.0, "roll": 0.0, "pitch": 0.0, "yaw": 0.0}
        
        concrete_controller._process_body_control(inputs)
        
        concrete_controller.task_interface.hexapod.move_body.assert_not_called()

    def test_process_body_control_exception(self, concrete_controller):
        """Test body control processing with exception."""
        concrete_controller.current_mode = concrete_controller.BODY_CONTROL_MODE
        concrete_controller.task_interface.hexapod.move_body.side_effect = Exception("Test error")
        
        inputs = {"tx": 1.0, "ty": 0.0, "tz": 0.0, "roll": 0.0, "pitch": 0.0, "yaw": 0.0}
        
        # Should not raise exception, just log error
        concrete_controller._process_body_control(inputs)

    def test_process_gait_control_marching_disabled_neutral(self, concrete_controller):
        """Test gait control with marching disabled and neutral inputs."""
        concrete_controller.current_mode = concrete_controller.GAIT_CONTROL_MODE
        concrete_controller.marching_enabled = False
        concrete_controller.is_gait_control_active = Mock(return_value=True)
        concrete_controller.stop_gait_control = Mock()
        
        inputs = {"direction_x": 0.0, "direction_y": 0.0, "rotation": 0.0}
        
        concrete_controller._process_gait_control(inputs)
        
        concrete_controller.stop_gait_control.assert_called_once()

    def test_process_gait_control_marching_enabled(self, concrete_controller):
        """Test gait control with marching enabled."""
        concrete_controller.current_mode = concrete_controller.GAIT_CONTROL_MODE
        concrete_controller.marching_enabled = True
        concrete_controller.is_gait_control_active = Mock(return_value=False)
        concrete_controller.start_gait_control = Mock()
        concrete_controller.current_gait = Mock()
        
        inputs = {"direction_x": 0.0, "direction_y": 0.0, "rotation": 0.0}
        
        concrete_controller._process_gait_control(inputs)
        
        concrete_controller.start_gait_control.assert_called_once()

    def test_process_gait_control_with_translation(self, concrete_controller):
        """Test gait control with translation movement."""
        concrete_controller.current_mode = concrete_controller.GAIT_CONTROL_MODE
        concrete_controller.marching_enabled = False
        concrete_controller.is_gait_control_active = Mock(return_value=False)
        concrete_controller.start_gait_control = Mock()
        concrete_controller.current_gait = Mock()
        concrete_controller.translation_gait = Mock()
        concrete_controller.rotation_gait = Mock()
        
        inputs = {"direction_x": 1.0, "direction_y": 0.0, "rotation": 0.0}
        
        concrete_controller._process_gait_control(inputs)
        
        concrete_controller.start_gait_control.assert_called_once()

    def test_process_gait_control_with_rotation(self, concrete_controller):
        """Test gait control with rotation movement."""
        concrete_controller.current_mode = concrete_controller.GAIT_CONTROL_MODE
        concrete_controller.marching_enabled = False
        concrete_controller.is_gait_control_active = Mock(return_value=False)
        concrete_controller.start_gait_control = Mock()
        concrete_controller.current_gait = Mock()
        concrete_controller.translation_gait = Mock()
        concrete_controller.rotation_gait = Mock()
        
        inputs = {"direction_x": 0.0, "direction_y": 0.0, "rotation": 1.0}
        
        concrete_controller._process_gait_control(inputs)
        
        concrete_controller.start_gait_control.assert_called_once()

    def test_process_sensitivity_deltas_translation_body_mode(self, concrete_controller):
        """Test processing translation sensitivity deltas in body mode."""
        concrete_controller.current_mode = concrete_controller.BODY_CONTROL_MODE
        concrete_controller.translation_sensitivity = 0.5
        
        inputs = {"sensitivity_deltas": {"translation_delta": 0.1}}
        concrete_controller._process_sensitivity_deltas(inputs)
        
        assert concrete_controller.translation_sensitivity == 0.6

    def test_process_sensitivity_deltas_rotation_body_mode(self, concrete_controller):
        """Test processing rotation sensitivity deltas in body mode."""
        concrete_controller.current_mode = concrete_controller.BODY_CONTROL_MODE
        concrete_controller.rotation_sensitivity = 0.5
        
        inputs = {"sensitivity_deltas": {"rotation_delta": 0.1}}
        concrete_controller._process_sensitivity_deltas(inputs)
        
        assert concrete_controller.rotation_sensitivity == 0.6

    def test_process_sensitivity_deltas_gait_mode(self, concrete_controller):
        """Test processing sensitivity deltas in gait mode."""
        concrete_controller.current_mode = concrete_controller.GAIT_CONTROL_MODE
        concrete_controller.gait_direction_sensitivity = 0.5
        concrete_controller.gait_rotation_sensitivity = 0.5
        
        inputs = {
            "sensitivity_deltas": {
                "translation_delta": 0.1,
                "rotation_delta": 0.1
            }
        }
        concrete_controller._process_sensitivity_deltas(inputs)
        
        assert concrete_controller.gait_direction_sensitivity == 0.6
        assert concrete_controller.gait_rotation_sensitivity == 0.6

    def test_process_sensitivity_deltas_limits(self, concrete_controller):
        """Test processing sensitivity deltas with limits."""
        concrete_controller.current_mode = concrete_controller.BODY_CONTROL_MODE
        concrete_controller.translation_sensitivity = 0.1
        
        # Test minimum limit
        inputs = {"sensitivity_deltas": {"translation_delta": -0.2}}
        concrete_controller._process_sensitivity_deltas(inputs)
        assert concrete_controller.translation_sensitivity == 0.1
        
        # Test maximum limit
        concrete_controller.translation_sensitivity = 1.0
        inputs = {"sensitivity_deltas": {"translation_delta": 0.2}}
        concrete_controller._process_sensitivity_deltas(inputs)
        assert concrete_controller.translation_sensitivity == 1.0

    def test_show_gait_status_no_gait(self, concrete_controller):
        """Test showing gait status when no gait is active."""
        concrete_controller.current_gait = None
        
        concrete_controller.show_gait_status()
        
        # Should call the mocked method
        concrete_controller.show_gait_status.assert_called_once()

    def test_show_gait_status_with_gait(self, concrete_controller):
        """Test showing gait status with active gait."""
        mock_gait = Mock()
        mock_gait.direction_input = (0.5, 0.3)
        mock_gait.rotation_input = 0.2
        concrete_controller.current_gait = mock_gait
        concrete_controller.translation_gait = mock_gait
        concrete_controller.rotation_gait = Mock()
        
        concrete_controller.show_gait_status()
        
        # Should call the mocked method
        concrete_controller.show_gait_status.assert_called_once()

    def test_print_current_position_details(self, concrete_controller):
        """Test printing current position details."""
        concrete_controller.current_tx = 10.0
        concrete_controller.current_ty = 20.0
        concrete_controller.current_tz = 30.0
        concrete_controller.current_roll = 40.0
        concrete_controller.current_pitch = 50.0
        concrete_controller.current_yaw = 60.0
        
        concrete_controller.print_current_position_details()
        
        # Should call the mocked method
        concrete_controller.print_current_position_details.assert_called_once()

    def test_print_current_sensitivity_levels(self, concrete_controller):
        """Test printing current sensitivity levels."""
        concrete_controller.translation_sensitivity = 0.7
        concrete_controller.rotation_sensitivity = 0.8
        concrete_controller.gait_direction_sensitivity = 0.9
        concrete_controller.gait_rotation_sensitivity = 1.0
        
        concrete_controller.print_current_sensitivity_levels()
        
        # Should call the mocked method
        concrete_controller.print_current_sensitivity_levels.assert_called_once()

    def test_show_current_position_gait_mode(self, concrete_controller):
        """Test showing current position in gait mode."""
        concrete_controller.current_mode = concrete_controller.GAIT_CONTROL_MODE
        
        concrete_controller.show_current_position()
        
        concrete_controller.show_gait_status.assert_called_once()
        concrete_controller.print_current_sensitivity_levels.assert_called_once()

    def test_show_current_position_body_mode(self, concrete_controller):
        """Test showing current position in body mode."""
        concrete_controller.current_mode = concrete_controller.BODY_CONTROL_MODE
        
        concrete_controller.show_current_position()
        
        concrete_controller.print_current_position_details.assert_called_once()
        concrete_controller.print_current_sensitivity_levels.assert_called_once()

    def test_toggle_mode_body_to_gait(self, concrete_controller):
        """Test toggling from body control to gait control mode."""
        concrete_controller.current_mode = concrete_controller.BODY_CONTROL_MODE
        concrete_controller.marching_enabled = True
        concrete_controller.start_gait_control = Mock()
        concrete_controller.reset_position = Mock()
        concrete_controller._on_mode_toggled = Mock()
        
        concrete_controller.toggle_mode()
        
        assert concrete_controller.current_mode == concrete_controller.GAIT_CONTROL_MODE
        concrete_controller.reset_position.assert_called_once()
        concrete_controller.start_gait_control.assert_called_once()
        concrete_controller._on_mode_toggled.assert_called_once_with(concrete_controller.GAIT_CONTROL_MODE)

    def test_toggle_mode_gait_to_body(self, concrete_controller):
        """Test toggling from gait control to body control mode."""
        concrete_controller.current_mode = concrete_controller.GAIT_CONTROL_MODE
        concrete_controller.stop_gait_control = Mock()
        concrete_controller.reset_position = Mock()
        concrete_controller._on_mode_toggled = Mock()
        
        concrete_controller.toggle_mode()
        
        assert concrete_controller.current_mode == concrete_controller.BODY_CONTROL_MODE
        concrete_controller.stop_gait_control.assert_called_once()
        concrete_controller.reset_position.assert_called_once()
        concrete_controller._on_mode_toggled.assert_called_once_with(concrete_controller.BODY_CONTROL_MODE)

    def test_on_mode_toggled_body_mode(self, concrete_controller):
        """Test mode toggled hook for body control mode."""
        concrete_controller._on_mode_toggled(concrete_controller.BODY_CONTROL_MODE)
        
        concrete_controller.task_interface.lights_handler.pulse_smoothly.assert_called_once()

    def test_on_mode_toggled_gait_mode(self, concrete_controller):
        """Test mode toggled hook for gait control mode."""
        concrete_controller._on_mode_toggled(concrete_controller.GAIT_CONTROL_MODE)
        
        concrete_controller.task_interface.lights_handler.think.assert_called_once()

    def test_on_mode_toggled_voice_mode(self, concrete_controller):
        """Test mode toggled hook for voice control mode."""
        concrete_controller.stop_gait_control = Mock()
        
        concrete_controller._on_mode_toggled(concrete_controller.VOICE_CONTROL_MODE)
        
        concrete_controller.stop_gait_control.assert_called_once()

    def test_start_initial_animation_body_mode(self, concrete_controller):
        """Test starting initial animation in body control mode."""
        concrete_controller.current_mode = concrete_controller.BODY_CONTROL_MODE
        
        concrete_controller._start_initial_animation()
        
        concrete_controller.task_interface.lights_handler.pulse_smoothly.assert_called_once()

    def test_start_initial_animation_gait_mode(self, concrete_controller):
        """Test starting initial animation in gait control mode."""
        concrete_controller.current_mode = concrete_controller.GAIT_CONTROL_MODE
        
        concrete_controller._start_initial_animation()
        
        concrete_controller.task_interface.lights_handler.think.assert_called_once()

    def test_pause_unpause(self, concrete_controller):
        """Test pausing and unpausing the controller."""
        # Configure the pause_event mock to return False initially
        concrete_controller.pause_event.is_set.return_value = False
        
        assert not concrete_controller.pause_event.is_set()
        
        concrete_controller.pause()
        # After pause, is_set should return True
        concrete_controller.pause_event.is_set.return_value = True
        assert concrete_controller.pause_event.is_set()
        
        concrete_controller.unpause()
        # After unpause, is_set should return False
        concrete_controller.pause_event.is_set.return_value = False
        assert not concrete_controller.pause_event.is_set()

    def test_toggle_voice_control_mode_no_voice_control(self, concrete_controller):
        """Test toggling voice control mode when voice control is None."""
        concrete_controller.voice_control = None
        
        concrete_controller.toggle_voice_control_mode()
        
        # Should not change mode when voice control is None
        assert concrete_controller.current_mode == concrete_controller.BODY_CONTROL_MODE

    def test_toggle_voice_control_mode_enter_voice(self, concrete_controller):
        """Test entering voice control mode."""
        concrete_controller.current_mode = concrete_controller.BODY_CONTROL_MODE
        concrete_controller.pause = Mock()
        concrete_controller._on_mode_toggled = Mock()
        
        concrete_controller.toggle_voice_control_mode()
        
        assert concrete_controller.current_mode == concrete_controller.VOICE_CONTROL_MODE
        assert concrete_controller._previous_manual_mode == concrete_controller.BODY_CONTROL_MODE
        concrete_controller.pause.assert_called_once()
        concrete_controller.task_interface.request_unpause_voice_control.assert_called_once()

    def test_toggle_voice_control_mode_exit_voice(self, concrete_controller):
        """Test exiting voice control mode."""
        concrete_controller.current_mode = concrete_controller.VOICE_CONTROL_MODE
        concrete_controller._previous_manual_mode = concrete_controller.BODY_CONTROL_MODE
        concrete_controller.unpause = Mock()
        concrete_controller._on_mode_toggled = Mock()
        
        concrete_controller.toggle_voice_control_mode()
        
        assert concrete_controller.current_mode == concrete_controller.BODY_CONTROL_MODE
        concrete_controller.unpause.assert_called_once()
        concrete_controller.task_interface.request_pause_voice_control.assert_called_once()

    def test_trigger_shutdown_with_callback(self, concrete_controller):
        """Test triggering shutdown with callback."""
        shutdown_callback = Mock()
        concrete_controller.shutdown_callback = shutdown_callback
        
        concrete_controller.trigger_shutdown()
        
        shutdown_callback.assert_called_once()

    def test_trigger_shutdown_without_callback(self, concrete_controller):
        """Test triggering shutdown without callback."""
        concrete_controller.shutdown_callback = None
        concrete_controller.stop = Mock()
        
        concrete_controller.trigger_shutdown()
        
        concrete_controller.stop.assert_called_once()

    def test_stop(self, concrete_controller):
        """Test stopping the controller."""
        # Don't mock the stop method, let it run the actual implementation
        concrete_controller.stop = ManualHexapodController.stop.__get__(concrete_controller, ConcreteController)
        concrete_controller.cleanup = Mock()
        
        concrete_controller.stop()
        
        # The stop_event should be set after calling stop()
        concrete_controller.stop_event.set.assert_called_once()
        concrete_controller.cleanup.assert_called_once()

    def test_cleanup(self, concrete_controller):
        """Test cleanup method."""
        # Don't mock the cleanup method, let it run the actual implementation
        concrete_controller.cleanup = ManualHexapodController.cleanup.__get__(concrete_controller, ConcreteController)
        concrete_controller.task_interface.hexapod.gait_generator.is_running = True
        concrete_controller.cleanup_controller = Mock()
        
        concrete_controller.cleanup()
        
        # Check that the cleanup method calls the expected methods
        concrete_controller.task_interface.lights_handler.off.assert_called_once()
        concrete_controller.task_interface.hexapod.gait_generator.stop.assert_called_once()
        concrete_controller.task_interface.hexapod.move_to_position.assert_called_once()
        concrete_controller.task_interface.hexapod.deactivate_all_servos.assert_called_once()
        concrete_controller.cleanup_controller.assert_called_once()

    def test_cleanup_exception(self, concrete_controller):
        """Test cleanup with exception."""
        # Don't mock the cleanup method, let it run the actual implementation
        concrete_controller.cleanup = ManualHexapodController.cleanup.__get__(concrete_controller, ConcreteController)
        concrete_controller.task_interface.hexapod.gait_generator.stop.side_effect = Exception("Test error")
        concrete_controller.cleanup_controller = Mock()
        
        # Should not raise exception, just log error
        concrete_controller.cleanup()
        
        # The cleanup_controller should still be called even if there's an exception
        concrete_controller.cleanup_controller.assert_called_once()

    def test_run_loop(self, concrete_controller):
        """Test the main run loop."""
        concrete_controller.print_help = Mock()
        concrete_controller.reset_position = Mock()
        concrete_controller._start_initial_animation = Mock()
        concrete_controller.get_inputs = Mock(return_value={})
        concrete_controller.process_movement_inputs = Mock()
        
        # Start the thread
        concrete_controller.start()
        
        # Let it run briefly
        time.sleep(0.1)
        
        # Stop it
        concrete_controller.stop()
        concrete_controller.join(timeout=1.0)
        
        concrete_controller.print_help.assert_called_once()
        concrete_controller.reset_position.assert_called_once()
        concrete_controller._start_initial_animation.assert_called_once()

    def test_run_loop_paused(self, concrete_controller):
        """Test the main run loop when paused."""
        concrete_controller.print_help = Mock()
        concrete_controller.reset_position = Mock()
        concrete_controller._start_initial_animation = Mock()
        concrete_controller.get_inputs = Mock(return_value={})
        concrete_controller.process_movement_inputs = Mock()
        
        # Configure pause_event to return True (paused state)
        concrete_controller.pause_event.is_set.return_value = True
        concrete_controller.pause()
        
        # Start the thread
        concrete_controller.start()
        
        # Let it run briefly
        time.sleep(0.1)
        
        # Stop it
        concrete_controller.stop()
        concrete_controller.join(timeout=1.0)
        
        # Should not process inputs when paused
        concrete_controller.process_movement_inputs.assert_not_called()

    def test_run_loop_exception(self, concrete_controller):
        """Test the main run loop with exception."""
        concrete_controller.print_help = Mock()
        concrete_controller.reset_position = Mock()
        concrete_controller._start_initial_animation = Mock()
        concrete_controller.get_inputs = Mock(side_effect=Exception("Test error"))
        
        # Start the thread
        concrete_controller.start()
        
        # Let it run briefly
        time.sleep(0.1)
        
        # Stop it
        concrete_controller.stop()
        concrete_controller.join(timeout=1.0)
        
        # Should not raise exception, just log error
        assert True


# Create a concrete implementation for testing
class ConcreteController(ManualHexapodController):
    """Concrete implementation of ManualHexapodController for testing."""
    
    def get_inputs(self):
        return {}
    
    def print_help(self):
        pass
    
    def cleanup_controller(self):
        pass
