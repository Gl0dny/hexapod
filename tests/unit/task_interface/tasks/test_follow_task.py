"""Unit tests for FollowTask."""

import pytest
from unittest.mock import Mock, patch
from hexapod.task_interface.tasks.follow_task import FollowTask
from hexapod.robot import PredefinedPosition


class TestFollowTask:
    """Test cases for FollowTask."""

    @pytest.fixture
    def mock_hexapod(self):
        """Create a mock hexapod."""
        hexapod = Mock()
        hexapod.gait_generator = Mock()
        hexapod.gait_generator.current_gait = None
        hexapod.gait_generator.is_running = False
        hexapod.gait_generator.create_gait = Mock()
        hexapod.gait_generator.queue_direction = Mock()
        hexapod.gait_generator.start = Mock()
        hexapod.gait_generator.stop = Mock()
        hexapod.move_to_position = Mock()
        hexapod.wait_until_motion_complete = Mock()
        hexapod.gait_params = {"translation": {}}
        return hexapod

    @pytest.fixture
    def mock_lights_handler(self):
        """Create a mock lights handler."""
        return Mock()

    @pytest.fixture
    def mock_odas_processor(self):
        """Create a mock ODAS processor."""
        processor = Mock()
        processor.get_tracked_sources_azimuths = Mock()
        processor.start = Mock()
        processor.close = Mock()
        return processor

    @pytest.fixture
    def mock_external_control_paused_event(self):
        """Create a mock external control paused event."""
        return Mock()

    @pytest.fixture
    def follow_task(self, mock_hexapod, mock_lights_handler, mock_odas_processor, mock_external_control_paused_event):
        """Create a FollowTask instance."""
        return FollowTask(
            mock_hexapod,
            mock_lights_handler,
            mock_odas_processor,
            mock_external_control_paused_event
        )

    def test_init_default_parameters(self, mock_hexapod, mock_lights_handler, mock_odas_processor, mock_external_control_paused_event):
        """Test initialization with default parameters."""
        with patch('hexapod.task_interface.tasks.follow_task.logger') as mock_logger:
            task = FollowTask(
                mock_hexapod,
                mock_lights_handler,
                mock_odas_processor,
                mock_external_control_paused_event
            )
            assert task.hexapod == mock_hexapod
            assert task.lights_handler == mock_lights_handler
            assert task.odas_processor == mock_odas_processor
            assert task.external_control_paused_event == mock_external_control_paused_event
            assert task.callback is None
            assert task.odas_processor.stop_event == task.stop_event
            mock_logger.debug.assert_called_once_with("Initializing FollowTask")

    def test_init_with_callback(self, mock_hexapod, mock_lights_handler, mock_odas_processor, mock_external_control_paused_event):
        """Test initialization with a custom callback."""
        with patch('hexapod.task_interface.tasks.follow_task.logger') as mock_logger:
            mock_callback = Mock()
            task = FollowTask(
                mock_hexapod,
                mock_lights_handler,
                mock_odas_processor,
                mock_external_control_paused_event,
                callback=mock_callback
            )
            assert task.callback == mock_callback

    def test_get_movement_direction_from_odas_no_sources(self, follow_task, mock_odas_processor):
        """Test getting movement direction when no sources are available."""
        mock_odas_processor.get_tracked_sources_azimuths.return_value = {}
        
        direction = follow_task._get_movement_direction_from_odas()
        
        assert direction == "neutral"

    def test_get_movement_direction_from_odas_right(self, follow_task, mock_odas_processor):
        """Test getting movement direction for right sector."""
        mock_odas_processor.get_tracked_sources_azimuths.return_value = {0: 0}
        
        direction = follow_task._get_movement_direction_from_odas()
        
        assert direction == "right"

    def test_get_movement_direction_from_odas_forward(self, follow_task, mock_odas_processor):
        """Test getting movement direction for forward sector."""
        mock_odas_processor.get_tracked_sources_azimuths.return_value = {0: 90}
        
        direction = follow_task._get_movement_direction_from_odas()
        
        assert direction == "forward"

    def test_get_movement_direction_from_odas_left(self, follow_task, mock_odas_processor):
        """Test getting movement direction for left sector."""
        mock_odas_processor.get_tracked_sources_azimuths.return_value = {0: 180}
        
        direction = follow_task._get_movement_direction_from_odas()
        
        assert direction == "left"

    def test_get_movement_direction_from_odas_backward(self, follow_task, mock_odas_processor):
        """Test getting movement direction for backward sector."""
        mock_odas_processor.get_tracked_sources_azimuths.return_value = {0: 270}
        
        direction = follow_task._get_movement_direction_from_odas()
        
        assert direction == "backward"

    def test_move_hexapod_in_direction_no_gait(self, follow_task, mock_hexapod):
        """Test moving hexapod when no gait exists."""
        follow_task._move_hexapod_in_direction("forward")
        
        mock_hexapod.gait_generator.create_gait.assert_called_once_with("tripod", **{})
        mock_hexapod.gait_generator.queue_direction.assert_called_once_with("forward")
        mock_hexapod.gait_generator.start.assert_called_once()

    def test_move_hexapod_in_direction_existing_gait(self, follow_task, mock_hexapod):
        """Test moving hexapod when gait already exists."""
        mock_hexapod.gait_generator.current_gait = Mock()
        
        follow_task._move_hexapod_in_direction("left")
        
        mock_hexapod.gait_generator.create_gait.assert_not_called()
        mock_hexapod.gait_generator.queue_direction.assert_called_once_with("left")
        mock_hexapod.gait_generator.start.assert_called_once()

    def test_execute_task_success(self, follow_task, mock_hexapod, mock_lights_handler, mock_odas_processor, mock_external_control_paused_event):
        """Test successful task execution."""
        with patch('hexapod.task_interface.tasks.follow_task.logger') as mock_logger, \
             patch('hexapod.task_interface.tasks.follow_task.time.sleep') as mock_sleep, \
             patch('hexapod.task_interface.tasks.follow_task.threading.Thread') as mock_thread_class:
            
            # Mock the thread
            mock_thread = Mock()
            mock_thread_class.return_value = mock_thread
            
            # Mock stop_event to exit the loop immediately
            follow_task.stop_event = Mock()
            follow_task.stop_event.is_set.return_value = True
            follow_task.stop_event.wait.return_value = None
            
            # Mock ODAS processor to return a direction
            mock_odas_processor.get_tracked_sources_azimuths.return_value = {0: 90}
            
            follow_task.execute_task()
            
            # Verify task sequence
            mock_logger.info.assert_any_call("FollowTask started")
            mock_sleep.assert_called_once_with(4)
            mock_hexapod.move_to_position.assert_called_once_with(PredefinedPosition.ZERO)
            mock_hexapod.wait_until_motion_complete.assert_called_once_with(stop_event=follow_task.stop_event)
            mock_thread_class.assert_called_once()
            mock_thread.start.assert_called_once()
            mock_odas_processor.close.assert_called_once()
            mock_thread.join.assert_called_once_with(timeout=5)
            mock_logger.info.assert_any_call("FollowTask completed")

    def test_execute_task_exception_handling(self, follow_task, mock_hexapod, mock_lights_handler, mock_odas_processor, mock_external_control_paused_event):
        """Test task execution with exception handling."""
        with patch('hexapod.task_interface.tasks.follow_task.logger') as mock_logger, \
             patch('hexapod.task_interface.tasks.follow_task.time.sleep') as mock_sleep, \
             patch('hexapod.task_interface.tasks.follow_task.threading.Thread') as mock_thread_class:
            
            # Mock the thread
            mock_thread = Mock()
            mock_thread_class.return_value = mock_thread
            
            # Mock stop_event to exit the loop after one iteration
            follow_task.stop_event = Mock()
            follow_task.stop_event.is_set.side_effect = [False, True]  # First call returns False, second returns True
            follow_task.stop_event.wait.return_value = None
            
            # Mock ODAS processor to raise an exception
            mock_odas_processor.get_tracked_sources_azimuths.side_effect = Exception("ODAS error")
            
            follow_task.execute_task()
            
            # Should log the error (not exception) in the inner try-except block
            mock_logger.error.assert_called_once_with("Error in follow loop: ODAS error")
            mock_odas_processor.close.assert_called_once()
            mock_logger.info.assert_any_call("FollowTask completed")