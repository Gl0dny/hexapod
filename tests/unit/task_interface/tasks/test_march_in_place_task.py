"""
Unit tests for march in place task.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from hexapod.task_interface.tasks.march_in_place_task import MarchInPlaceTask


class TestMarchInPlaceTask:
    """Test cases for MarchInPlaceTask class."""
    
    @pytest.fixture
    def mock_hexapod(self):
        """Mock hexapod instance for testing."""
        hexapod = MagicMock()
        hexapod.gait_generator = MagicMock()
        hexapod.gait_generator.thread = MagicMock()
        hexapod.gait_params = {"translation": {"param1": "value1"}}
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
    def march_task_default(self, mock_hexapod, mock_lights_handler):
        """Create MarchInPlaceTask instance with default parameters."""
        return MarchInPlaceTask(mock_hexapod, mock_lights_handler)
    
    @pytest.fixture
    def march_task_with_duration(self, mock_hexapod, mock_lights_handler):
        """Create MarchInPlaceTask instance with duration."""
        return MarchInPlaceTask(mock_hexapod, mock_lights_handler, duration=5.0)
    
    def test_init_default_parameters(self, mock_hexapod, mock_lights_handler):
        """Test MarchInPlaceTask initialization with default parameters."""
        task = MarchInPlaceTask(mock_hexapod, mock_lights_handler)
        
        assert task.hexapod == mock_hexapod
        assert task.lights_handler == mock_lights_handler
        assert task.duration is None
        assert task.callback is None
    
    def test_init_custom_parameters(self, mock_hexapod, mock_lights_handler):
        """Test MarchInPlaceTask initialization with custom parameters."""
        callback = Mock()
        task = MarchInPlaceTask(mock_hexapod, mock_lights_handler, duration=10.0, callback=callback)
        
        assert task.hexapod == mock_hexapod
        assert task.lights_handler == mock_lights_handler
        assert task.duration == 10.0
        assert task.callback == callback
    
    def test_perform_march_with_duration(self, march_task_with_duration, mock_hexapod):
        """Test performing march with duration."""
        with patch('hexapod.task_interface.tasks.march_in_place_task.logger') as mock_logger:
            march_task_with_duration._perform_march()
            
            # Verify zero position was set
            from hexapod.robot import PredefinedPosition
            mock_hexapod.move_to_position.assert_called_once_with(PredefinedPosition.ZERO)
            mock_hexapod.wait_until_motion_complete.assert_called_once_with(march_task_with_duration.stop_event)
            
            # Verify gait was created with correct parameters
            expected_params = {
                "param1": "value1",
                "step_radius": 0.0,
                "leg_lift_distance": 30.0,
                "dwell_time": 0.3
            }
            mock_hexapod.gait_generator.create_gait.assert_called_once_with("tripod", **expected_params)
            
            # Verify duration-based execution
            mock_hexapod.gait_generator.run_for_duration.assert_called_once_with(5.0)
            mock_hexapod.gait_generator.thread.join.assert_called_once()
            
            # Verify logging
            mock_logger.info.assert_any_call("Starting marching in place motion")
            mock_logger.info.assert_any_call("Marching in place for 5.0 seconds")
            mock_logger.info.assert_any_call("Started marching in place for 5.0 seconds in background thread")
            mock_logger.info.assert_any_call("Completed marching in place for 5.0 seconds")
    
    def test_perform_march_infinite(self, march_task_default, mock_hexapod):
        """Test performing infinite march."""
        with patch('hexapod.task_interface.tasks.march_in_place_task.logger') as mock_logger:
            march_task_default._perform_march()
            
            # Verify gait was created
            expected_params = {
                "param1": "value1",
                "step_radius": 0.0,
                "leg_lift_distance": 30.0,
                "dwell_time": 0.3
            }
            mock_hexapod.gait_generator.create_gait.assert_called_once_with("tripod", **expected_params)
            
            # Verify infinite execution
            mock_hexapod.gait_generator.start.assert_called_once()
            mock_hexapod.gait_generator.thread.join.assert_called_once()
            
            # Verify logging
            mock_logger.info.assert_any_call("Starting infinite marching in place")
            mock_logger.warning.assert_any_call("Infinite marching started - will continue until stopped externally")
            mock_logger.info.assert_any_call("Infinite marching completed")
    
    def test_perform_march_stop_event_during_position_change(self, march_task_default, mock_hexapod):
        """Test march when stop event is set during position change."""
        # Set stop event before position change
        march_task_default.stop_event.set()
        
        with patch('hexapod.task_interface.tasks.march_in_place_task.logger') as mock_logger:
            march_task_default._perform_march()
            
            # Should not proceed with gait creation
            mock_hexapod.gait_generator.create_gait.assert_not_called()
            
            # Verify warning was logged
            mock_logger.warning.assert_called_once_with("March task interrupted during position change.")
    
    def test_perform_march_no_gait_thread(self, march_task_with_duration, mock_hexapod):
        """Test march when gait generator thread is None."""
        mock_hexapod.gait_generator.thread = None
        
        with patch('hexapod.task_interface.tasks.march_in_place_task.logger') as mock_logger:
            march_task_with_duration._perform_march()
            
            # Should not call join on None thread
            # The method should handle this gracefully
            mock_logger.info.assert_any_call("Completed marching in place for 5.0 seconds")
    
    def test_execute_task_success(self, march_task_with_duration, mock_hexapod, mock_lights_handler):
        """Test successful execution of march task."""
        with patch.object(march_task_with_duration, '_perform_march'), \
             patch('hexapod.task_interface.tasks.march_in_place_task.logger') as mock_logger:
            
            march_task_with_duration.execute_task()
            
            # Verify lights handler was called
            mock_lights_handler.think.assert_called_once()
            
            # Verify march was performed
            march_task_with_duration._perform_march.assert_called_once()
            
            # Verify final position
            from hexapod.robot import PredefinedPosition
            mock_hexapod.move_to_position.assert_called_with(PredefinedPosition.ZERO)
            mock_hexapod.wait_until_motion_complete.assert_called_with(march_task_with_duration.stop_event)
            
            # Verify logging
            mock_logger.info.assert_any_call("MarchTask started")
            mock_logger.info.assert_any_call("Performing marching routine.")
            mock_logger.info.assert_any_call("MarchTask completed")
    
    def test_execute_task_exception_handling(self, march_task_with_duration, mock_hexapod, mock_lights_handler):
        """Test exception handling during march task execution."""
        # Make _perform_march raise an exception
        with patch.object(march_task_with_duration, '_perform_march', side_effect=Exception("March failed")), \
             patch('hexapod.task_interface.tasks.march_in_place_task.logger') as mock_logger:
            
            march_task_with_duration.execute_task()
            
            # Verify exception was logged
            mock_logger.exception.assert_called_once()
            assert "Error in MarchTask" in str(mock_logger.exception.call_args)
            
            # Verify final position was still called
            from hexapod.robot import PredefinedPosition
            mock_hexapod.move_to_position.assert_called_with(PredefinedPosition.ZERO)
            mock_hexapod.wait_until_motion_complete.assert_called_with(march_task_with_duration.stop_event)
    
    def test_gait_parameters_customization(self, march_task_with_duration, mock_hexapod):
        """Test that gait parameters are customized for marching."""
        with patch('hexapod.task_interface.tasks.march_in_place_task.logger'):
            march_task_with_duration._perform_march()
            
            # Verify gait was created with marching-specific parameters
            call_args = mock_hexapod.gait_generator.create_gait.call_args
            gait_params = call_args[1]
            
            assert gait_params["step_radius"] == 0.0  # No forward movement
            assert gait_params["leg_lift_distance"] == 30.0  # Lift legs 30mm
            assert gait_params["dwell_time"] == 0.3  # Fast stepping for marching
            assert gait_params["param1"] == "value1"  # Original parameters preserved
    
    def test_different_durations(self, mock_hexapod, mock_lights_handler):
        """Test march task with different durations."""
        durations = [1.0, 5.0, 10.0, 30.0]
        
        for duration in durations:
            task = MarchInPlaceTask(mock_hexapod, mock_lights_handler, duration=duration)
            
            with patch('hexapod.task_interface.tasks.march_in_place_task.logger'):
                task._perform_march()
                
                # Verify duration was used
                mock_hexapod.gait_generator.run_for_duration.assert_called_with(duration)
                
                # Reset mocks for next iteration
                mock_hexapod.gait_generator.reset_mock()
    
    def test_march_task_threading_behavior(self, march_task_with_duration, mock_hexapod):
        """Test that march task properly handles threading."""
        with patch('hexapod.task_interface.tasks.march_in_place_task.logger'):
            march_task_with_duration._perform_march()
            
            # Verify thread operations
            mock_hexapod.gait_generator.run_for_duration.assert_called_once()
            mock_hexapod.gait_generator.thread.join.assert_called_once()
    
    def test_march_task_stop_event_handling(self, march_task_with_duration, mock_hexapod):
        """Test that march task properly handles stop events."""
        # Set stop event before execution
        march_task_with_duration.stop_event.set()
        
        with patch('hexapod.task_interface.tasks.march_in_place_task.logger') as mock_logger:
            march_task_with_duration._perform_march()
            
            # Should not proceed with gait creation
            mock_hexapod.gait_generator.create_gait.assert_not_called()
            
            # Verify warning was logged
            mock_logger.warning.assert_called_once_with("March task interrupted during position change.")
