"""
Unit tests for rotate task.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from hexapod.task_interface.tasks.rotate_task import RotateTask


class TestRotateTask:
    """Test cases for RotateTask class."""

    @pytest.fixture
    def mock_hexapod(self):
        """Mock hexapod instance for testing."""
        hexapod = MagicMock()
        hexapod.gait_generator = MagicMock()
        hexapod.gait_generator.current_gait = MagicMock()
        hexapod.gait_generator.thread = MagicMock()
        hexapod.gait_params = {"rotation": {"step_radius": 50.0, "param1": "value1"}}
        hexapod.move_to_position = MagicMock()
        hexapod.wait_until_motion_complete = MagicMock()
        return hexapod

    @pytest.fixture
    def mock_lights_handler(self):
        """Mock lights handler for testing."""
        lights_handler = MagicMock()
        lights_handler.think = MagicMock()
        return lights_handler

    @pytest.fixture
    def rotate_task_angle(self, mock_hexapod, mock_lights_handler):
        """Create RotateTask instance with angle."""
        return RotateTask(
            mock_hexapod, mock_lights_handler, angle=90.0, turn_direction="clockwise"
        )

    @pytest.fixture
    def rotate_task_cycles(self, mock_hexapod, mock_lights_handler):
        """Create RotateTask instance with cycles."""
        return RotateTask(
            mock_hexapod,
            mock_lights_handler,
            cycles=5,
            turn_direction="counterclockwise",
        )

    @pytest.fixture
    def rotate_task_duration(self, mock_hexapod, mock_lights_handler):
        """Create RotateTask instance with duration."""
        return RotateTask(
            mock_hexapod, mock_lights_handler, duration=10.0, turn_direction="left"
        )

    @pytest.fixture
    def rotate_task_infinite(self, mock_hexapod, mock_lights_handler):
        """Create RotateTask instance with infinite rotation."""
        return RotateTask(mock_hexapod, mock_lights_handler, turn_direction="right")

    def test_init_default_parameters(self, mock_hexapod, mock_lights_handler):
        """Test RotateTask initialization with default parameters."""
        task = RotateTask(mock_hexapod, mock_lights_handler)

        assert task.hexapod == mock_hexapod
        assert task.lights_handler == mock_lights_handler
        assert task.angle is None
        assert task.turn_direction is None
        assert task.cycles is None
        assert task.duration is None
        assert task.callback is None

    def test_init_custom_parameters(self, mock_hexapod, mock_lights_handler):
        """Test RotateTask initialization with custom parameters."""
        callback = Mock()
        task = RotateTask(
            mock_hexapod,
            mock_lights_handler,
            angle=45.0,
            turn_direction="clockwise",
            cycles=3,
            duration=5.0,
            callback=callback,
        )

        assert task.angle == 45.0
        assert task.turn_direction == "clockwise"
        assert task.cycles == 3
        assert task.duration == 5.0
        assert task.callback == callback

    def test_perform_rotation_with_angle(self, rotate_task_angle, mock_hexapod):
        """Test performing rotation with angle."""
        with patch("hexapod.task_interface.tasks.rotate_task.logger") as mock_logger:
            rotate_task_angle._perform_rotation()

            # Verify zero position was set
            from hexapod.robot import PredefinedPosition

            mock_hexapod.move_to_position.assert_called_once_with(
                PredefinedPosition.ZERO
            )
            mock_hexapod.wait_until_motion_complete.assert_called_once_with(
                rotate_task_angle.stop_event
            )

            # Verify gait was created
            mock_hexapod.gait_generator.create_gait.assert_called_once_with(
                "tripod", **mock_hexapod.gait_params["rotation"]
            )

            # Verify direction was set
            mock_hexapod.gait_generator.current_gait.set_direction.assert_called_once_with(
                "neutral", rotation=1.0
            )

            # Verify angle-based rotation was executed
            mock_hexapod.gait_generator.execute_rotation_by_angle.assert_called_once_with(
                angle_degrees=90.0, rotation_direction=1.0, step_radius=50.0
            )
            mock_hexapod.gait_generator.thread.join.assert_called_once()

            # Verify logging
            mock_logger.info.assert_any_call(
                "Starting rotation with direction: clockwise"
            )
            mock_logger.info.assert_any_call(
                "Rotating 90.0 degrees using angle-based rotation"
            )
            mock_logger.info.assert_any_call(
                "Started rotation execution for 90.0 degrees in background thread"
            )
            mock_logger.info.assert_any_call("Completed rotation for 90.0 degrees")

    def test_perform_rotation_with_cycles(self, rotate_task_cycles, mock_hexapod):
        """Test performing rotation with cycles."""
        with patch("hexapod.task_interface.tasks.rotate_task.logger") as mock_logger:
            rotate_task_cycles._perform_rotation()

            # Verify gait was created
            mock_hexapod.gait_generator.create_gait.assert_called_once_with(
                "tripod", **mock_hexapod.gait_params["rotation"]
            )

            # Verify direction was set (counterclockwise = -1.0)
            mock_hexapod.gait_generator.current_gait.set_direction.assert_called_once_with(
                "neutral", rotation=-1.0
            )

            # Verify cycles were executed
            mock_hexapod.gait_generator.execute_cycles.assert_called_once_with(5)
            mock_hexapod.gait_generator.thread.join.assert_called_once()

            # Verify logging
            mock_logger.info.assert_any_call(
                "Starting rotation with direction: counterclockwise"
            )
            mock_logger.info.assert_any_call("Executing 5 rotation cycles")
            mock_logger.info.assert_any_call(
                "Started execution of 5 rotation cycles in background thread"
            )
            mock_logger.info.assert_any_call("Completed 5 rotation cycles")

    def test_perform_rotation_with_duration(self, rotate_task_duration, mock_hexapod):
        """Test performing rotation with duration."""
        with patch("hexapod.task_interface.tasks.rotate_task.logger") as mock_logger:
            rotate_task_duration._perform_rotation()

            # Verify gait was created
            mock_hexapod.gait_generator.create_gait.assert_called_once_with(
                "tripod", **mock_hexapod.gait_params["rotation"]
            )

            # Verify direction was set (left = -1.0)
            mock_hexapod.gait_generator.current_gait.set_direction.assert_called_once_with(
                "neutral", rotation=-1.0
            )

            # Verify duration-based execution
            mock_hexapod.gait_generator.run_for_duration.assert_called_once_with(10.0)
            mock_hexapod.gait_generator.thread.join.assert_called_once()

            # Verify logging
            mock_logger.info.assert_any_call("Starting rotation with direction: left")
            mock_logger.info.assert_any_call("Executing rotation for 10.0 seconds")
            mock_logger.info.assert_any_call(
                "Started duration-based rotation for 10.0 seconds in background thread"
            )
            mock_logger.info.assert_any_call("Completed duration-based rotation")

    def test_perform_rotation_infinite(self, rotate_task_infinite, mock_hexapod):
        """Test performing infinite rotation."""
        with patch("hexapod.task_interface.tasks.rotate_task.logger") as mock_logger:
            rotate_task_infinite._perform_rotation()

            # Verify gait was created
            mock_hexapod.gait_generator.create_gait.assert_called_once_with(
                "tripod", **mock_hexapod.gait_params["rotation"]
            )

            # Verify direction was set (right = 1.0)
            mock_hexapod.gait_generator.current_gait.set_direction.assert_called_once_with(
                "neutral", rotation=1.0
            )

            # Verify infinite execution
            mock_hexapod.gait_generator.start.assert_called_once()
            mock_hexapod.gait_generator.thread.join.assert_called_once()

            # Verify logging
            mock_logger.info.assert_any_call("Starting rotation with direction: right")
            mock_logger.info.assert_any_call("Starting infinite gait generation")
            mock_logger.warning.assert_any_call(
                "Infinite gait generation started - will continue until stopped externally"
            )
            mock_logger.info.assert_any_call("Infinite gait generation completed")

    def test_rotation_direction_mapping(self, mock_hexapod, mock_lights_handler):
        """Test rotation direction mapping."""
        test_cases = [
            ("clockwise", 1.0),
            ("right", 1.0),
            ("counterclockwise", -1.0),
            ("left", -1.0),
            ("invalid", 1.0),  # Default to clockwise
        ]

        for direction, expected_rotation in test_cases:
            task = RotateTask(
                mock_hexapod, mock_lights_handler, turn_direction=direction, cycles=1
            )

            with patch("hexapod.task_interface.tasks.rotate_task.logger"):
                task._perform_rotation()

                # Verify direction was set correctly
                mock_hexapod.gait_generator.current_gait.set_direction.assert_called_with(
                    "neutral", rotation=expected_rotation
                )

                # Reset mocks for next iteration
                mock_hexapod.gait_generator.reset_mock()

    def test_perform_rotation_no_current_gait(self, rotate_task_angle, mock_hexapod):
        """Test rotation when current_gait is None."""
        mock_hexapod.gait_generator.current_gait = None

        with patch("hexapod.task_interface.tasks.rotate_task.logger"):
            rotate_task_angle._perform_rotation()

            # Should still execute angle-based rotation
            mock_hexapod.gait_generator.execute_rotation_by_angle.assert_called_once()

    def test_perform_rotation_no_gait_thread(self, rotate_task_angle, mock_hexapod):
        """Test rotation when gait generator thread is None."""
        mock_hexapod.gait_generator.thread = None

        with patch("hexapod.task_interface.tasks.rotate_task.logger") as mock_logger:
            rotate_task_angle._perform_rotation()

            # Should not call join on None thread
            # The method should handle this gracefully
            mock_logger.info.assert_any_call("Completed rotation for 90.0 degrees")

    def test_execute_task_success(
        self, rotate_task_angle, mock_hexapod, mock_lights_handler
    ):
        """Test successful execution of rotate task."""
        with (
            patch.object(rotate_task_angle, "_perform_rotation"),
            patch("hexapod.task_interface.tasks.rotate_task.logger") as mock_logger,
        ):

            rotate_task_angle.execute_task()

            # Verify lights handler was called
            mock_lights_handler.think.assert_called_once()

            # Verify rotation was performed
            rotate_task_angle._perform_rotation.assert_called_once()

            # Verify final position
            from hexapod.robot import PredefinedPosition

            mock_hexapod.move_to_position.assert_called_with(PredefinedPosition.ZERO)
            mock_hexapod.wait_until_motion_complete.assert_called_with(
                rotate_task_angle.stop_event
            )

            # Verify logging
            mock_logger.info.assert_any_call("RotateTask started")
            mock_logger.info.assert_any_call(
                "Performing rotation with direction: clockwise."
            )
            mock_logger.info.assert_any_call("RotateTask completed")

    def test_execute_task_exception_handling(
        self, rotate_task_angle, mock_hexapod, mock_lights_handler
    ):
        """Test exception handling during rotate task execution."""
        # Make _perform_rotation raise an exception
        with (
            patch.object(
                rotate_task_angle,
                "_perform_rotation",
                side_effect=Exception("Rotation failed"),
            ),
            patch("hexapod.task_interface.tasks.rotate_task.logger") as mock_logger,
        ):

            rotate_task_angle.execute_task()

            # Verify exception was logged
            mock_logger.exception.assert_called_once()
            assert "Error in RotateTask" in str(mock_logger.exception.call_args)

            # Verify final position was still called
            from hexapod.robot import PredefinedPosition

            mock_hexapod.move_to_position.assert_called_with(PredefinedPosition.ZERO)
            mock_hexapod.wait_until_motion_complete.assert_called_with(
                rotate_task_angle.stop_event
            )

    def test_rotation_priority(self, mock_hexapod, mock_lights_handler):
        """Test that angle takes priority over cycles and duration."""
        task = RotateTask(
            mock_hexapod,
            mock_lights_handler,
            angle=90.0,
            cycles=5,
            duration=10.0,
            turn_direction="clockwise",
        )

        with patch("hexapod.task_interface.tasks.rotate_task.logger"):
            task._perform_rotation()

            # Should execute angle-based rotation, not cycles or duration
            mock_hexapod.gait_generator.execute_rotation_by_angle.assert_called_once()
            mock_hexapod.gait_generator.execute_cycles.assert_not_called()
            mock_hexapod.gait_generator.run_for_duration.assert_not_called()

    def test_cycles_priority_over_duration(self, mock_hexapod, mock_lights_handler):
        """Test that cycles take priority over duration when angle is not specified."""
        task = RotateTask(
            mock_hexapod,
            mock_lights_handler,
            cycles=5,
            duration=10.0,
            turn_direction="clockwise",
        )

        with patch("hexapod.task_interface.tasks.rotate_task.logger"):
            task._perform_rotation()

            # Should execute cycles, not duration
            mock_hexapod.gait_generator.execute_cycles.assert_called_once()
            mock_hexapod.gait_generator.run_for_duration.assert_not_called()

    def test_gait_parameters_usage(self, rotate_task_angle, mock_hexapod):
        """Test that rotation gait parameters are used correctly."""
        with patch("hexapod.task_interface.tasks.rotate_task.logger"):
            rotate_task_angle._perform_rotation()

            # Verify gait was created with rotation parameters
            call_args = mock_hexapod.gait_generator.create_gait.call_args
            gait_params = call_args[1]

            assert gait_params["step_radius"] == 50.0
            assert gait_params["param1"] == "value1"
