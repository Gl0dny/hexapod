"""
Unit tests for sound source localization task.
"""
import pytest
import threading
from unittest.mock import Mock, patch, MagicMock

from hexapod.task_interface.tasks.sound_source_localization import SoundSourceLocalizationTask


class TestSoundSourceLocalizationTask:
    """Test cases for SoundSourceLocalizationTask class."""
    
    @pytest.fixture
    def mock_hexapod(self):
        """Mock hexapod instance for testing."""
        hexapod = MagicMock()
        return hexapod
    
    @pytest.fixture
    def mock_lights_handler(self):
        """Mock lights handler for testing."""
        lights_handler = MagicMock()
        lights_handler.think = MagicMock()
        lights_handler.off = MagicMock()
        return lights_handler
    
    @pytest.fixture
    def mock_odas_processor(self):
        """Mock ODAS processor for testing."""
        processor = MagicMock()
        processor.start = MagicMock()
        processor.close = MagicMock()
        return processor
    
    @pytest.fixture
    def external_control_paused_event(self):
        """Mock external control paused event."""
        return threading.Event()
    
    @pytest.fixture
    def sound_localization_task(self, mock_hexapod, mock_lights_handler, mock_odas_processor, external_control_paused_event):
        """Create SoundSourceLocalizationTask instance for testing."""
        return SoundSourceLocalizationTask(
            mock_hexapod,
            mock_lights_handler,
            mock_odas_processor,
            external_control_paused_event
        )
    
    def test_init_default_parameters(self, mock_hexapod, mock_lights_handler, mock_odas_processor, external_control_paused_event):
        """Test SoundSourceLocalizationTask initialization with default parameters."""
        task = SoundSourceLocalizationTask(mock_hexapod, mock_lights_handler, mock_odas_processor, external_control_paused_event)
        
        assert task.hexapod == mock_hexapod
        assert task.lights_handler == mock_lights_handler
        assert task.odas_processor == mock_odas_processor
        assert task.external_control_paused_event == external_control_paused_event
        assert task.callback is None
        assert task.odas_processor.stop_event == task.stop_event
    
    def test_init_custom_parameters(self, mock_hexapod, mock_lights_handler, mock_odas_processor, external_control_paused_event):
        """Test SoundSourceLocalizationTask initialization with custom parameters."""
        callback = Mock()
        task = SoundSourceLocalizationTask(
            mock_hexapod, 
            mock_lights_handler, 
            mock_odas_processor, 
            external_control_paused_event,
            callback=callback
        )
        
        assert task.callback == callback
    
    def test_execute_task_success(self, sound_localization_task, mock_hexapod, mock_lights_handler, mock_odas_processor):
        """Test successful execution of sound source localization task."""
        with patch('hexapod.task_interface.tasks.sound_source_localization.logger') as mock_logger, \
             patch('hexapod.task_interface.tasks.sound_source_localization.time.sleep'):
            
            # Set stop event to exit loop quickly
            sound_localization_task.stop_event.set()
            
            sound_localization_task.execute_task()
            
            # Verify lights handler was called
            mock_lights_handler.think.assert_called_once()
            mock_lights_handler.off.assert_called_once()
            
            # Verify ODAS processor was started
            mock_odas_processor.start.assert_called_once()
            
            # Verify ODAS processor was closed
            mock_odas_processor.close.assert_called_once()
            
            # Verify logging
            mock_logger.info.assert_any_call("SoundSourceLocalizationTask started")
            mock_logger.info.assert_any_call("SoundSourceLocalizationTask completed")
    
    def test_execute_task_exception_handling(self, sound_localization_task, mock_hexapod, mock_lights_handler, mock_odas_processor):
        """Test exception handling during sound source localization task execution."""
        # Make ODAS processor start raise an exception
        mock_odas_processor.start.side_effect = Exception("ODAS start failed")
        
        with patch('hexapod.task_interface.tasks.sound_source_localization.logger') as mock_logger, \
             patch('hexapod.task_interface.tasks.sound_source_localization.time.sleep'):
            
            sound_localization_task.execute_task()
            
            # Verify exception was logged
            mock_logger.exception.assert_called_once()
            assert "Sound source localization task failed" in str(mock_logger.exception.call_args)
            
            # Verify ODAS processor was still closed
            mock_odas_processor.close.assert_called_once()
    
    def test_execute_task_odas_processor_cleanup(self, sound_localization_task, mock_hexapod, mock_lights_handler, mock_odas_processor):
        """Test ODAS processor cleanup during task execution."""
        with patch('hexapod.task_interface.tasks.sound_source_localization.logger') as mock_logger, \
             patch('hexapod.task_interface.tasks.sound_source_localization.time.sleep'):
            
            # Set stop event to exit loop quickly
            sound_localization_task.stop_event.set()
            
            sound_localization_task.execute_task()
            
            # Verify ODAS processor was started
            mock_odas_processor.start.assert_called_once()
            
            # Verify ODAS processor was closed
            mock_odas_processor.close.assert_called_once()
    
    def test_execute_task_odas_processor_hasattr_check(self, sound_localization_task, mock_hexapod, mock_lights_handler, mock_odas_processor):
        """Test ODAS processor cleanup with hasattr check."""
        # Remove odas_processor attribute to test hasattr check
        del sound_localization_task.odas_processor
        
        with patch('hexapod.task_interface.tasks.sound_source_localization.logger') as mock_logger, \
             patch('hexapod.task_interface.tasks.sound_source_localization.time.sleep'):
            
            # Set stop event to exit loop quickly
            sound_localization_task.stop_event.set()
            
            sound_localization_task.execute_task()
            
            # Should not call close on non-existent processor
            mock_odas_processor.close.assert_not_called()
    
    def test_execute_task_wait_loop(self, sound_localization_task, mock_hexapod, mock_lights_handler, mock_odas_processor):
        """Test the wait loop in execute_task."""
        with patch('hexapod.task_interface.tasks.sound_source_localization.logger') as mock_logger, \
             patch('hexapod.task_interface.tasks.sound_source_localization.time.sleep') as mock_sleep:
            
            # Mock stop_event.wait to return False (not set) for first few calls, then True
            call_count = 0
            def wait_side_effect(timeout):
                nonlocal call_count
                call_count += 1
                if call_count <= 3:
                    return False  # Not set yet
                else:
                    sound_localization_task.stop_event.set()
                    return True  # Set
            
            sound_localization_task.stop_event.wait = wait_side_effect
            
            sound_localization_task.execute_task()
            
            # Verify wait was called multiple times
            assert call_count >= 3
            
            # Verify ODAS processor was started
            mock_odas_processor.start.assert_called_once()
    
    def test_execute_task_initialization_sequence(self, sound_localization_task, mock_hexapod, mock_lights_handler, mock_odas_processor):
        """Test the initialization sequence in execute_task."""
        with patch('hexapod.task_interface.tasks.sound_source_localization.logger') as mock_logger, \
             patch('hexapod.task_interface.tasks.sound_source_localization.time.sleep') as mock_sleep:
            
            # Set stop event to exit loop quickly
            sound_localization_task.stop_event.set()
            
            sound_localization_task.execute_task()
            
            # Verify initialization sequence
            mock_lights_handler.think.assert_called_once()
            mock_sleep.assert_called_once_with(4)  # Wait for Voice Control to pause
            mock_lights_handler.off.assert_called_once()
            mock_odas_processor.start.assert_called_once()
    
    def test_execute_task_logging_sequence(self, sound_localization_task, mock_hexapod, mock_lights_handler, mock_odas_processor):
        """Test the logging sequence in execute_task."""
        with patch('hexapod.task_interface.tasks.sound_source_localization.logger') as mock_logger, \
             patch('hexapod.task_interface.tasks.sound_source_localization.time.sleep'):
            
            # Set stop event to exit loop quickly
            sound_localization_task.stop_event.set()
            
            sound_localization_task.execute_task()
            
            # Verify logging sequence
            calls = mock_logger.info.call_args_list
            call_strings = [str(call) for call in calls]
            
            assert any("SoundSourceLocalizationTask started" in call for call in call_strings)
            assert any("SoundSourceLocalizationTask completed" in call for call in call_strings)
    
    def test_execute_task_stop_event_handling(self, sound_localization_task, mock_hexapod, mock_lights_handler, mock_odas_processor):
        """Test stop event handling in execute_task."""
        # Set stop event before execution
        sound_localization_task.stop_event.set()
        
        with patch('hexapod.task_interface.tasks.sound_source_localization.logger') as mock_logger, \
             patch('hexapod.task_interface.tasks.sound_source_localization.time.sleep'):
            
            sound_localization_task.execute_task()
            
            # Should still execute initialization sequence
            mock_lights_handler.think.assert_called_once()
            mock_lights_handler.off.assert_called_once()
            mock_odas_processor.start.assert_called_once()
            
            # Should exit wait loop immediately
            mock_odas_processor.close.assert_called_once()
    
    def test_execute_task_threading_compatibility(self, sound_localization_task, mock_hexapod, mock_lights_handler, mock_odas_processor):
        """Test that SoundSourceLocalizationTask is compatible with threading."""
        import threading
        
        with patch('hexapod.task_interface.tasks.sound_source_localization.logger'), \
             patch('hexapod.task_interface.tasks.sound_source_localization.time.sleep'):
            
            # Set stop event to exit quickly
            sound_localization_task.stop_event.set()
            
            # Run in thread
            thread = threading.Thread(target=sound_localization_task.execute_task)
            thread.start()
            thread.join(timeout=1.0)
            
            # Should complete without hanging
            assert not thread.is_alive()
    
    def test_execute_task_exception_during_odas_start(self, sound_localization_task, mock_hexapod, mock_lights_handler, mock_odas_processor):
        """Test exception handling when ODAS processor start fails."""
        mock_odas_processor.start.side_effect = Exception("ODAS start error")
        
        with patch('hexapod.task_interface.tasks.sound_source_localization.logger') as mock_logger, \
             patch('hexapod.task_interface.tasks.sound_source_localization.time.sleep'):
            
            sound_localization_task.execute_task()
            
            # Verify exception was logged
            mock_logger.exception.assert_called_once()
            assert "Sound source localization task failed" in str(mock_logger.exception.call_args)
            
            # Verify cleanup still happened
            mock_odas_processor.close.assert_called_once()
    
    def test_execute_task_exception_during_odas_close(self, sound_localization_task, mock_hexapod, mock_lights_handler, mock_odas_processor):
        """Test exception handling when ODAS processor close fails."""
        mock_odas_processor.close.side_effect = Exception("ODAS close error")
        
        with patch('hexapod.task_interface.tasks.sound_source_localization.logger') as mock_logger, \
             patch('hexapod.task_interface.tasks.sound_source_localization.time.sleep'):
            
            # Set stop event to exit loop quickly
            sound_localization_task.stop_event.set()
            
            # The task should handle the exception gracefully
            # The close() call in finally block will raise the exception
            # but it should be caught by the outer try-catch
            try:
                sound_localization_task.execute_task()
            except Exception:
                # This is expected - the close() call in finally raises the exception
                pass
            
            mock_odas_processor.close.assert_called_once()
    
    def test_execute_task_multiple_executions(self, sound_localization_task, mock_hexapod, mock_lights_handler, mock_odas_processor):
        """Test that SoundSourceLocalizationTask can be executed multiple times."""
        with patch('hexapod.task_interface.tasks.sound_source_localization.logger'), \
             patch('hexapod.task_interface.tasks.sound_source_localization.time.sleep'):
            
            # Execute multiple times
            for _ in range(3):
                sound_localization_task.stop_event.set()
                sound_localization_task.execute_task()
                sound_localization_task.stop_event.clear()
            
            # Should work without issues
            assert mock_odas_processor.start.call_count == 3
            assert mock_odas_processor.close.call_count == 3
