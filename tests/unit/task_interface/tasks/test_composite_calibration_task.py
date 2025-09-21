"""Unit tests for CompositeCalibrationTask."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from hexapod.task_interface.tasks.composite_calibration_task import (
    CompositeCalibrationTask,
    MonitorCalibrationStatusTask,
    RunCalibrationTask,
)
from hexapod.robot import PredefinedPosition


class TestCompositeCalibrationTask:
    """Test cases for CompositeCalibrationTask."""

    @pytest.fixture
    def mock_hexapod(self):
        """Create a mock hexapod."""
        hexapod = Mock()
        hexapod.calibration = Mock()
        hexapod.calibrate_all_servos = Mock()
        hexapod.move_to_position = Mock()
        hexapod.wait_until_motion_complete = Mock()
        return hexapod

    @pytest.fixture
    def mock_lights_handler(self):
        """Create a mock lights handler."""
        return Mock()

    @pytest.fixture
    def mock_external_control_paused_event(self):
        """Create a mock external control paused event."""
        return Mock()

    @pytest.fixture
    def composite_calibration_task(
        self, mock_hexapod, mock_lights_handler, mock_external_control_paused_event
    ):
        """Create a CompositeCalibrationTask instance."""
        return CompositeCalibrationTask(
            mock_hexapod, mock_lights_handler, mock_external_control_paused_event
        )

    def test_init_default_parameters(
        self, mock_hexapod, mock_lights_handler, mock_external_control_paused_event
    ):
        """Test initialization with default parameters."""
        task = CompositeCalibrationTask(
            mock_hexapod, mock_lights_handler, mock_external_control_paused_event
        )
        assert task.hexapod == mock_hexapod
        assert task.lights_handler == mock_lights_handler
        assert task.external_control_paused_event == mock_external_control_paused_event
        assert task.callback is None
        assert isinstance(task.run_calibration_task, RunCalibrationTask)
        assert isinstance(task.monitor_calibration_task, MonitorCalibrationStatusTask)

    def test_init_with_callback(
        self, mock_hexapod, mock_lights_handler, mock_external_control_paused_event
    ):
        """Test initialization with a custom callback."""
        mock_callback = Mock()
        task = CompositeCalibrationTask(
            mock_hexapod,
            mock_lights_handler,
            mock_external_control_paused_event,
            callback=mock_callback,
        )
        assert task.callback == mock_callback

    def test_execute_task_success(
        self,
        composite_calibration_task,
        mock_hexapod,
        mock_lights_handler,
        mock_external_control_paused_event,
    ):
        """Test successful task execution."""
        with patch(
            "hexapod.task_interface.tasks.composite_calibration_task.logger"
        ) as mock_logger:
            # Mock the child tasks
            composite_calibration_task.run_calibration_task = Mock()
            composite_calibration_task.monitor_calibration_task = Mock()

            composite_calibration_task.execute_task()

            # Verify task sequence
            mock_logger.info.assert_any_call("CompositeCalibrationTask started")
            mock_logger.user_info.assert_called_once_with(
                "Starting composite calibration task."
            )
            composite_calibration_task.monitor_calibration_task.start.assert_called_once()
            composite_calibration_task.run_calibration_task.start.assert_called_once()
            composite_calibration_task.run_calibration_task.join.assert_called_once()
            composite_calibration_task.monitor_calibration_task.join.assert_called_once()
            mock_logger.debug.assert_called_once_with("Composite calibration completed")
            mock_external_control_paused_event.clear.assert_called_once()
            mock_logger.info.assert_any_call("CompositeCalibrationTask completed")

    def test_execute_task_exception_handling(
        self,
        composite_calibration_task,
        mock_hexapod,
        mock_lights_handler,
        mock_external_control_paused_event,
    ):
        """Test task execution with exception handling."""
        with patch(
            "hexapod.task_interface.tasks.composite_calibration_task.logger"
        ) as mock_logger:
            # Mock the child tasks to raise an exception
            composite_calibration_task.run_calibration_task = Mock()
            composite_calibration_task.monitor_calibration_task = Mock()
            composite_calibration_task.run_calibration_task.start.side_effect = (
                Exception("Test error")
            )

            composite_calibration_task.execute_task()

            # Should log the exception
            mock_logger.exception.assert_called_once_with(
                "Composite calibration task failed: Test error"
            )
            mock_external_control_paused_event.clear.assert_called_once()
            mock_logger.info.assert_any_call("CompositeCalibrationTask completed")

    def test_stop_task_with_timeout(
        self,
        composite_calibration_task,
        mock_hexapod,
        mock_lights_handler,
        mock_external_control_paused_event,
    ):
        """Test stopping task with timeout."""
        with (
            patch(
                "hexapod.task_interface.tasks.composite_calibration_task.logger"
            ) as mock_logger,
            patch.object(
                composite_calibration_task.__class__.__bases__[0], "stop_task"
            ) as mock_super_stop,
        ):

            # Mock the child tasks
            composite_calibration_task.run_calibration_task = Mock()
            composite_calibration_task.monitor_calibration_task = Mock()

            composite_calibration_task.stop_task(timeout=5.0)

            # Verify stop sequence
            mock_logger.info.assert_called_once_with(
                "Stopping composite calibration task"
            )
            composite_calibration_task.run_calibration_task.stop_task.assert_called_once()
            composite_calibration_task.monitor_calibration_task.stop_task.assert_called_once()
            composite_calibration_task.run_calibration_task.join.assert_called_once_with(
                timeout=5.0
            )
            composite_calibration_task.monitor_calibration_task.join.assert_called_once_with(
                timeout=5.0
            )
            mock_super_stop.assert_called_once()

    def test_stop_task_without_timeout(
        self,
        composite_calibration_task,
        mock_hexapod,
        mock_lights_handler,
        mock_external_control_paused_event,
    ):
        """Test stopping task without timeout."""
        with (
            patch(
                "hexapod.task_interface.tasks.composite_calibration_task.logger"
            ) as mock_logger,
            patch.object(
                composite_calibration_task.__class__.__bases__[0], "stop_task"
            ) as mock_super_stop,
        ):

            # Mock the child tasks
            composite_calibration_task.run_calibration_task = Mock()
            composite_calibration_task.monitor_calibration_task = Mock()

            composite_calibration_task.stop_task()

            # Verify stop sequence
            mock_logger.info.assert_called_once_with(
                "Stopping composite calibration task"
            )
            composite_calibration_task.run_calibration_task.stop_task.assert_called_once()
            composite_calibration_task.monitor_calibration_task.stop_task.assert_called_once()
            composite_calibration_task.run_calibration_task.join.assert_called_once()
            composite_calibration_task.monitor_calibration_task.join.assert_called_once()
            mock_super_stop.assert_called_once()

    def test_stop_task_exception_handling(
        self,
        composite_calibration_task,
        mock_hexapod,
        mock_lights_handler,
        mock_external_control_paused_event,
    ):
        """Test stop task with exception handling."""
        with patch(
            "hexapod.task_interface.tasks.composite_calibration_task.logger"
        ) as mock_logger:
            # Mock the child tasks to raise an exception
            composite_calibration_task.run_calibration_task = Mock()
            composite_calibration_task.monitor_calibration_task = Mock()
            composite_calibration_task.run_calibration_task.stop_task.side_effect = (
                Exception("Stop error")
            )

            with pytest.raises(Exception, match="Stop error"):
                composite_calibration_task.stop_task()

            # Should log the exception
            mock_logger.exception.assert_called_once_with(
                "Error stopping composite calibration task: Stop error"
            )


class TestMonitorCalibrationStatusTask:
    """Test cases for MonitorCalibrationStatusTask."""

    @pytest.fixture
    def mock_hexapod(self):
        """Create a mock hexapod."""
        hexapod = Mock()
        hexapod.calibration = Mock()
        hexapod.calibration.get_calibration_status.return_value = {
            "leg_0": "calibrated",
            "leg_1": "calibrated",
            "leg_2": "calibrated",
            "leg_3": "calibrated",
            "leg_4": "calibrated",
            "leg_5": "calibrated",
        }
        return hexapod

    @pytest.fixture
    def mock_lights_handler(self):
        """Create a mock lights handler."""
        return Mock()

    @pytest.fixture
    def monitor_calibration_task(self, mock_hexapod, mock_lights_handler):
        """Create a MonitorCalibrationStatusTask instance."""
        return MonitorCalibrationStatusTask(mock_hexapod, mock_lights_handler)

    def test_init_default_parameters(self, mock_hexapod, mock_lights_handler):
        """Test initialization with default parameters."""
        task = MonitorCalibrationStatusTask(mock_hexapod, mock_lights_handler)
        assert task.hexapod == mock_hexapod
        assert task.lights_handler == mock_lights_handler
        assert task.callback is None

    def test_init_with_callback(self, mock_hexapod, mock_lights_handler):
        """Test initialization with a custom callback."""
        mock_callback = Mock()
        task = MonitorCalibrationStatusTask(
            mock_hexapod, mock_lights_handler, callback=mock_callback
        )
        assert task.callback == mock_callback

    def test_execute_task_all_calibrated(
        self, monitor_calibration_task, mock_hexapod, mock_lights_handler
    ):
        """Test task execution when all legs are calibrated."""
        with patch(
            "hexapod.task_interface.tasks.composite_calibration_task.logger"
        ) as mock_logger:
            # Mock stop_event to be set after first check
            monitor_calibration_task.stop_event = Mock()
            monitor_calibration_task.stop_event.is_set.return_value = True
            monitor_calibration_task.stop_event.wait.return_value = None

            monitor_calibration_task.execute_task()

            # Verify task sequence
            mock_logger.info.assert_any_call("MonitorCalibrationStatusTask started")
            mock_hexapod.calibration.get_calibration_status.assert_called_once()
            mock_lights_handler.update_calibration_leds_status.assert_called_once()
            # Debug log is only called inside the while loop, which we're skipping
            mock_lights_handler.off.assert_called_once()
            mock_logger.info.assert_any_call("MonitorCalibrationStatusTask completed")

    def test_execute_task_not_all_calibrated(
        self, monitor_calibration_task, mock_hexapod, mock_lights_handler
    ):
        """Test task execution when not all legs are calibrated."""
        with patch(
            "hexapod.task_interface.tasks.composite_calibration_task.logger"
        ) as mock_logger:
            # Mock calibration status to show some legs not calibrated
            mock_hexapod.calibration.get_calibration_status.return_value = {
                "leg_0": "calibrated",
                "leg_1": "not_calibrated",
                "leg_2": "calibrated",
                "leg_3": "not_calibrated",
                "leg_4": "calibrated",
                "leg_5": "not_calibrated",
            }

            # Mock stop_event to be set after first check
            monitor_calibration_task.stop_event = Mock()
            monitor_calibration_task.stop_event.is_set.return_value = True
            monitor_calibration_task.stop_event.wait.return_value = None

            monitor_calibration_task.execute_task()

            # Verify task sequence
            mock_logger.info.assert_any_call("MonitorCalibrationStatusTask started")
            mock_hexapod.calibration.get_calibration_status.assert_called_once()
            mock_lights_handler.update_calibration_leds_status.assert_called_once()
            # Debug log is only called inside the while loop, which we're skipping
            mock_lights_handler.off.assert_called_once()
            mock_logger.info.assert_any_call("MonitorCalibrationStatusTask completed")

    def test_execute_task_exception_handling(
        self, monitor_calibration_task, mock_hexapod, mock_lights_handler
    ):
        """Test task execution with exception handling."""
        with patch(
            "hexapod.task_interface.tasks.composite_calibration_task.logger"
        ) as mock_logger:
            # Mock calibration to raise an exception
            mock_hexapod.calibration.get_calibration_status.side_effect = Exception(
                "Calibration error"
            )

            monitor_calibration_task.execute_task()

            # Should log the exception
            mock_logger.exception.assert_called_once_with(
                "Error in calibration status monitoring thread: Calibration error"
            )
            mock_lights_handler.off.assert_called_once()
            mock_logger.info.assert_any_call("MonitorCalibrationStatusTask completed")


class TestRunCalibrationTask:
    """Test cases for RunCalibrationTask."""

    @pytest.fixture
    def mock_hexapod(self):
        """Create a mock hexapod."""
        hexapod = Mock()
        hexapod.calibrate_all_servos = Mock()
        hexapod.move_to_position = Mock()
        hexapod.wait_until_motion_complete = Mock()
        return hexapod

    @pytest.fixture
    def run_calibration_task(self, mock_hexapod):
        """Create a RunCalibrationTask instance."""
        return RunCalibrationTask(mock_hexapod)

    def test_init_default_parameters(self, mock_hexapod):
        """Test initialization with default parameters."""
        with patch(
            "hexapod.task_interface.tasks.composite_calibration_task.logger"
        ) as mock_logger:
            task = RunCalibrationTask(mock_hexapod)
            assert task.hexapod == mock_hexapod
            assert task.callback is None
            mock_logger.debug.assert_called_once_with("Initializing RunCalibrationTask")

    def test_init_with_callback(self, mock_hexapod):
        """Test initialization with a custom callback."""
        with patch(
            "hexapod.task_interface.tasks.composite_calibration_task.logger"
        ) as mock_logger:
            mock_callback = Mock()
            task = RunCalibrationTask(mock_hexapod, callback=mock_callback)
            assert task.callback == mock_callback

    def test_execute_task_success(self, run_calibration_task, mock_hexapod):
        """Test successful task execution."""
        with patch(
            "hexapod.task_interface.tasks.composite_calibration_task.logger"
        ) as mock_logger:
            run_calibration_task.execute_task()

            # Verify task sequence
            mock_logger.user_info.assert_called_once_with("RunCalibrationTask started")
            mock_hexapod.calibrate_all_servos.assert_called_once_with(
                stop_event=run_calibration_task.stop_event
            )
            mock_hexapod.move_to_position.assert_called_once_with(
                PredefinedPosition.LOW_PROFILE
            )
            mock_hexapod.wait_until_motion_complete.assert_called_once_with(
                stop_event=run_calibration_task.stop_event
            )
            mock_logger.info.assert_called_once_with("RunCalibrationTask completed")

    def test_execute_task_exception_handling(self, run_calibration_task, mock_hexapod):
        """Test task execution with exception handling."""
        with patch(
            "hexapod.task_interface.tasks.composite_calibration_task.logger"
        ) as mock_logger:
            # Mock calibrate_all_servos to raise an exception
            mock_hexapod.calibrate_all_servos.side_effect = Exception(
                "Calibration error"
            )

            run_calibration_task.execute_task()

            # Should log the exception
            mock_logger.exception.assert_called_once_with(
                "Error in RunCalibrationTask thread: Calibration error"
            )
            mock_hexapod.move_to_position.assert_called_once_with(
                PredefinedPosition.LOW_PROFILE
            )
            mock_hexapod.wait_until_motion_complete.assert_called_once_with(
                stop_event=run_calibration_task.stop_event
            )
            mock_logger.info.assert_called_once_with("RunCalibrationTask completed")

    def test_execute_task_final_position(self, run_calibration_task, mock_hexapod):
        """Test that the hexapod moves to LOW_PROFILE position after calibration."""
        with patch("hexapod.task_interface.tasks.composite_calibration_task.logger"):
            run_calibration_task.execute_task()
            mock_hexapod.move_to_position.assert_called_with(
                PredefinedPosition.LOW_PROFILE
            )
            mock_hexapod.wait_until_motion_complete.assert_called_once_with(
                stop_event=run_calibration_task.stop_event
            )
