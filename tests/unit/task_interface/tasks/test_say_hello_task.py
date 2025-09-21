"""Unit tests for SayHelloTask."""

import pytest
import math
from unittest.mock import Mock, patch
from hexapod.task_interface.tasks.say_hello_task import SayHelloTask


class TestSayHelloTask:
    """Test cases for SayHelloTask."""

    @pytest.fixture
    def mock_hexapod(self):
        """Create a mock hexapod."""
        hexapod = Mock()
        hexapod.current_leg_angles = {0: (10.0, 20.0, 30.0)}
        hexapod.move_leg_angles = Mock()
        hexapod.move_to_position = Mock()
        hexapod.wait_until_motion_complete = Mock()
        return hexapod

    @pytest.fixture
    def mock_lights_handler(self):
        """Create a mock lights handler."""
        return Mock()

    @pytest.fixture
    def say_hello_task(self, mock_hexapod, mock_lights_handler):
        """Create a SayHelloTask instance."""
        return SayHelloTask(mock_hexapod, mock_lights_handler)

    def test_init_default_parameters(self, mock_hexapod, mock_lights_handler):
        """Test initialization with default parameters."""
        task = SayHelloTask(mock_hexapod, mock_lights_handler)

        assert task.hexapod == mock_hexapod
        assert task.lights_handler == mock_lights_handler
        assert task.callback is None
        assert task.stop_event is not None
        assert not task.stop_event.is_set()

    def test_init_with_callback(self, mock_hexapod, mock_lights_handler):
        """Test initialization with callback."""
        callback = Mock()
        task = SayHelloTask(mock_hexapod, mock_lights_handler, callback=callback)

        assert task.callback == callback

    def test_execute_task_success(
        self, say_hello_task, mock_hexapod, mock_lights_handler
    ):
        """Test successful task execution."""
        with (
            patch("hexapod.task_interface.tasks.say_hello_task.logger") as mock_logger,
            patch.object(say_hello_task, "_perform_infinity_wave") as mock_perform,
        ):

            say_hello_task.execute_task()

            # Verify task sequence
            mock_logger.info.assert_any_call("SayHelloTask started")
            mock_hexapod.move_to_position.assert_called_once()
            mock_hexapod.wait_until_motion_complete.assert_called_once_with(
                say_hello_task.stop_event
            )
            mock_perform.assert_called_once()
            mock_logger.info.assert_any_call("SayHelloTask completed")

    def test_execute_task_stop_event_during_initial_movement(
        self, say_hello_task, mock_hexapod, mock_lights_handler
    ):
        """Test task execution when stop event is set during initial movement."""
        # Set stop event before initial movement
        say_hello_task.stop_event.set()

        with (
            patch("hexapod.task_interface.tasks.say_hello_task.logger") as mock_logger,
            patch.object(say_hello_task, "_perform_infinity_wave") as mock_perform,
        ):

            say_hello_task.execute_task()

            # Should still perform infinity wave (it's called before the stop event check)
            mock_perform.assert_called_once()
            mock_logger.info.assert_any_call("SayHelloTask completed")

    def test_execute_task_stop_event_during_infinity_wave(
        self, say_hello_task, mock_hexapod, mock_lights_handler
    ):
        """Test task execution when stop event is set during infinity wave."""
        with (
            patch("hexapod.task_interface.tasks.say_hello_task.logger") as mock_logger,
            patch.object(say_hello_task, "_perform_infinity_wave") as mock_perform,
        ):

            # Set stop event during infinity wave
            def side_effect():
                say_hello_task.stop_event.set()

            mock_perform.side_effect = side_effect

            say_hello_task.execute_task()

            # Should have started but stopped during infinity wave
            mock_perform.assert_called_once()
            mock_logger.info.assert_any_call("SayHelloTask completed")

    def test_execute_task_final_position(
        self, say_hello_task, mock_hexapod, mock_lights_handler
    ):
        """Test that task moves to final position."""
        with (
            patch("hexapod.task_interface.tasks.say_hello_task.logger"),
            patch.object(say_hello_task, "_perform_infinity_wave"),
        ):

            say_hello_task.execute_task()

            # Verify final position was still called
            from hexapod.robot import PredefinedPosition

            mock_hexapod.move_to_position.assert_called_with(
                PredefinedPosition.LOW_PROFILE
            )
            mock_hexapod.wait_until_motion_complete.assert_called_with(
                say_hello_task.stop_event
            )

    def test_execute_task_exception_handling(
        self, say_hello_task, mock_hexapod, mock_lights_handler
    ):
        """Test task execution with exception handling."""
        with (
            patch("hexapod.task_interface.tasks.say_hello_task.logger") as mock_logger,
            patch.object(
                say_hello_task,
                "_perform_infinity_wave",
                side_effect=Exception("Test error"),
            ),
        ):

            say_hello_task.execute_task()

            # Should log the exception
            mock_logger.exception.assert_called_with(
                "Say hello task failed: Test error"
            )

    def test_say_hello_task_minimal_implementation(
        self, mock_hexapod, mock_lights_handler
    ):
        """Test that SayHelloTask has minimal required implementation."""
        task = SayHelloTask(mock_hexapod, mock_lights_handler)

        # Should have required attributes
        assert hasattr(task, "hexapod")
        assert hasattr(task, "lights_handler")
        assert hasattr(task, "stop_event")
        assert hasattr(task, "execute_task")
        assert hasattr(task, "_perform_infinity_wave")

        # Should be callable
        assert callable(task.execute_task)
        assert callable(task._perform_infinity_wave)

    def test_stop_event_management(self, say_hello_task):
        """Test stop event management."""
        # Initially not set
        assert not say_hello_task.stop_event.is_set()

        # Can be set
        say_hello_task.stop_event.set()
        assert say_hello_task.stop_event.is_set()

        # Can be cleared
        say_hello_task.stop_event.clear()
        assert not say_hello_task.stop_event.is_set()

    def test_task_attributes(self, say_hello_task, mock_hexapod, mock_lights_handler):
        """Test task attributes are set correctly."""
        assert say_hello_task.hexapod == mock_hexapod
        assert say_hello_task.lights_handler == mock_lights_handler
        assert say_hello_task.stop_event is not None

    def test_perform_infinity_wave_success(self, say_hello_task, mock_hexapod):
        """Test successful infinity wave execution."""
        with (
            patch("hexapod.task_interface.tasks.say_hello_task.logger") as mock_logger,
            patch(
                "hexapod.task_interface.tasks.say_hello_task.time.sleep"
            ) as mock_sleep,
            patch("hexapod.task_interface.tasks.say_hello_task.time.time") as mock_time,
        ):

            # Mock time.time to return increasing values for the delay loop
            call_count = 0

            def time_side_effect():
                nonlocal call_count
                call_count += 1
                return call_count * 0.01  # Return increasing time values

            mock_time.side_effect = time_side_effect

            # Mock current leg angles
            mock_hexapod.current_leg_angles = {0: (10.0, 20.0, 30.0)}

            say_hello_task._perform_infinity_wave()

            # Verify logging
            mock_logger.info.assert_any_call(
                "Starting infinity wave motion using angle-based movement"
            )
            mock_logger.info.assert_any_call(
                "Original leg 0 angles: coxa=10.0°, femur=20.0°, tibia=30.0°"
            )
            mock_logger.info.assert_any_call("Returning leg 0 to original angles")

            # Verify leg movements
            assert (
                mock_hexapod.move_leg_angles.call_count >= 3
            )  # At least preparation, animation, and return
            mock_hexapod.wait_until_motion_complete.assert_called()

    def test_perform_infinity_wave_stop_event_during_preparation(
        self, say_hello_task, mock_hexapod
    ):
        """Test infinity wave stops during preparation phase."""
        with (
            patch("hexapod.task_interface.tasks.say_hello_task.logger") as mock_logger,
            patch(
                "hexapod.task_interface.tasks.say_hello_task.time.sleep"
            ) as mock_sleep,
            patch("hexapod.task_interface.tasks.say_hello_task.time.time") as mock_time,
        ):

            # Mock current leg angles
            mock_hexapod.current_leg_angles = {0: (10.0, 20.0, 30.0)}

            # Set stop event after first wait_until_motion_complete
            def side_effect(*args, **kwargs):
                say_hello_task.stop_event.set()
                return None

            mock_hexapod.wait_until_motion_complete.side_effect = side_effect

            say_hello_task._perform_infinity_wave()

            # Should log interruption during preparation
            mock_logger.info.assert_any_call(
                "Infinity wave task interrupted during preparation."
            )

    def test_perform_infinity_wave_stop_event_during_animation(
        self, say_hello_task, mock_hexapod
    ):
        """Test infinity wave stops during animation phase."""
        with (
            patch("hexapod.task_interface.tasks.say_hello_task.logger") as mock_logger,
            patch(
                "hexapod.task_interface.tasks.say_hello_task.time.sleep"
            ) as mock_sleep,
            patch("hexapod.task_interface.tasks.say_hello_task.time.time") as mock_time,
        ):

            # Mock current leg angles
            mock_hexapod.current_leg_angles = {0: (10.0, 20.0, 30.0)}

            # Mock time.time to return increasing values, then set stop event
            call_count = 0

            def time_side_effect():
                nonlocal call_count
                call_count += 1
                # Set stop event after the delay loop completes but before the final check
                if call_count == 20:  # After delay phase completes
                    say_hello_task.stop_event.set()
                return call_count * 0.01

            mock_time.side_effect = time_side_effect

            say_hello_task._perform_infinity_wave()

            # Should log interruption during animation (not delay)
            mock_logger.info.assert_any_call(
                "Infinity wave task interrupted during animation."
            )

    def test_perform_infinity_wave_stop_event_during_delay(
        self, say_hello_task, mock_hexapod
    ):
        """Test infinity wave stops during delay phase."""
        with (
            patch("hexapod.task_interface.tasks.say_hello_task.logger") as mock_logger,
            patch(
                "hexapod.task_interface.tasks.say_hello_task.time.sleep"
            ) as mock_sleep,
            patch("hexapod.task_interface.tasks.say_hello_task.time.time") as mock_time,
        ):

            # Mock current leg angles
            mock_hexapod.current_leg_angles = {0: (10.0, 20.0, 30.0)}

            # Mock time.time to simulate delay, then set stop event
            call_count = 0

            def time_side_effect():
                nonlocal call_count
                call_count += 1
                if call_count == 3:  # Set stop event during delay
                    say_hello_task.stop_event.set()
                return call_count * 0.01

            mock_time.side_effect = time_side_effect

            say_hello_task._perform_infinity_wave()

            # Should log interruption during delay
            mock_logger.info.assert_any_call(
                "Infinity wave task interrupted during delay."
            )

    def test_perform_infinity_wave_angle_calculations(
        self, say_hello_task, mock_hexapod
    ):
        """Test that angle calculations are correct for infinity wave."""
        with (
            patch("hexapod.task_interface.tasks.say_hello_task.logger") as mock_logger,
            patch(
                "hexapod.task_interface.tasks.say_hello_task.time.sleep"
            ) as mock_sleep,
            patch("hexapod.task_interface.tasks.say_hello_task.time.time") as mock_time,
        ):

            # Mock current leg angles
            original_coxa, original_femur, original_tibia = 10.0, 20.0, 30.0
            mock_hexapod.current_leg_angles = {
                0: (original_coxa, original_femur, original_tibia)
            }

            # Mock time.time to return increasing values
            call_count = 0

            def time_side_effect():
                nonlocal call_count
                call_count += 1
                return call_count * 0.01

            mock_time.side_effect = time_side_effect

            say_hello_task._perform_infinity_wave()

            # Verify that move_leg_angles was called with calculated angles
            calls = mock_hexapod.move_leg_angles.call_args_list

            # Check that we have preparation calls, animation calls, and return call
            assert len(calls) >= 3

            # Check preparation calls
            assert calls[0] == ((0, original_coxa, 45.0, original_tibia),)  # Lift leg
            assert calls[1] == ((0, original_coxa, 45.0, 45),)  # Extend tibia

            # Check return call (last call)
            assert calls[-1] == ((0, original_coxa, original_femur, original_tibia),)

    def test_perform_infinity_wave_parameters(self, say_hello_task, mock_hexapod):
        """Test that infinity wave uses correct parameters."""
        with (
            patch("hexapod.task_interface.tasks.say_hello_task.logger") as mock_logger,
            patch(
                "hexapod.task_interface.tasks.say_hello_task.time.sleep"
            ) as mock_sleep,
            patch("hexapod.task_interface.tasks.say_hello_task.time.time") as mock_time,
        ):

            # Mock current leg angles
            mock_hexapod.current_leg_angles = {0: (10.0, 20.0, 30.0)}

            # Mock time.time to return increasing values
            call_count = 0

            def time_side_effect():
                nonlocal call_count
                call_count += 1
                return call_count * 0.01

            mock_time.side_effect = time_side_effect

            say_hello_task._perform_infinity_wave()

            # Verify that the correct leg (0) is used
            for call in mock_hexapod.move_leg_angles.call_args_list:
                assert call[0][0] == 0  # First argument should be leg 0

            # Verify that extended tibia angle (45) is used
            calls = mock_hexapod.move_leg_angles.call_args_list
            # Check that tibia is set to 45 degrees in preparation and animation
            for call in calls[1:-1]:  # Skip first and last calls
                assert call[0][3] == 45  # Fourth argument should be 45

    def test_perform_infinity_wave_debug_logging(self, say_hello_task, mock_hexapod):
        """Test that debug logging works correctly."""
        with (
            patch("hexapod.task_interface.tasks.say_hello_task.logger") as mock_logger,
            patch(
                "hexapod.task_interface.tasks.say_hello_task.time.sleep"
            ) as mock_sleep,
            patch("hexapod.task_interface.tasks.say_hello_task.time.time") as mock_time,
        ):

            # Mock current leg angles
            mock_hexapod.current_leg_angles = {0: (10.0, 20.0, 30.0)}

            # Mock time.time to return increasing values
            call_count = 0

            def time_side_effect():
                nonlocal call_count
                call_count += 1
                return call_count * 0.01

            mock_time.side_effect = time_side_effect

            say_hello_task._perform_infinity_wave()

            # Verify debug logging for angle calculations
            debug_calls = [
                call
                for call in mock_logger.debug.call_args_list
                if "Moving leg 0 to angles" in str(call)
            ]
            assert len(debug_calls) > 0

    def test_perform_infinity_wave_math_calculations(
        self, say_hello_task, mock_hexapod
    ):
        """Test that mathematical calculations are correct."""
        with (
            patch("hexapod.task_interface.tasks.say_hello_task.logger") as mock_logger,
            patch(
                "hexapod.task_interface.tasks.say_hello_task.time.sleep"
            ) as mock_sleep,
            patch("hexapod.task_interface.tasks.say_hello_task.time.time") as mock_time,
        ):

            # Mock current leg angles
            original_coxa, original_femur, original_tibia = 10.0, 20.0, 30.0
            mock_hexapod.current_leg_angles = {
                0: (original_coxa, original_femur, original_tibia)
            }

            # Mock time.time to return increasing values
            call_count = 0

            def time_side_effect():
                nonlocal call_count
                call_count += 1
                return call_count * 0.01

            mock_time.side_effect = time_side_effect

            say_hello_task._perform_infinity_wave()

            # Verify that the mathematical formulas are applied correctly
            # The infinity wave uses:
            # delta_coxa = angle_amplitude * math.cos(t)
            # delta_femur = angle_amplitude * math.sin(t) * math.cos(t)
            # where angle_amplitude = 18.0

            calls = mock_hexapod.move_leg_angles.call_args_list
            animation_calls = calls[2:-1]  # Skip preparation and return calls

            # Check a few animation calls to verify the math
            for i, call in enumerate(
                animation_calls[:5]
            ):  # Check first 5 animation calls
                t = i * (2 * math.pi / 50)  # time_step calculation
                expected_delta_coxa = 18.0 * math.cos(t)
                expected_delta_femur = 18.0 * math.sin(t) * math.cos(t)

                expected_coxa = original_coxa + expected_delta_coxa
                expected_femur = original_femur + expected_delta_femur
                expected_tibia = 45.0

                actual_coxa, actual_femur, actual_tibia = (
                    call[0][1],
                    call[0][2],
                    call[0][3],
                )

                # Allow small floating point differences
                assert abs(actual_coxa - expected_coxa) < 0.1
                assert abs(actual_femur - expected_femur) < 0.1
                assert actual_tibia == expected_tibia

    def test_execute_task_lights_handler_called(
        self, say_hello_task, mock_hexapod, mock_lights_handler
    ):
        """Test that lights handler is called during task execution."""
        with (
            patch("hexapod.task_interface.tasks.say_hello_task.logger") as mock_logger,
            patch.object(say_hello_task, "_perform_infinity_wave"),
        ):

            say_hello_task.execute_task()

            # Verify lights handler is called
            mock_lights_handler.think.assert_called_once()

    def test_execute_task_final_cleanup(
        self, say_hello_task, mock_hexapod, mock_lights_handler
    ):
        """Test that final cleanup happens even after exception."""
        with (
            patch("hexapod.task_interface.tasks.say_hello_task.logger") as mock_logger,
            patch.object(
                say_hello_task,
                "_perform_infinity_wave",
                side_effect=Exception("Test error"),
            ),
        ):

            say_hello_task.execute_task()

            # Verify final cleanup still happens
            from hexapod.robot import PredefinedPosition

            mock_hexapod.move_to_position.assert_called_with(
                PredefinedPosition.LOW_PROFILE
            )
            mock_hexapod.wait_until_motion_complete.assert_called_with(
                say_hello_task.stop_event
            )
            mock_logger.info.assert_any_call("SayHelloTask completed")
