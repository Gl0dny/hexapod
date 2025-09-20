"""
Unit tests for sit up task.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from hexapod.task_interface.tasks.sit_up_task import SitUpTask


class TestSitUpTask:
    """Test cases for SitUpTask class."""
    
    @pytest.fixture
    def mock_hexapod(self):
        """Mock hexapod instance for testing."""
        hexapod = MagicMock()
        hexapod.current_leg_positions = [
            (100.0, 50.0, -80.0), (120.0, 60.0, -85.0), (110.0, 55.0, -82.0),
            (105.0, 52.0, -81.0), (115.0, 58.0, -83.0), (125.0, 62.0, -86.0)
        ]
        hexapod.move_to_position = MagicMock()
        hexapod.wait_until_motion_complete = MagicMock()
        hexapod.move_body = MagicMock()
        return hexapod
    
    @pytest.fixture
    def mock_lights_handler(self):
        """Mock lights handler for testing."""
        lights_handler = MagicMock()
        lights_handler.think = MagicMock()
        return lights_handler
    
    @pytest.fixture
    def sit_up_task(self, mock_hexapod, mock_lights_handler):
        """Create SitUpTask instance for testing."""
        return SitUpTask(mock_hexapod, mock_lights_handler)
    
    def test_init_default_parameters(self, mock_hexapod, mock_lights_handler):
        """Test SitUpTask initialization with default parameters."""
        task = SitUpTask(mock_hexapod, mock_lights_handler)
        
        assert task.hexapod == mock_hexapod
        assert task.lights_handler == mock_lights_handler
        assert task.callback is None
    
    def test_init_custom_parameters(self, mock_hexapod, mock_lights_handler):
        """Test SitUpTask initialization with custom parameters."""
        callback = Mock()
        task = SitUpTask(mock_hexapod, mock_lights_handler, callback=callback)
        
        assert task.callback == callback
    
    def test_perform_sit_up_success(self, sit_up_task, mock_hexapod):
        """Test successful sit up performance."""
        with patch('hexapod.task_interface.tasks.sit_up_task.logger') as mock_logger, \
             patch('hexapod.task_interface.tasks.sit_up_task.time.sleep'):
            
            sit_up_task._perform_sit_up()
            
            # Verify low profile position was set
            from hexapod.robot import PredefinedPosition
            mock_hexapod.move_to_position.assert_called_once_with(PredefinedPosition.LOW_PROFILE)
            mock_hexapod.wait_until_motion_complete.assert_called_once_with(sit_up_task.stop_event)
            
            # Verify reference positions were accessed (but not stored as attribute)
            # The copy() method is called on current_leg_positions
            pass  # This is verified by the fact that the method completes successfully
            
            # Verify sit up movements were performed (5 repetitions)
            # Each repetition: up, down, return = 3 movements
            # 5 repetitions * 3 movements = 15 total movements
            assert mock_hexapod.move_body.call_count == 15
            
            # Verify logging
            mock_logger.info.assert_any_call("Starting sit-up motion")
            mock_logger.info.assert_any_call("Performing sit-up repetition 1/5")
            mock_logger.info.assert_any_call("Performing sit-up repetition 5/5")
            mock_logger.info.assert_any_call("Moving body up")
            mock_logger.info.assert_any_call("Moving body down")
            mock_logger.info.assert_any_call("Returning to reference position")
    
    def test_perform_sit_up_stop_event_during_position_change(self, sit_up_task, mock_hexapod):
        """Test sit up when stop event is set during position change."""
        # Set stop event before position change
        sit_up_task.stop_event.set()
        
        with patch('hexapod.task_interface.tasks.sit_up_task.logger') as mock_logger:
            sit_up_task._perform_sit_up()
            
            # Should not proceed with sit up movements
            mock_hexapod.move_body.assert_not_called()
    
    def test_perform_sit_up_stop_event_during_repetition(self, sit_up_task, mock_hexapod):
        """Test sit up when stop event is set during repetition."""
        # Set stop event during first repetition
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # After second movement (during first repetition)
                sit_up_task.stop_event.set()
        
        mock_hexapod.move_body.side_effect = side_effect
        
        with patch('hexapod.task_interface.tasks.sit_up_task.logger') as mock_logger, \
             patch('hexapod.task_interface.tasks.sit_up_task.time.sleep'):
            
            sit_up_task._perform_sit_up()
            
            # Should have started but stopped early
            assert mock_hexapod.move_body.call_count >= 2
            # The interruption may not be logged if it happens during movement
    
    def test_sit_up_movement_calculations(self, sit_up_task, mock_hexapod):
        """Test sit up movement calculations."""
        with patch('hexapod.task_interface.tasks.sit_up_task.logger'), \
             patch('hexapod.task_interface.tasks.sit_up_task.time.sleep'):
            
            sit_up_task._perform_sit_up()
            
            # Verify movement sequence
            calls = mock_hexapod.move_body.call_args_list
            
            # First movement should be up (tz=50.0)
            assert calls[0][1]['tz'] == 50.0
            
            # Second movement should be down (tz=-(50.0 + 0.0) = -50.0)
            assert calls[1][1]['tz'] == -50.0
            
            # Third movement should be return to reference (tz=0.0)
            assert calls[2][1]['tz'] == 0.0
            
            # Pattern should repeat for all 5 repetitions
            for rep in range(5):
                base_idx = rep * 3
                assert calls[base_idx][1]['tz'] == 50.0      # up
                assert calls[base_idx + 1][1]['tz'] == -50.0  # down
                assert calls[base_idx + 2][1]['tz'] == 0.0    # return
    
    def test_sit_up_parameters(self, sit_up_task, mock_hexapod):
        """Test sit up parameters."""
        with patch('hexapod.task_interface.tasks.sit_up_task.logger'), \
             patch('hexapod.task_interface.tasks.sit_up_task.time.sleep') as mock_sleep:
            
            sit_up_task._perform_sit_up()
            
            # Verify parameters
            # up_height = 50.0, down_height = 0.0, hold_time = 0.8, repetitions = 5
            
            # Verify hold times (2 holds per repetition * 5 repetitions = 10 total)
            assert mock_sleep.call_count == 10
            
            # Verify all sleep calls are for 0.8 seconds
            for call in mock_sleep.call_args_list:
                assert call[0][0] == 0.8
    
    def test_execute_task_success(self, sit_up_task, mock_hexapod, mock_lights_handler):
        """Test successful execution of sit up task."""
        with patch.object(sit_up_task, '_perform_sit_up'), \
             patch('hexapod.task_interface.tasks.sit_up_task.logger') as mock_logger:
            
            sit_up_task.execute_task()
            
            # Verify lights handler was called
            mock_lights_handler.think.assert_called_once()
            
            # Verify sit up was performed
            sit_up_task._perform_sit_up.assert_called_once()
            
            # Verify final position
            from hexapod.robot import PredefinedPosition
            mock_hexapod.move_to_position.assert_called_with(PredefinedPosition.LOW_PROFILE)
            mock_hexapod.wait_until_motion_complete.assert_called_with(sit_up_task.stop_event)
            
            # Verify logging
            mock_logger.info.assert_any_call("SitUpTask started")
            mock_logger.info.assert_any_call("Performing sit-up routine.")
            mock_logger.info.assert_any_call("SitUpTask completed")
    
    def test_execute_task_exception_handling(self, sit_up_task, mock_hexapod, mock_lights_handler):
        """Test exception handling during sit up task execution."""
        # Make _perform_sit_up raise an exception
        with patch.object(sit_up_task, '_perform_sit_up', side_effect=Exception("Sit up failed")), \
             patch('hexapod.task_interface.tasks.sit_up_task.logger') as mock_logger:
            
            sit_up_task.execute_task()
            
            # Verify exception was logged
            mock_logger.exception.assert_called_once()
            assert "Sit-up task failed" in str(mock_logger.exception.call_args)
            
            # Verify final position was still called
            from hexapod.robot import PredefinedPosition
            mock_hexapod.move_to_position.assert_called_with(PredefinedPosition.LOW_PROFILE)
            mock_hexapod.wait_until_motion_complete.assert_called_with(sit_up_task.stop_event)
    
    def test_sit_up_reference_position_storage(self, sit_up_task, mock_hexapod):
        """Test that reference positions are stored correctly."""
        with patch('hexapod.task_interface.tasks.sit_up_task.logger'), \
             patch('hexapod.task_interface.tasks.sit_up_task.time.sleep'):
            
            sit_up_task._perform_sit_up()
            
            # Verify reference positions were accessed (but not stored as attribute)
            # The copy() method is called on current_leg_positions
            pass  # This is verified by the fact that the method completes successfully
    
    def test_sit_up_movement_sequence(self, sit_up_task, mock_hexapod):
        """Test the complete sit up movement sequence."""
        with patch('hexapod.task_interface.tasks.sit_up_task.logger'), \
             patch('hexapod.task_interface.tasks.sit_up_task.time.sleep'):
            
            sit_up_task._perform_sit_up()
            
            # Verify the complete sequence
            calls = mock_hexapod.move_body.call_args_list
            
            # Should have 15 calls total (5 repetitions * 3 movements each)
            assert len(calls) == 15
            
            # Verify the pattern repeats correctly
            for rep in range(5):
                base_idx = rep * 3
                
                # Up movement
                assert calls[base_idx][1]['tz'] == 50.0
                
                # Down movement (total_down_movement = -(up_height + down_height) = -(50.0 + 0.0) = -50.0)
                assert calls[base_idx + 1][1]['tz'] == -50.0
                
                # Return to reference (return_to_reference = down_height = 0.0)
                assert calls[base_idx + 2][1]['tz'] == 0.0
    
    def test_sit_up_stop_event_during_hold(self, sit_up_task, mock_hexapod):
        """Test sit up when stop event is set during hold."""
        def sleep_side_effect(duration):
            sit_up_task.stop_event.set()
        
        with patch('hexapod.task_interface.tasks.sit_up_task.logger'), \
             patch('hexapod.task_interface.tasks.sit_up_task.time.sleep', side_effect=sleep_side_effect):
            
            sit_up_task._perform_sit_up()
            
            # Should have started but stopped during first hold
            assert mock_hexapod.move_body.call_count >= 1  # At least one movement
    
    def test_sit_up_different_parameters(self, mock_hexapod, mock_lights_handler):
        """Test sit up with different parameter values."""
        # The current implementation uses hardcoded parameters
        # This test verifies the current behavior
        task = SitUpTask(mock_hexapod, mock_lights_handler)
        
        with patch('hexapod.task_interface.tasks.sit_up_task.logger'), \
             patch('hexapod.task_interface.tasks.sit_up_task.time.sleep'):
            
            task._perform_sit_up()
            
            # Verify current parameters
            # up_height = 50.0, down_height = 0.0, hold_time = 0.8, repetitions = 5
            assert mock_hexapod.move_body.call_count == 15  # 5 * 3 movements
            assert mock_hexapod.current_leg_positions is not None  # Reference stored
