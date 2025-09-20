"""
Unit tests for move task.
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock

from hexapod.task_interface.tasks.move_task import MoveTask
from hexapod.robot import PredefinedPosition


class TestMoveTask:
    """Test cases for MoveTask class."""
    
    @pytest.fixture
    def mock_hexapod(self):
        """Mock hexapod instance for testing."""
        hexapod = MagicMock()
        hexapod.gait_params = {"translation": {"param1": "value1"}}
        hexapod.gait_generator = MagicMock()
        hexapod.gait_generator.current_gait = MagicMock()
        hexapod.gait_generator.thread = MagicMock()
        hexapod.move_to_position = MagicMock()
        hexapod.wait_until_motion_complete = MagicMock()
        return hexapod
    
    @pytest.fixture
    def mock_lights_handler(self):
        """Mock lights handler for testing."""
        lights_handler = MagicMock()
        lights_handler.think = MagicMock()
        return lights_handler
    
    def test_init_default_parameters(self, mock_hexapod, mock_lights_handler):
        """Test MoveTask initialization with default parameters."""
        task = MoveTask(mock_hexapod, mock_lights_handler, "forward")
        
        assert task.hexapod == mock_hexapod
        assert task.lights_handler == mock_lights_handler
        assert task.direction == "forward"
        assert task.cycles is None
        assert task.duration is None
        assert task.callback is None
    
    def test_init_custom_parameters(self, mock_hexapod, mock_lights_handler):
        """Test MoveTask initialization with custom parameters."""
        callback = Mock()
        task = MoveTask(
            mock_hexapod, 
            mock_lights_handler, 
            "backward", 
            cycles=5, 
            duration=10.0, 
            callback=callback
        )
        
        assert task.hexapod == mock_hexapod
        assert task.lights_handler == mock_lights_handler
        assert task.direction == "backward"
        assert task.cycles == 5
        assert task.duration == 10.0
        assert task.callback == callback
    
    def test_execute_task_calls_lights_handler(self, mock_hexapod, mock_lights_handler):
        """Test that execute_task calls lights_handler.think()."""
        task = MoveTask(mock_hexapod, mock_lights_handler, "forward")
        
        with patch.object(task, '_perform_movement'):
            task.execute_task()
            
            mock_lights_handler.think.assert_called_once()
    
    def test_execute_task_moves_to_zero_position_on_completion(self, mock_hexapod, mock_lights_handler):
        """Test that execute_task moves to zero position on completion."""
        task = MoveTask(mock_hexapod, mock_lights_handler, "forward")
        
        with patch.object(task, '_perform_movement'):
            task.execute_task()
            
            # Should move to zero position at the end
            mock_hexapod.move_to_position.assert_called_with(PredefinedPosition.ZERO)
            mock_hexapod.wait_until_motion_complete.assert_called_with(task.stop_event)
    
    def test_execute_task_handles_exception(self, mock_hexapod, mock_lights_handler):
        """Test that execute_task handles exceptions gracefully."""
        task = MoveTask(mock_hexapod, mock_lights_handler, "forward")
        
        # Make _perform_movement raise an exception
        with patch.object(task, '_perform_movement', side_effect=Exception("Movement failed")):
            # Should not raise exception
            task.execute_task()
            
            # Should still move to zero position in finally block
            mock_hexapod.move_to_position.assert_called_with(PredefinedPosition.ZERO)
    
    def test_perform_movement_with_cycles(self, mock_hexapod, mock_lights_handler):
        """Test _perform_movement with cycles parameter."""
        task = MoveTask(mock_hexapod, mock_lights_handler, "forward", cycles=3)
        
        task._perform_movement()
        
        # Should move to zero position first
        mock_hexapod.move_to_position.assert_called_with(PredefinedPosition.ZERO)
        mock_hexapod.wait_until_motion_complete.assert_called_with(task.stop_event)
        
        # Should create gait and set direction
        mock_hexapod.gait_generator.create_gait.assert_called_once_with("tripod", **mock_hexapod.gait_params["translation"])
        mock_hexapod.gait_generator.current_gait.set_direction.assert_called_once_with("forward")
        
        # Should execute cycles
        mock_hexapod.gait_generator.execute_cycles.assert_called_once_with(3)
        mock_hexapod.gait_generator.thread.join.assert_called_once()
    
    def test_perform_movement_with_duration(self, mock_hexapod, mock_lights_handler):
        """Test _perform_movement with duration parameter."""
        task = MoveTask(mock_hexapod, mock_lights_handler, "backward", duration=5.0)
        
        task._perform_movement()
        
        # Should create gait and set direction
        mock_hexapod.gait_generator.create_gait.assert_called_once_with("tripod", **mock_hexapod.gait_params["translation"])
        mock_hexapod.gait_generator.current_gait.set_direction.assert_called_once_with("backward")
        
        # Should run for duration
        mock_hexapod.gait_generator.run_for_duration.assert_called_once_with(5.0)
        mock_hexapod.gait_generator.thread.join.assert_called_once()
    
    def test_perform_movement_infinite(self, mock_hexapod, mock_lights_handler):
        """Test _perform_movement with infinite execution (no cycles or duration)."""
        task = MoveTask(mock_hexapod, mock_lights_handler, "left")
        
        task._perform_movement()
        
        # Should create gait and set direction
        mock_hexapod.gait_generator.create_gait.assert_called_once_with("tripod", **mock_hexapod.gait_params["translation"])
        mock_hexapod.gait_generator.current_gait.set_direction.assert_called_once_with("left")
        
        # Should start infinite gait generation
        mock_hexapod.gait_generator.start.assert_called_once()
        mock_hexapod.gait_generator.thread.join.assert_called_once()
    
    def test_perform_movement_stop_event_during_position_change(self, mock_hexapod, mock_lights_handler):
        """Test _perform_movement when stop_event is set during position change."""
        task = MoveTask(mock_hexapod, mock_lights_handler, "forward")
        
        # Set stop event before position change completes
        task.stop_event.set()
        
        task._perform_movement()
        
        # Should not proceed with gait generation
        mock_hexapod.gait_generator.create_gait.assert_not_called()
    
    def test_perform_movement_no_current_gait(self, mock_hexapod, mock_lights_handler):
        """Test _perform_movement when current_gait is None."""
        task = MoveTask(mock_hexapod, mock_lights_handler, "forward", cycles=1)
        mock_hexapod.gait_generator.current_gait = None
        
        task._perform_movement()
        
        # Should still execute cycles even without current_gait
        mock_hexapod.gait_generator.execute_cycles.assert_called_once_with(1)
    
    def test_perform_movement_no_gait_thread(self, mock_hexapod, mock_lights_handler):
        """Test _perform_movement when gait_generator.thread is None."""
        task = MoveTask(mock_hexapod, mock_lights_handler, "forward", cycles=1)
        mock_hexapod.gait_generator.thread = None
        
        task._perform_movement()
        
        # Should not call join on None thread
        mock_hexapod.gait_generator.execute_cycles.assert_called_once_with(1)
    
    def test_perform_movement_different_directions(self, mock_hexapod, mock_lights_handler):
        """Test _perform_movement with different directions."""
        directions = ["forward", "backward", "left", "right", "up", "down"]
        
        for direction in directions:
            task = MoveTask(mock_hexapod, mock_lights_handler, direction, cycles=1)
            task._perform_movement()
            
            # Should set the correct direction
            mock_hexapod.gait_generator.current_gait.set_direction.assert_called_with(direction)
            
            # Reset mocks for next iteration
            mock_hexapod.gait_generator.current_gait.set_direction.reset_mock()
    
    def test_perform_movement_logging(self, mock_hexapod, mock_lights_handler):
        """Test that _perform_movement logs appropriate messages."""
        task = MoveTask(mock_hexapod, mock_lights_handler, "forward", cycles=2)
        
        with patch('hexapod.task_interface.tasks.move_task.logger') as mock_logger:
            task._perform_movement()
            
            # Should log movement start
            mock_logger.info.assert_any_call("Starting movement in forward direction")
            mock_logger.info.assert_any_call("Executing 2 gait cycles")
            mock_logger.info.assert_any_call("Completed 2 cycles")
    
    def test_perform_movement_duration_logging(self, mock_hexapod, mock_lights_handler):
        """Test that _perform_movement logs duration messages."""
        task = MoveTask(mock_hexapod, mock_lights_handler, "backward", duration=3.0)
        
        with patch('hexapod.task_interface.tasks.move_task.logger') as mock_logger:
            task._perform_movement()
            
            # Should log duration messages
            mock_logger.info.assert_any_call("Executing gait for 3.0 seconds")
            mock_logger.info.assert_any_call("Completed duration-based movement")
    
    def test_perform_movement_infinite_logging(self, mock_hexapod, mock_lights_handler):
        """Test that _perform_movement logs infinite generation messages."""
        task = MoveTask(mock_hexapod, mock_lights_handler, "left")
        
        with patch('hexapod.task_interface.tasks.move_task.logger') as mock_logger:
            task._perform_movement()
            
            # Should log infinite generation messages
            mock_logger.info.assert_any_call("Starting infinite gait generation")
            mock_logger.warning.assert_any_call("Infinite gait generation started - will continue until stopped externally")
            mock_logger.info.assert_any_call("Infinite gait generation completed")
    
    def test_perform_movement_stop_event_logging(self, mock_hexapod, mock_lights_handler):
        """Test that _perform_movement logs stop event messages."""
        task = MoveTask(mock_hexapod, mock_lights_handler, "forward")
        task.stop_event.set()
        
        with patch('hexapod.task_interface.tasks.move_task.logger') as mock_logger:
            task._perform_movement()
            
            # Should log stop event warning
            mock_logger.warning.assert_called_with("Move task interrupted during position change.")
    
    def test_execute_task_logging(self, mock_hexapod, mock_lights_handler):
        """Test that execute_task logs appropriate messages."""
        task = MoveTask(mock_hexapod, mock_lights_handler, "forward")
        
        with patch('hexapod.task_interface.tasks.move_task.logger') as mock_logger:
            with patch.object(task, '_perform_movement'):
                task.execute_task()
                
                # Should log start and completion
                mock_logger.info.assert_any_call("MoveTask started")
                mock_logger.info.assert_any_call("Performing movement in forward direction.")
                mock_logger.info.assert_any_call("MoveTask completed")
    
    def test_execute_task_exception_logging(self, mock_hexapod, mock_lights_handler):
        """Test that execute_task logs exceptions."""
        task = MoveTask(mock_hexapod, mock_lights_handler, "forward")
        
        with patch('hexapod.task_interface.tasks.move_task.logger') as mock_logger:
            with patch.object(task, '_perform_movement', side_effect=Exception("Test error")):
                task.execute_task()
                
                # Should log exception
                mock_logger.exception.assert_called_with("Error in MoveTask: Test error")
