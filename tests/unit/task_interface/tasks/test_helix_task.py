"""
Unit tests for helix task.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from hexapod.task_interface.tasks.helix_task import HelixTask


class TestHelixTask:
    """Test cases for HelixTask class."""

    @pytest.fixture
    def mock_hexapod(self):
        """Mock hexapod instance for testing."""
        hexapod = MagicMock()
        hexapod.current_leg_angles = [
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0),
        ]
        hexapod.coxa_params = {"angle_min": -90, "angle_max": 90}
        hexapod.move_to_position = MagicMock()
        hexapod.wait_until_motion_complete = MagicMock()
        hexapod.move_all_legs_angles = MagicMock()
        return hexapod

    @pytest.fixture
    def mock_lights_handler(self):
        """Mock lights handler for testing."""
        lights_handler = MagicMock()
        lights_handler.think = MagicMock()
        return lights_handler

    @pytest.fixture
    def helix_task(self, mock_hexapod, mock_lights_handler):
        """Create HelixTask instance for testing."""
        return HelixTask(mock_hexapod, mock_lights_handler)

    def test_init_default_parameters(self, mock_hexapod, mock_lights_handler):
        """Test HelixTask initialization with default parameters."""
        task = HelixTask(mock_hexapod, mock_lights_handler)

        assert task.hexapod == mock_hexapod
        assert task.lights_handler == mock_lights_handler
        assert task.callback is None

    def test_init_custom_parameters(self, mock_hexapod, mock_lights_handler):
        """Test HelixTask initialization with custom parameters."""
        callback = Mock()
        task = HelixTask(mock_hexapod, mock_lights_handler, callback=callback)

        assert task.callback == callback

    def test_perform_helix_success(self, helix_task, mock_hexapod):
        """Test successful helix performance."""
        with patch("hexapod.task_interface.tasks.helix_task.logger") as mock_logger:
            helix_task._perform_helix()

            # Verify low profile position was set
            from hexapod.robot import PredefinedPosition

            mock_hexapod.move_to_position.assert_called_once_with(
                PredefinedPosition.LOW_PROFILE
            )
            # wait_until_motion_complete is called 5 times: 1 initial + 4 after each move_all_legs_angles
            assert mock_hexapod.wait_until_motion_complete.call_count == 5

            # Verify helix positions were calculated
            assert hasattr(helix_task, "helix_positions")
            assert "helix_minimum" in helix_task.helix_positions
            assert "helix_maximum" in helix_task.helix_positions
            assert len(helix_task.helix_positions["helix_minimum"]) == 6
            assert len(helix_task.helix_positions["helix_maximum"]) == 6

            # Verify helix movements were performed
            assert (
                mock_hexapod.move_all_legs_angles.call_count == 4
            )  # 2 repetitions * 2 positions each

            # Verify logging
            mock_logger.info.assert_any_call("Starting helix maneuver")
            mock_logger.info.assert_any_call("Performing helix repetition 1/2")
            mock_logger.info.assert_any_call("Performing helix repetition 2/2")
            mock_logger.debug.assert_any_call("Helix maneuver: Finished.")

    def test_perform_helix_stop_event_during_position_change(
        self, helix_task, mock_hexapod
    ):
        """Test helix performance when stop event is set during position change."""
        # Set stop event before position change
        helix_task.stop_event.set()

        with patch("hexapod.task_interface.tasks.helix_task.logger") as mock_logger:
            helix_task._perform_helix()

            # Should not proceed with helix movements
            mock_hexapod.move_all_legs_angles.assert_not_called()

    def test_perform_helix_stop_event_during_repetition(self, helix_task, mock_hexapod):
        """Test helix performance when stop event is set during repetition."""
        # Set stop event after first repetition
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # After first move_all_legs_angles call
                helix_task.stop_event.set()

        mock_hexapod.move_all_legs_angles.side_effect = side_effect

        with patch("hexapod.task_interface.tasks.helix_task.logger") as mock_logger:
            helix_task._perform_helix()

            # Should have started but stopped early
            assert mock_hexapod.move_all_legs_angles.call_count >= 1
            # The stop event check happens at the beginning of each repetition
            # So we need to check if the stop event was set during the loop
            assert helix_task.stop_event.is_set()

    def test_execute_task_success(self, helix_task, mock_hexapod, mock_lights_handler):
        """Test successful execution of helix task."""
        with (
            patch.object(helix_task, "_perform_helix"),
            patch("hexapod.task_interface.tasks.helix_task.logger") as mock_logger,
        ):

            helix_task.execute_task()

            # Verify lights handler was called
            mock_lights_handler.think.assert_called_once()

            # Verify helix was performed
            helix_task._perform_helix.assert_called_once()

            # Verify final position
            from hexapod.robot import PredefinedPosition

            mock_hexapod.move_to_position.assert_called_with(
                PredefinedPosition.LOW_PROFILE
            )
            mock_hexapod.wait_until_motion_complete.assert_called_with(
                helix_task.stop_event
            )

            # Verify logging
            mock_logger.info.assert_any_call("HelixTask started")
            mock_logger.info.assert_any_call("Performing helix routine.")
            mock_logger.info.assert_any_call("HelixTask completed")

    def test_execute_task_exception_handling(
        self, helix_task, mock_hexapod, mock_lights_handler
    ):
        """Test exception handling during helix task execution."""
        # Make _perform_helix raise an exception
        with (
            patch.object(
                helix_task, "_perform_helix", side_effect=Exception("Helix failed")
            ),
            patch("hexapod.task_interface.tasks.helix_task.logger") as mock_logger,
        ):

            helix_task.execute_task()

            # Verify exception was logged
            mock_logger.exception.assert_called_once()
            assert "Error in HelixTask" in str(mock_logger.exception.call_args)

            # Verify final position was still called
            from hexapod.robot import PredefinedPosition

            mock_hexapod.move_to_position.assert_called_with(
                PredefinedPosition.LOW_PROFILE
            )
            mock_hexapod.wait_until_motion_complete.assert_called_with(
                helix_task.stop_event
            )

    def test_helix_positions_calculation(self, helix_task, mock_hexapod):
        """Test helix positions calculation."""
        # Set up mock current leg angles
        mock_hexapod.current_leg_angles = [
            (10.0, 20.0, 30.0),
            (11.0, 21.0, 31.0),
            (12.0, 22.0, 32.0),
            (13.0, 23.0, 33.0),
            (14.0, 24.0, 34.0),
            (15.0, 25.0, 35.0),
        ]

        with patch("hexapod.task_interface.tasks.helix_task.logger"):
            helix_task._perform_helix()

            # Verify helix positions were calculated correctly
            helix_min = helix_task.helix_positions["helix_minimum"]
            helix_max = helix_task.helix_positions["helix_maximum"]

            # Check that coxa angles are set correctly
            for i in range(6):
                # helix_min should have coxa = angle_min + 25 = -90 + 25 = -65
                assert helix_min[i][0] == -65.0
                # helix_max should have coxa = angle_max = 90
                assert helix_max[i][0] == 90.0
                # femur and tibia should be preserved from current angles
                assert helix_min[i][1] == mock_hexapod.current_leg_angles[i][1]
                assert helix_min[i][2] == mock_hexapod.current_leg_angles[i][2]
                assert helix_max[i][1] == mock_hexapod.current_leg_angles[i][1]
                assert helix_max[i][2] == mock_hexapod.current_leg_angles[i][2]

    def test_helix_repetitions(self, helix_task, mock_hexapod):
        """Test helix repetitions."""
        with patch("hexapod.task_interface.tasks.helix_task.logger"):
            helix_task._perform_helix()

            # Should perform 2 repetitions, each with 2 movements (max and min)
            assert mock_hexapod.move_all_legs_angles.call_count == 4

            # Verify the sequence of calls
            calls = mock_hexapod.move_all_legs_angles.call_args_list
            # First call should be helix_maximum
            assert calls[0][0][0] == helix_task.helix_positions["helix_maximum"]
            # Second call should be helix_minimum
            assert calls[1][0][0] == helix_task.helix_positions["helix_minimum"]
            # Third call should be helix_maximum again
            assert calls[2][0][0] == helix_task.helix_positions["helix_maximum"]
            # Fourth call should be helix_minimum again
            assert calls[3][0][0] == helix_task.helix_positions["helix_minimum"]

    def test_helix_wait_until_motion_complete_calls(self, helix_task, mock_hexapod):
        """Test that wait_until_motion_complete is called correctly."""
        with patch("hexapod.task_interface.tasks.helix_task.logger"):
            helix_task._perform_helix()

            # Should be called 5 times: 1 initial + 4 after each move_all_legs_angles
            assert mock_hexapod.wait_until_motion_complete.call_count == 5

            # All calls should use the stop_event
            for call in mock_hexapod.wait_until_motion_complete.call_args_list:
                assert call[0][0] == helix_task.stop_event
