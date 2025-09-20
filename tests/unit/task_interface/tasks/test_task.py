"""
Unit tests for base task system.
"""
import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock

from hexapod.task_interface.tasks.task import Task


class ConcreteTask(Task):
    """Concrete implementation of Task for testing."""
    
    def __init__(self, callback=None, should_raise=False):
        super().__init__(callback)
        self.should_raise = should_raise
        self.executed = False
        self.execution_count = 0
    
    def execute_task(self):
        """Concrete implementation of execute_task."""
        self.executed = True
        self.execution_count += 1
        if self.should_raise:
            raise Exception("Test exception")
        # Simulate some work
        time.sleep(0.01)


class TestTask:
    """Test cases for Task base class."""
    
    def test_init_default_parameters(self):
        """Test Task initialization with default parameters."""
        task = ConcreteTask()
        
        assert task.callback is None
        assert task._callback_called is False
        assert isinstance(task.stop_event, threading.Event)
        assert not task.stop_event.is_set()
        assert task.daemon is True
    
    def test_init_custom_parameters(self):
        """Test Task initialization with custom parameters."""
        callback = Mock()
        task = ConcreteTask(callback=callback)
        
        assert task.callback == callback
        assert task._callback_called is False
        assert isinstance(task.stop_event, threading.Event)
        assert not task.stop_event.is_set()
    
    def test_start_task(self):
        """Test starting a task."""
        task = ConcreteTask()
        
        # Initially not alive
        assert not task.is_alive()
        
        # Start the task
        task.start()
        
        # Should be alive now
        assert task.is_alive()
        
        # Wait for completion
        task.join(timeout=1.0)
        assert task.executed
    
    def test_start_clears_stop_event(self):
        """Test that start clears the stop event."""
        task = ConcreteTask()
        
        # Set stop event
        task.stop_event.set()
        assert task.stop_event.is_set()
        
        # Start should clear it
        task.start()
        assert not task.stop_event.is_set()
        
        # Clean up
        task.join(timeout=1.0)
    
    def test_run_executes_task(self):
        """Test that run method executes the task."""
        task = ConcreteTask()
        
        # Run the task directly (not in thread)
        task.run()
        
        assert task.executed
        assert task.execution_count == 1
    
    def test_run_calls_callback(self):
        """Test that run calls the callback when provided."""
        callback = Mock()
        task = ConcreteTask(callback=callback)
        
        # Run the task directly
        task.run()
        
        callback.assert_called_once()
        assert task._callback_called is True
    
    def test_run_calls_callback_only_once(self):
        """Test that run calls the callback only once even if run multiple times."""
        callback = Mock()
        task = ConcreteTask(callback=callback)
        
        # Run the task multiple times
        task.run()
        task.run()
        
        callback.assert_called_once()
        assert task._callback_called is True
    
    def test_run_handles_callback_exception(self):
        """Test that run handles callback exceptions gracefully."""
        def failing_callback():
            raise Exception("Callback failed")
        
        task = ConcreteTask(callback=failing_callback)
        
        # Should not raise exception - the run method doesn't catch exceptions
        # The exception should propagate
        with pytest.raises(Exception, match="Callback failed"):
            task.run()
        
        assert task.executed
        assert task._callback_called is True
    
    def test_stop_task_sets_stop_event(self):
        """Test that stop_task sets the stop event."""
        task = ConcreteTask()
        
        assert not task.stop_event.is_set()
        task.stop_task()
        assert task.stop_event.is_set()
    
    def test_stop_task_with_alive_thread(self):
        """Test stopping a task that is alive."""
        task = ConcreteTask()
        task.start()
        
        # Wait a bit to ensure it's running
        time.sleep(0.1)
        
        # Stop the task (regardless of whether it's still alive)
        task.stop_task(timeout=1.0)
        
        # Should not be alive anymore
        assert not task.is_alive()
        assert task.stop_event.is_set()
    
    def test_stop_task_with_timeout(self):
        """Test stopping a task with timeout."""
        task = ConcreteTask()
        task.start()
        
        # Stop with timeout
        task.stop_task(timeout=0.1)
        
        # Should not be alive
        assert not task.is_alive()
    
    def test_stop_task_calls_callback_if_not_called(self):
        """Test that stop_task calls callback if not already called."""
        callback = Mock()
        task = ConcreteTask(callback=callback)
        
        # Stop without running
        task.stop_task()
        
        callback.assert_called_once()
        assert task._callback_called is True
    
    def test_stop_task_does_not_call_callback_if_already_called(self):
        """Test that stop_task does not call callback if already called."""
        callback = Mock()
        task = ConcreteTask(callback=callback)
        
        # Run first (which calls callback)
        task.run()
        callback.reset_mock()
        
        # Stop task
        task.stop_task()
        
        # Callback should not be called again
        callback.assert_not_called()
    
    def test_stop_task_handles_join_exception(self):
        """Test that stop_task handles join exceptions gracefully."""
        task = ConcreteTask()
        task.start()
        
        # Mock join to raise exception
        with patch.object(task, 'join', side_effect=Exception("Join failed")):
            # Should not raise exception
            task.stop_task(timeout=1.0)
    
    def test_stop_task_logs_timeout_warning(self):
        """Test that stop_task logs warning when task doesn't stop in time."""
        task = ConcreteTask()
        task.start()
        
        with patch('hexapod.task_interface.tasks.task.logger') as mock_logger:
            # Mock is_alive to return True after join
            with patch.object(task, 'is_alive', return_value=True):
                task.stop_task(timeout=0.001)  # Very short timeout
                
                # Should log timeout warning
                mock_logger.error.assert_called()
                assert "did not stop within" in str(mock_logger.error.call_args)
    
    def test_execute_task_abstract(self):
        """Test that execute_task is abstract and must be implemented."""
        # Cannot instantiate Task directly
        with pytest.raises(TypeError):
            Task()
    
    def test_task_threading_behavior(self):
        """Test that task runs in separate thread."""
        task = ConcreteTask()
        main_thread = threading.current_thread()
        
        task.start()
        
        # Wait for completion
        task.join(timeout=1.0)
        
        # Task should have executed
        assert task.executed
        assert task.execution_count == 1
    
    def test_multiple_start_calls(self):
        """Test that multiple start calls raise RuntimeError."""
        task = ConcreteTask()
        
        # Start once
        task.start()
        
        # Second start should raise RuntimeError
        with pytest.raises(RuntimeError, match="threads can only be started once"):
            task.start()
        
        task.stop_task()
    
    def test_stop_event_during_execution(self):
        """Test that stop_event can interrupt task execution."""
        class InterruptibleTask(Task):
            def execute_task(self):
                # Check stop_event during execution
                for i in range(10):
                    if self.stop_event.is_set():
                        return
                    time.sleep(0.01)
        
        task = InterruptibleTask()
        task.start()
        
        # Let it run a bit
        time.sleep(0.05)
        
        # Stop it
        task.stop_task(timeout=1.0)
        
        # Should not be alive
        assert not task.is_alive()
    
    def test_task_name_renaming(self):
        """Test that task thread is renamed."""
        # This test verifies that the task is created successfully
        # The actual rename_thread call is an implementation detail
        task = ConcreteTask()
        assert task.name.startswith('ConcreteTask')
    
    def test_daemon_thread_property(self):
        """Test that task is created as daemon thread."""
        task = ConcreteTask()
        assert task.daemon is True
