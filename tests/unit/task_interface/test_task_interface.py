"""
Unit tests for task interface system.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock, call
from types import MethodType

from hexapod.task_interface.task_interface import TaskInterface
from hexapod.robot import PredefinedPosition
from hexapod.lights import ColorRGB


class TestTaskInterface:
    """Test cases for TaskInterface class."""

    @pytest.fixture
    def mock_hexapod(self):
        """Mock hexapod instance for testing."""
        hexapod = MagicMock()
        hexapod.leg_to_led = MagicMock()
        hexapod.gait_generator = MagicMock()
        hexapod.gait_generator.is_gait_running.return_value = False
        hexapod.move_to_position = MagicMock()
        hexapod.wait_until_motion_complete = MagicMock()
        hexapod.deactivate_all_servos = MagicMock()
        hexapod.set_all_servos_speed = MagicMock()
        hexapod.set_all_servos_accel = MagicMock()
        return hexapod

    @pytest.fixture
    def mock_lights_handler(self):
        """Mock lights handler for testing."""
        lights_handler = MagicMock()
        lights_handler.listen_wakeword = MagicMock()
        lights_handler.off = MagicMock()
        lights_handler.set_brightness = MagicMock()
        lights_handler.rainbow = MagicMock()
        lights_handler.pulse_smoothly = MagicMock()
        lights_handler.shutdown = MagicMock()
        lights_handler.set_single_color = MagicMock()
        lights_handler.police = MagicMock()
        lights_handler.lights = MagicMock()
        lights_handler.lights.num_led = 10
        return lights_handler

    @pytest.fixture
    def mock_button_handler(self):
        """Mock button handler for testing."""
        button_handler = MagicMock()
        button_handler.cleanup = MagicMock()
        return button_handler

    @pytest.fixture
    def mock_voice_control(self):
        """Mock voice control for testing."""
        voice_control = MagicMock()
        voice_control.get_recording_status.return_value = {"is_recording": False}
        voice_control.start_recording.return_value = "test_recording.wav"
        voice_control.stop_recording.return_value = "test_recording.wav"
        return voice_control

    @pytest.fixture
    def task_interface(self, mock_hexapod, mock_lights_handler, mock_button_handler):
        """Create TaskInterface instance with mocked dependencies."""
        with (
            patch(
                "hexapod.task_interface.task_interface.Hexapod",
                return_value=mock_hexapod,
            ),
            patch(
                "hexapod.task_interface.task_interface.LightsInteractionHandler",
                return_value=mock_lights_handler,
            ),
            patch(
                "hexapod.task_interface.task_interface.ButtonHandler",
                return_value=mock_button_handler,
            ),
            patch("hexapod.task_interface.task_interface.StatusReporter"),
        ):

            interface = TaskInterface()
            interface.hexapod = mock_hexapod
            interface.lights_handler = mock_lights_handler
            interface.button_handler = mock_button_handler
            return interface

    def test_init_default_parameters(self, task_interface):
        """Test TaskInterface initialization with default parameters."""
        assert task_interface.hexapod is not None
        assert task_interface.lights_handler is not None
        assert task_interface.voice_control is None
        assert task_interface.task is None
        assert task_interface.voice_control_context_info is None
        assert task_interface._last_command is None
        assert task_interface.status_reporter is not None
        assert task_interface._last_args is None
        assert task_interface._last_kwargs is None
        assert task_interface.voice_control_paused_event is not None
        assert task_interface.external_control_paused_event is not None
        assert task_interface.button_handler is not None
        assert task_interface.task_complete_callback is None

    def test_init_custom_parameters(
        self, mock_hexapod, mock_lights_handler, mock_button_handler
    ):
        """Test TaskInterface initialization with custom parameters."""
        with (
            patch(
                "hexapod.task_interface.task_interface.Hexapod",
                return_value=mock_hexapod,
            ),
            patch(
                "hexapod.task_interface.task_interface.LightsInteractionHandler",
                return_value=mock_lights_handler,
            ),
            patch(
                "hexapod.task_interface.task_interface.ButtonHandler",
                return_value=mock_button_handler,
            ),
            patch("hexapod.task_interface.task_interface.StatusReporter"),
        ):

            interface = TaskInterface()

            # Test that all components are properly initialized
            assert interface.hexapod == mock_hexapod
            assert interface.lights_handler == mock_lights_handler
            assert interface.button_handler == mock_button_handler
            assert interface.voice_control is None
            assert interface.task is None

    def test_request_pause_voice_control(self, task_interface):
        """Test requesting to pause voice control."""
        assert not task_interface.voice_control_paused_event.is_set()

        task_interface.request_pause_voice_control()

        assert task_interface.voice_control_paused_event.is_set()

    def test_request_unpause_voice_control(self, task_interface):
        """Test requesting to unpause voice control."""
        task_interface.voice_control_paused_event.set()
        assert task_interface.voice_control_paused_event.is_set()

        task_interface.request_unpause_voice_control()

        assert not task_interface.voice_control_paused_event.is_set()

    def test_request_block_voice_control_pausing(self, task_interface):
        """Test requesting to block voice control pausing."""
        assert not task_interface.external_control_paused_event.is_set()

        task_interface.request_block_voice_control_pausing()

        assert task_interface.external_control_paused_event.is_set()

    def test_request_unblock_voice_control_pausing(self, task_interface):
        """Test requesting to unblock voice control pausing."""
        task_interface.external_control_paused_event.set()
        assert task_interface.external_control_paused_event.is_set()

        task_interface.request_unblock_voice_control_pausing()

        assert not task_interface.external_control_paused_event.is_set()

    def test_inject_hexapod_decorator(self, task_interface):
        """Test the inject_hexapod decorator."""

        def test_func(self, hexapod, arg1, arg2=None):
            return hexapod, arg1, arg2

        decorated_func = TaskInterface.inject_hexapod(test_func)
        result = decorated_func(task_interface, "test_arg", arg2="test_kwarg")

        assert result[0] == task_interface.hexapod
        assert result[1] == "test_arg"
        assert result[2] == "test_kwarg"

    def test_inject_lights_handler_decorator(self, task_interface):
        """Test the inject_lights_handler decorator."""

        def test_func(self, lights_handler, arg1, arg2=None):
            return lights_handler, arg1, arg2

        decorated_func = TaskInterface.inject_lights_handler(test_func)
        result = decorated_func(task_interface, "test_arg", arg2="test_kwarg")

        assert result[0] == task_interface.lights_handler
        assert result[1] == "test_arg"
        assert result[2] == "test_kwarg"

    def test_set_task_complete_callback(self, task_interface):
        """Test setting task complete callback."""

        def test_callback(task):
            return f"Task {task} completed"

        task_interface.set_task_complete_callback(test_callback)

        assert task_interface.task_complete_callback == test_callback

    def test_notify_task_completion(self, task_interface):
        """Test notifying task completion."""
        callback_called = []

        def test_callback(task):
            callback_called.append(task)

        task_interface.task_complete_callback = test_callback
        mock_task = MagicMock()
        mock_task.__class__.__name__ = "TestTask"

        task_interface._notify_task_completion(mock_task)

        assert callback_called == [mock_task]

    def test_notify_task_completion_no_callback(self, task_interface):
        """Test notifying task completion without callback."""
        mock_task = MagicMock()
        mock_task.__class__.__name__ = "TestTask"

        # Should not raise exception
        task_interface._notify_task_completion(mock_task)

    def test_notify_task_completion_special_tasks(self, task_interface):
        """Test notifying task completion for special tasks that unpause controls."""
        special_task_names = [
            "SoundSourceLocalizationTask",
            "FollowTask",
            "StreamODASAudioTask",
            "CompositeCalibrationTask",
        ]

        for task_name in special_task_names:
            mock_task = MagicMock()
            mock_task.__class__.__name__ = task_name
            task_interface.task = mock_task

            task_interface._notify_task_completion(mock_task)

            # Should clear the task
            assert task_interface.task is None

    def test_store_last_command(self, task_interface):
        """Test storing last command."""

        def test_func(arg1, arg2=None):
            return f"result_{arg1}_{arg2}"

        task_interface._store_last_command(test_func, "value1", arg2="value2")

        assert task_interface._last_command is not None
        assert task_interface._last_args == ("value1",)
        assert task_interface._last_kwargs == {"arg2": "value2"}

    def test_repeat_last_command(self, task_interface):
        """Test repeating last command."""

        def test_func():
            return "test_result"

        task_interface._last_command = test_func
        task_interface._last_args = ()
        task_interface._last_kwargs = {}

        # Mock the function to track calls
        task_interface._last_command = MagicMock()
        task_interface._last_command.return_value = "test_result"
        task_interface._last_command.__name__ = "test_func"  # Add __name__ attribute

        result = task_interface.repeat_last_command()

        task_interface._last_command.assert_called_once_with()

    def test_repeat_last_command_no_command(self, task_interface):
        """Test repeating last command when no command exists."""
        task_interface._last_command = None

        # Should not raise exception
        task_interface.repeat_last_command()

    def test_set_voice_control(self, task_interface, mock_voice_control):
        """Test setting voice control."""
        task_interface.set_voice_control(mock_voice_control)

        assert task_interface.voice_control == mock_voice_control
        assert task_interface._recording_available is True

    def test_start_recording(self, task_interface, mock_voice_control):
        """Test starting recording."""
        task_interface.voice_control = mock_voice_control
        task_interface._recording_available = True
        mock_voice_control.get_recording_status.return_value = {"is_recording": False}
        mock_voice_control.start_recording.return_value = "test.wav"

        task_interface.start_recording()

        mock_voice_control.start_recording.assert_called_once_with(duration=None)

    def test_start_recording_with_duration(self, task_interface, mock_voice_control):
        """Test starting recording with duration."""
        task_interface.voice_control = mock_voice_control
        task_interface._recording_available = True
        mock_voice_control.get_recording_status.return_value = {"is_recording": False}
        mock_voice_control.start_recording.return_value = "test.wav"

        task_interface.start_recording(duration=10.0)

        mock_voice_control.start_recording.assert_called_once_with(duration=10.0)

    def test_start_recording_not_available(self, task_interface):
        """Test starting recording when not available."""
        task_interface._recording_available = False

        # Should not raise exception
        task_interface.start_recording()

    def test_start_recording_no_voice_control(self, task_interface):
        """Test starting recording when no voice control."""
        task_interface.voice_control = None
        task_interface._recording_available = True

        # Should not raise exception
        task_interface.start_recording()

    def test_stop_recording(self, task_interface, mock_voice_control):
        """Test stopping recording."""
        task_interface.voice_control = mock_voice_control
        task_interface._recording_available = True
        mock_voice_control.stop_recording.return_value = "test.wav"

        task_interface.stop_recording()

        mock_voice_control.stop_recording.assert_called_once()

    def test_stop_recording_not_available(self, task_interface):
        """Test stopping recording when not available."""
        task_interface._recording_available = False

        # Should not raise exception
        task_interface.stop_recording()

    def test_stop_recording_no_voice_control(self, task_interface):
        """Test stopping recording when no voice control."""
        task_interface.voice_control = None
        task_interface._recording_available = True

        # Should not raise exception
        task_interface.stop_recording()

    def test_hexapod_help(self, task_interface):
        """Test hexapod help command."""
        task_interface.voice_control_context_info = "Test context info"

        task_interface.hexapod_help()

        task_interface.lights_handler.listen_wakeword.assert_called_once()

    def test_hexapod_help_no_context(self, task_interface):
        """Test hexapod help command without context info."""
        task_interface.voice_control_context_info = None

        task_interface.hexapod_help()

        task_interface.lights_handler.listen_wakeword.assert_called_once()

    def test_system_status(self, task_interface):
        """Test system status command."""
        mock_status = "Mock status report"
        task_interface.status_reporter.get_complete_status.return_value = mock_status

        task_interface.system_status()

        task_interface.status_reporter.get_complete_status.assert_called_once_with(
            task_interface.hexapod
        )
        task_interface.lights_handler.listen_wakeword.assert_called_once()

    def test_wake_up(self, task_interface):
        """Test wake up command."""
        task_interface.wake_up()

        task_interface.lights_handler.set_brightness.assert_called_once_with(50)
        task_interface.lights_handler.rainbow.assert_called_once()
        task_interface.hexapod.move_to_position.assert_called_once_with(
            PredefinedPosition.ZERO
        )
        task_interface.hexapod.wait_until_motion_complete.assert_called_once()

    def test_sleep(self, task_interface):
        """Test sleep command."""
        task_interface.sleep()

        task_interface.lights_handler.set_brightness.assert_called_once_with(5)
        task_interface.lights_handler.pulse_smoothly.assert_called_once()
        task_interface.hexapod.wait_until_motion_complete.assert_called_once()
        task_interface.hexapod.deactivate_all_servos.assert_called_once()

    def test_calibrate(self, task_interface):
        """Test calibrate command."""
        with patch(
            "hexapod.task_interface.task_interface.tasks.CompositeCalibrationTask"
        ) as mock_task_class:
            mock_task = MagicMock()
            mock_task_class.return_value = mock_task
            task_interface.task = mock_task

            task_interface.calibrate()

            mock_task_class.assert_called_once()
            mock_task.start.assert_called_once()

    def test_idle_stance(self, task_interface):
        """Test idle stance command."""
        task_interface.idle_stance()

        task_interface.hexapod.move_to_position.assert_called_once_with(
            PredefinedPosition.ZERO
        )
        task_interface.hexapod.wait_until_motion_complete.assert_called_once()
        task_interface.lights_handler.listen_wakeword.assert_called_once()

    def test_turn_lights_off(self, task_interface):
        """Test turning lights off."""
        task_interface.turn_lights("off")

        task_interface.lights_handler.off.assert_called_once()

    def test_turn_lights_on(self, task_interface):
        """Test turning lights on."""
        task_interface.turn_lights("on")

        task_interface.lights_handler.listen_wakeword.assert_called_once()

    def test_change_color(self, task_interface):
        """Test changing light color."""
        task_interface.change_color("red")

        task_interface.lights_handler.set_single_color.assert_called_once_with(
            ColorRGB.RED
        )

    def test_change_color_invalid(self, task_interface):
        """Test changing light color with invalid color."""
        task_interface.change_color("invalid")

        # Should not raise exception, just log error
        task_interface.lights_handler.set_single_color.assert_not_called()

    def test_set_brightness(self, task_interface):
        """Test setting brightness."""
        task_interface.set_brightness(75.0)

        task_interface.lights_handler.set_brightness.assert_called_once_with(75)
        task_interface.lights_handler.listen_wakeword.assert_called_once()

    def test_set_speed(self, task_interface):
        """Test setting speed."""
        task_interface.set_speed(50.0)

        task_interface.hexapod.set_all_servos_speed.assert_called_once_with(50)
        task_interface.lights_handler.listen_wakeword.assert_called_once()

    def test_set_accel(self, task_interface):
        """Test setting acceleration."""
        task_interface.set_accel(30.0)

        task_interface.hexapod.set_all_servos_accel.assert_called_once_with(30)
        task_interface.lights_handler.listen_wakeword.assert_called_once()

    def test_police(self, task_interface):
        """Test police lights command."""
        task_interface.police()

        task_interface.lights_handler.police.assert_called_once()

    def test_rainbow(self, task_interface):
        """Test rainbow lights command."""
        task_interface.rainbow()

        task_interface.lights_handler.rainbow.assert_called_once()

    def test_stop(self, task_interface):
        """Test stop command."""
        mock_task = MagicMock()
        task_interface.task = mock_task
        task_interface.hexapod.gait_generator.is_gait_running.return_value = True

        task_interface.stop()

        task_interface.hexapod.gait_generator.stop.assert_called_once()
        mock_task.stop_task.assert_called_once()
        task_interface.hexapod.move_to_position.assert_called_once_with(
            PredefinedPosition.ZERO
        )
        task_interface.hexapod.wait_until_motion_complete.assert_called_once()

    def test_stop_no_task(self, task_interface):
        """Test stop command with no active task."""
        task_interface.task = None

        task_interface.stop()

        task_interface.lights_handler.listen_wakeword.assert_called_once()

    def test_cleanup(self, task_interface):
        """Test cleanup functionality."""
        task_interface.cleanup()

        task_interface.button_handler.cleanup.assert_called_once()
        task_interface.lights_handler.off.assert_called_once()
        task_interface.hexapod.deactivate_all_servos.assert_called_once()

    def test_cleanup_with_voice_control(self, task_interface, mock_voice_control):
        """Test cleanup with voice control."""
        task_interface.voice_control = mock_voice_control

        task_interface.cleanup()

        task_interface.button_handler.cleanup.assert_called_once()
        task_interface.lights_handler.off.assert_called_once()
        task_interface.hexapod.deactivate_all_servos.assert_called_once()

    def test_march_in_place(self, task_interface):
        """Test march in place command."""
        with patch(
            "hexapod.task_interface.task_interface.tasks.MarchInPlaceTask"
        ) as mock_task_class:
            mock_task = MagicMock()
            mock_task_class.return_value = mock_task
            task_interface.task = mock_task

            task_interface.march_in_place()

            mock_task_class.assert_called_once()
            mock_task.start.assert_called_once()

    def test_march_in_place_with_duration(self, task_interface):
        """Test march in place command with duration."""
        with patch(
            "hexapod.task_interface.task_interface.tasks.MarchInPlaceTask"
        ) as mock_task_class:
            mock_task = MagicMock()
            mock_task_class.return_value = mock_task
            task_interface.task = mock_task

            task_interface.march_in_place(duration=10.0)

            # Check that the task class was called with the right arguments
            mock_task_class.assert_called_once()
            call_args = mock_task_class.call_args
            assert call_args[0][0] == task_interface.hexapod
            assert call_args[0][1] == task_interface.lights_handler
            assert call_args[1]["duration"] == 10.0
            assert callable(call_args[1]["callback"])  # Check that callback is callable
            mock_task.start.assert_called_once()

    def test_move(self, task_interface):
        """Test move command."""
        with patch(
            "hexapod.task_interface.task_interface.tasks.MoveTask"
        ) as mock_task_class:
            mock_task = MagicMock()
            mock_task_class.return_value = mock_task
            task_interface.task = mock_task

            task_interface.move("forward")

            mock_task_class.assert_called_once()
            mock_task.start.assert_called_once()

    def test_move_with_cycles(self, task_interface):
        """Test move command with cycles."""
        with patch(
            "hexapod.task_interface.task_interface.tasks.MoveTask"
        ) as mock_task_class:
            mock_task = MagicMock()
            mock_task_class.return_value = mock_task
            task_interface.task = mock_task

            task_interface.move("forward", cycles=5)

            # Check that the task class was called with the right arguments
            mock_task_class.assert_called_once()
            call_args = mock_task_class.call_args
            assert call_args[0][0] == task_interface.hexapod
            assert call_args[0][1] == task_interface.lights_handler
            assert call_args[0][2] == "forward"
            assert call_args[1]["cycles"] == 5
            assert call_args[1]["duration"] is None
            assert callable(call_args[1]["callback"])  # Check that callback is callable
            mock_task.start.assert_called_once()

    def test_rotate(self, task_interface):
        """Test rotate command."""
        with patch(
            "hexapod.task_interface.task_interface.tasks.RotateTask"
        ) as mock_task_class:
            mock_task = MagicMock()
            mock_task_class.return_value = mock_task
            task_interface.task = mock_task

            task_interface.rotate()

            mock_task_class.assert_called_once()
            mock_task.start.assert_called_once()

    def test_rotate_with_angle(self, task_interface):
        """Test rotate command with angle."""
        with patch(
            "hexapod.task_interface.task_interface.tasks.RotateTask"
        ) as mock_task_class:
            mock_task = MagicMock()
            mock_task_class.return_value = mock_task
            task_interface.task = mock_task

            task_interface.rotate(angle=90.0, turn_direction="left")

            # Check that the task class was called with the right arguments
            mock_task_class.assert_called_once()
            call_args = mock_task_class.call_args
            assert call_args[0][0] == task_interface.hexapod
            assert call_args[0][1] == task_interface.lights_handler
            assert call_args[1]["angle"] == 90.0
            assert call_args[1]["turn_direction"] == "left"
            assert call_args[1]["cycles"] is None
            assert call_args[1]["duration"] is None
            assert callable(call_args[1]["callback"])  # Check that callback is callable
            mock_task.start.assert_called_once()

    def test_follow(self, task_interface):
        """Test follow command."""
        with (
            patch(
                "hexapod.task_interface.task_interface.tasks.FollowTask"
            ) as mock_task_class,
            patch(
                "hexapod.odas.odas_doa_ssl_processor.ODASDoASSLProcessor"
            ) as mock_odas_class,
        ):
            mock_task = MagicMock()
            mock_task_class.return_value = mock_task
            task_interface.task = mock_task

            # Should not raise exception
            task_interface.follow()

            mock_task_class.assert_called_once()
            mock_task.start.assert_called_once()

    def test_sound_source_localization(self, task_interface):
        """Test sound source localization command."""
        with (
            patch(
                "hexapod.task_interface.task_interface.tasks.SoundSourceLocalizationTask"
            ) as mock_task_class,
            patch(
                "hexapod.odas.odas_doa_ssl_processor.ODASDoASSLProcessor"
            ) as mock_odas_class,
        ):
            mock_task = MagicMock()
            mock_task_class.return_value = mock_task
            task_interface.task = mock_task

            # Should not raise exception
            task_interface.sound_source_localization()

            mock_task_class.assert_called_once()
            mock_task.start.assert_called_once()

    def test_stream_odas_audio(self, task_interface):
        """Test stream ODAS audio command."""
        with (
            patch(
                "hexapod.task_interface.task_interface.tasks.StreamODASAudioTask"
            ) as mock_task_class,
            patch(
                "hexapod.odas.odas_doa_ssl_processor.ODASDoASSLProcessor"
            ) as mock_odas_class,
        ):
            mock_task = MagicMock()
            mock_task_class.return_value = mock_task
            task_interface.task = mock_task

            # Should not raise exception
            task_interface.stream_odas_audio()

            mock_task_class.assert_called_once()
            mock_task.start.assert_called_once()

    def test_stream_odas_audio_with_type(self, task_interface):
        """Test stream ODAS audio command with stream type."""
        with (
            patch(
                "hexapod.task_interface.task_interface.tasks.StreamODASAudioTask"
            ) as mock_task_class,
            patch(
                "hexapod.odas.odas_doa_ssl_processor.ODASDoASSLProcessor"
            ) as mock_odas_class,
        ):
            mock_task = MagicMock()
            mock_task_class.return_value = mock_task
            task_interface.task = mock_task

            # Should not raise exception
            task_interface.stream_odas_audio(stream_type="mixed")

            mock_task_class.assert_called_once()
            mock_task.start.assert_called_once()

    def test_sit_up(self, task_interface):
        """Test sit up command."""
        with patch(
            "hexapod.task_interface.task_interface.tasks.SitUpTask"
        ) as mock_task_class:
            mock_task = MagicMock()
            mock_task_class.return_value = mock_task
            task_interface.task = mock_task

            task_interface.sit_up()

            mock_task_class.assert_called_once()
            mock_task.start.assert_called_once()

    def test_helix(self, task_interface):
        """Test helix command."""
        with patch(
            "hexapod.task_interface.task_interface.tasks.HelixTask"
        ) as mock_task_class:
            mock_task = MagicMock()
            mock_task_class.return_value = mock_task
            task_interface.task = mock_task

            task_interface.helix()

            mock_task_class.assert_called_once()
            mock_task.start.assert_called_once()

    def test_say_hello(self, task_interface):
        """Test say hello command."""
        with patch(
            "hexapod.task_interface.task_interface.tasks.SayHelloTask"
        ) as mock_task_class:
            mock_task = MagicMock()
            mock_task_class.return_value = mock_task
            task_interface.task = mock_task

            task_interface.say_hello()

            mock_task_class.assert_called_once()
            mock_task.start.assert_called_once()

    def test_stop_task(self, task_interface):
        """Test stopping a task."""
        mock_task = MagicMock()
        mock_task.__class__.__name__ = "TestTask"
        task_interface.task = mock_task

        task_interface.stop_task()

        mock_task.stop_task.assert_called_once_with(timeout=5.0)

    def test_stop_task_special_tasks(self, task_interface):
        """Test stopping special tasks that need unpausing."""
        special_task_names = [
            "SoundSourceLocalizationTask",
            "FollowTask",
            "StreamODASAudioTask",
            "CompositeCalibrationTask",
        ]

        for task_name in special_task_names:
            mock_task = MagicMock()
            mock_task.__class__.__name__ = task_name
            task_interface.task = mock_task

            # Mock the unpause methods to track calls
            with (
                patch.object(
                    task_interface, "request_unpause_voice_control"
                ) as mock_unpause,
                patch.object(
                    task_interface, "request_unblock_voice_control_pausing"
                ) as mock_unblock,
            ):

                task_interface.stop_task()

                mock_task.stop_task.assert_called_once_with(timeout=5.0)
                # Should call unpause methods for special tasks
                mock_unpause.assert_called()
                mock_unblock.assert_called()

    def test_stop_task_no_task(self, task_interface):
        """Test stopping when no task is active."""
        task_interface.task = None

        # Should not raise exception
        task_interface.stop_task()

    def test_stop_task_exception(self, task_interface):
        """Test stopping task when exception occurs."""
        mock_task = MagicMock()
        mock_task.__class__.__name__ = "TestTask"
        mock_task.stop_task.side_effect = Exception("Stop error")
        task_interface.task = mock_task

        # Should not raise exception, just log it
        task_interface.stop_task()

    def test_shut_down(self, task_interface):
        """Test shutdown command."""
        with (
            patch(
                "hexapod.task_interface.task_interface.NonBlockingConsoleInputHandler"
            ) as mock_input_class,
            patch(
                "hexapod.task_interface.task_interface.threading.Timer"
            ) as mock_timer_class,
            patch(
                "hexapod.task_interface.task_interface.threading.Thread"
            ) as mock_thread_class,
            patch("hexapod.task_interface.task_interface.rename_thread") as mock_rename,
        ):

            mock_input_handler = MagicMock()
            mock_input_class.return_value = mock_input_handler
            mock_timer = MagicMock()
            mock_timer_class.return_value = mock_timer
            mock_thread = MagicMock()
            mock_thread_class.return_value = mock_thread

            task_interface.shut_down()

            mock_input_class.assert_called_once()
            mock_input_handler.start.assert_called_once()
            mock_timer_class.assert_called_once()
            mock_timer.start.assert_called_once()
            mock_thread_class.assert_called_once()
            mock_thread.start.assert_called_once()

    def test_shut_down_exception(self, task_interface):
        """Test shutdown command with exception."""
        with patch(
            "hexapod.task_interface.task_interface.NonBlockingConsoleInputHandler"
        ) as mock_input_class:
            mock_input_class.side_effect = Exception("Input handler error")

            with pytest.raises(Exception, match="Input handler error"):
                task_interface.shut_down()

    def test_shutdown_monitor(self, task_interface):
        """Test shutdown monitor."""
        mock_timer = MagicMock()
        mock_timer.is_alive.return_value = False  # Timer not alive, so loop exits
        mock_input_handler = MagicMock()

        task_interface._shutdown_monitor(mock_timer, mock_input_handler)

        mock_timer.is_alive.assert_called()

    def test_shutdown_monitor_with_input(self, task_interface):
        """Test shutdown monitor with user input."""
        mock_timer = MagicMock()
        mock_timer.is_alive.side_effect = [
            True,
            False,
        ]  # First call returns True, then False
        mock_input_handler = MagicMock()
        mock_input_handler.get_input.return_value = "y"  # User input

        task_interface._shutdown_monitor(mock_timer, mock_input_handler)

        mock_timer.cancel.assert_called_once()
        mock_input_handler.shutdown.assert_called_once()

    def test_shutdown_monitor_no_input_handler(self, task_interface):
        """Test shutdown monitor with no input handler."""
        mock_timer = MagicMock()
        mock_timer.is_alive.return_value = True

        task_interface._shutdown_monitor(mock_timer, None)

        # Should break out of loop immediately
        mock_timer.is_alive.assert_called_once()

    def test_shutdown_monitor_exception(self, task_interface):
        """Test shutdown monitor with exception."""
        mock_timer = MagicMock()
        mock_timer.is_alive.side_effect = Exception("Timer error")
        mock_input_handler = MagicMock()

        # Should not raise exception, just log it
        task_interface._shutdown_monitor(mock_timer, mock_input_handler)

    def test_perform_shutdown(self, task_interface):
        """Test perform shutdown."""
        with patch("hexapod.task_interface.task_interface.os.system") as mock_system:
            task_interface._perform_shutdown(
                task_interface.hexapod, task_interface.lights_handler
            )

            task_interface.hexapod.deactivate_all_servos.assert_called_once()
            task_interface.lights_handler.off.assert_called_once()
            mock_system.assert_called_once_with("sudo shutdown now")

    def test_wake_up_exception(self, task_interface):
        """Test wake up command with exception."""
        task_interface.hexapod.move_to_position.side_effect = Exception("Move error")

        # Should not raise exception, just log it
        task_interface.wake_up()

    def test_sleep_exception(self, task_interface):
        """Test sleep command with exception."""
        task_interface.hexapod.wait_until_motion_complete.side_effect = Exception(
            "Wait error"
        )

        # Should not raise exception, just log it
        task_interface.sleep()

    def test_calibrate_exception(self, task_interface):
        """Test calibrate command with exception."""
        with patch(
            "hexapod.task_interface.task_interface.tasks.CompositeCalibrationTask"
        ) as mock_task_class:
            mock_task_class.side_effect = Exception("Calibration error")

            # Set a mock task to satisfy the @task decorator
            task_interface.task = MagicMock()

            # Should not raise exception, just log it
            task_interface.calibrate()

    def test_idle_stance_exception(self, task_interface):
        """Test idle stance command with exception."""
        task_interface.hexapod.move_to_position.side_effect = Exception("Move error")

        # Should not raise exception, just log it
        task_interface.idle_stance()

    def test_change_color_exception(self, task_interface):
        """Test change color command with exception."""
        with patch("hexapod.task_interface.task_interface.ColorRGB") as mock_color:
            mock_color.__getitem__.side_effect = Exception("Color error")

            # Should not raise exception, just log it
            with pytest.raises(Exception, match="Color error"):
                task_interface.change_color("invalid")

    def test_police_exception(self, task_interface):
        """Test police command with exception."""
        task_interface.lights_handler.police.side_effect = Exception("Police error")

        # Should not raise exception, just log it
        task_interface.police()

    def test_rainbow_exception(self, task_interface):
        """Test rainbow command with exception."""
        task_interface.lights_handler.rainbow.side_effect = Exception("Rainbow error")

        # Should not raise exception, just log it
        task_interface.rainbow()

    def test_stop_exception(self, task_interface):
        """Test stop command with exception."""
        mock_task = MagicMock()
        task_interface.task = mock_task
        task_interface.hexapod.gait_generator.is_gait_running.return_value = True
        mock_task.stop_task.side_effect = Exception("Stop error")

        # Should not raise exception, just log it
        task_interface.stop()

    def test_march_in_place_exception(self, task_interface):
        """Test march in place command with exception."""
        with patch(
            "hexapod.task_interface.task_interface.tasks.MarchInPlaceTask"
        ) as mock_task_class:
            mock_task_class.side_effect = Exception("March error")

            # Set a mock task to satisfy the @task decorator
            task_interface.task = MagicMock()

            # Should not raise exception, just log it
            task_interface.march_in_place()

    def test_move_exception(self, task_interface):
        """Test move command with exception."""
        with patch(
            "hexapod.task_interface.task_interface.tasks.MoveTask"
        ) as mock_task_class:
            mock_task_class.side_effect = Exception("Move error")

            # Set a mock task to satisfy the @task decorator
            task_interface.task = MagicMock()

            # Should not raise exception, just log it
            task_interface.move("forward")

    def test_rotate_exception(self, task_interface):
        """Test rotate command with exception."""
        with patch(
            "hexapod.task_interface.task_interface.tasks.RotateTask"
        ) as mock_task_class:
            mock_task_class.side_effect = Exception("Rotate error")

            # Set a mock task to satisfy the @task decorator
            task_interface.task = MagicMock()

            # Should not raise exception, just log it
            task_interface.rotate()

    def test_follow_exception(self, task_interface):
        """Test follow command with exception."""
        with (
            patch(
                "hexapod.task_interface.task_interface.tasks.FollowTask"
            ) as mock_task_class,
            patch(
                "hexapod.odas.odas_doa_ssl_processor.ODASDoASSLProcessor"
            ) as mock_odas_class,
        ):
            mock_task_class.side_effect = Exception("Follow error")

            # Set a mock task to satisfy the @task decorator
            task_interface.task = MagicMock()

            # Should not raise exception, just log it
            task_interface.follow()

    def test_sound_source_localization_exception(self, task_interface):
        """Test sound source localization command with exception."""
        with (
            patch(
                "hexapod.task_interface.task_interface.tasks.SoundSourceLocalizationTask"
            ) as mock_task_class,
            patch(
                "hexapod.odas.odas_doa_ssl_processor.ODASDoASSLProcessor"
            ) as mock_odas_class,
        ):
            mock_task_class.side_effect = Exception("SSL error")

            # Set a mock task to satisfy the @task decorator
            task_interface.task = MagicMock()

            # Should not raise exception, just log it
            task_interface.sound_source_localization()

    def test_stream_odas_audio_exception(self, task_interface):
        """Test stream ODAS audio command with exception."""
        with (
            patch(
                "hexapod.task_interface.task_interface.tasks.StreamODASAudioTask"
            ) as mock_task_class,
            patch(
                "hexapod.odas.odas_doa_ssl_processor.ODASDoASSLProcessor"
            ) as mock_odas_class,
        ):
            mock_task_class.side_effect = Exception("Stream error")

            # Set a mock task to satisfy the @task decorator
            task_interface.task = MagicMock()

            # Should not raise exception, just log it
            task_interface.stream_odas_audio()

    def test_sit_up_exception(self, task_interface):
        """Test sit up command with exception."""
        with patch(
            "hexapod.task_interface.task_interface.tasks.SitUpTask"
        ) as mock_task_class:
            mock_task_class.side_effect = Exception("Sit up error")

            # Set a mock task to satisfy the @task decorator
            task_interface.task = MagicMock()

            # Should not raise exception, just log it
            task_interface.sit_up()

    def test_helix_exception(self, task_interface):
        """Test helix command with exception."""
        with patch(
            "hexapod.task_interface.task_interface.tasks.HelixTask"
        ) as mock_task_class:
            mock_task_class.side_effect = Exception("Helix error")

            # Set a mock task to satisfy the @task decorator
            task_interface.task = MagicMock()

            # Should not raise exception, just log it
            task_interface.helix()

    def test_say_hello_exception(self, task_interface):
        """Test say hello command with exception."""
        with patch(
            "hexapod.task_interface.task_interface.tasks.SayHelloTask"
        ) as mock_task_class:
            mock_task_class.side_effect = Exception("Say hello error")

            # Set a mock task to satisfy the @task decorator
            task_interface.task = MagicMock()

            # Should not raise exception, just log it
            task_interface.say_hello()

    def test_start_recording_exception(self, task_interface, mock_voice_control):
        """Test start recording with exception."""
        task_interface.voice_control = mock_voice_control
        task_interface._recording_available = True
        mock_voice_control.get_recording_status.side_effect = Exception(
            "Recording error"
        )

        # Should not raise exception, just log it
        task_interface.start_recording()

    def test_stop_recording_exception(self, task_interface, mock_voice_control):
        """Test stop recording with exception."""
        task_interface.voice_control = mock_voice_control
        task_interface._recording_available = True
        mock_voice_control.stop_recording.side_effect = Exception(
            "Stop recording error"
        )

        # Should not raise exception, just log it
        task_interface.stop_recording()

    def test_start_recording_with_previous_recording(
        self, task_interface, mock_voice_control
    ):
        """Test start recording when a recording was already in progress."""
        task_interface.voice_control = mock_voice_control
        task_interface._recording_available = True
        mock_voice_control.get_recording_status.return_value = {"is_recording": True}
        mock_voice_control.start_recording.return_value = "new_recording.wav"

        task_interface.start_recording(duration=10.0)

        mock_voice_control.start_recording.assert_called_once_with(duration=10.0)

    def test_start_recording_with_previous_continuous_recording(
        self, task_interface, mock_voice_control
    ):
        """Test start recording when a continuous recording was already in progress."""
        task_interface.voice_control = mock_voice_control
        task_interface._recording_available = True
        mock_voice_control.get_recording_status.return_value = {"is_recording": True}
        mock_voice_control.start_recording.return_value = "new_recording.wav"

        task_interface.start_recording()  # No duration specified

        mock_voice_control.start_recording.assert_called_once_with(duration=None)

    def test_stop_recording_no_active_recording(
        self, task_interface, mock_voice_control
    ):
        """Test stop recording when no recording is active."""
        task_interface.voice_control = mock_voice_control
        task_interface._recording_available = True
        mock_voice_control.stop_recording.return_value = None  # No active recording

        task_interface.stop_recording()

        mock_voice_control.stop_recording.assert_called_once()

    def test_shutdown_monitor_with_sleep(self, task_interface):
        """Test shutdown monitor with sleep in the loop."""
        mock_timer = MagicMock()
        mock_timer.is_alive.side_effect = [True, True, False]  # Multiple iterations
        mock_input_handler = MagicMock()
        mock_input_handler.get_input.return_value = None  # No input

        with patch("hexapod.task_interface.task_interface.time.sleep") as mock_sleep:
            task_interface._shutdown_monitor(mock_timer, mock_input_handler)

            # Should have called sleep for each iteration
            assert mock_sleep.call_count >= 2
            mock_sleep.assert_called_with(0.1)
