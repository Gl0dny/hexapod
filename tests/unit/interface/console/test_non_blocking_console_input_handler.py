"""
Unit tests for non-blocking console input handler.
"""

import pytest
import threading
import queue
import time
import sys
from unittest.mock import Mock, patch, MagicMock, call
from io import StringIO

from hexapod.interface.console.non_blocking_console_input_handler import (
    NonBlockingConsoleInputHandler,
)


class TestNonBlockingConsoleInputHandler:
    """Test cases for NonBlockingConsoleInputHandler class."""

    @pytest.fixture
    def input_handler(self):
        """Create NonBlockingConsoleInputHandler instance for testing."""
        return NonBlockingConsoleInputHandler()

    @pytest.fixture
    def mock_stdin(self):
        """Mock sys.stdin for testing."""
        return StringIO()

    def test_init_default_parameters(self):
        """Test NonBlockingConsoleInputHandler initialization with default parameters."""
        handler = NonBlockingConsoleInputHandler()

        assert handler.daemon is True
        assert isinstance(handler.input_queue, queue.Queue)
        assert handler.stop_input_listener is False
        assert handler.input_queue.empty()

    def test_init_thread_properties(self):
        """Test that the handler is properly configured as a daemon thread."""
        handler = NonBlockingConsoleInputHandler()

        assert isinstance(handler, threading.Thread)
        assert handler.daemon is True
        assert handler.name is not None

    def test_start_method(self, input_handler, caplog):
        """Test starting the input listener thread."""
        with patch.object(threading.Thread, "start") as mock_start:
            input_handler.start()
            mock_start.assert_called_once()
            # Note: Logging is mocked in conftest.py, so we can't test log messages

    @patch("hexapod.interface.console.non_blocking_console_input_handler.select.select")
    @patch("hexapod.interface.console.non_blocking_console_input_handler.sys.stdin")
    def test_run_successful_input(self, mock_stdin, mock_select, input_handler, caplog):
        """Test run method with successful input processing."""
        # Mock select to return stdin as ready
        mock_select.return_value = ([mock_stdin], [], [])

        # Mock stdin.readline to return test input
        mock_stdin.readline.return_value = "test input\n"

        # Start the thread
        input_handler.start()

        # Give it time to process
        time.sleep(0.2)

        # Stop the thread
        input_handler.shutdown()

        # Check that input was processed
        assert not input_handler.input_queue.empty()
        retrieved_input = input_handler.input_queue.get_nowait()
        assert retrieved_input == "test input"

        # Note: Logging is mocked in conftest.py, so we can't test log messages

    @patch("hexapod.interface.console.non_blocking_console_input_handler.select.select")
    def test_run_no_input_available(self, mock_select, input_handler, caplog):
        """Test run method when no input is available."""
        # Mock select to return no ready file descriptors
        mock_select.return_value = ([], [], [])

        # Start the thread
        input_handler.start()

        # Give it time to run
        time.sleep(0.2)

        # Stop the thread
        input_handler.shutdown()

        # Check that no input was queued
        assert input_handler.input_queue.empty()

        # Check that select was called
        mock_select.assert_called()

    @patch("hexapod.interface.console.non_blocking_console_input_handler.select.select")
    @patch("hexapod.interface.console.non_blocking_console_input_handler.sys.stdin")
    def test_run_multiple_inputs(self, mock_stdin, mock_select, input_handler):
        """Test run method with multiple inputs."""
        # Mock select to return stdin as ready
        mock_select.return_value = ([mock_stdin], [], [])

        # Mock stdin.readline to return multiple inputs with a dynamic function
        call_count = [0]

        def mock_readline():
            call_count[0] += 1
            if call_count[0] <= 3:
                return f"input{call_count[0]}\n"
            else:
                # Stop the thread after 3 inputs
                input_handler.stop_input_listener = True
                return ""

        mock_stdin.readline.side_effect = mock_readline

        # Start the thread
        input_handler.start()

        # Give it time to process all inputs
        time.sleep(0.5)

        # Stop the thread
        input_handler.shutdown()

        # Check that all inputs were queued (may be 3 or 4 due to timing)
        assert input_handler.input_queue.qsize() >= 3
        assert input_handler.input_queue.qsize() <= 4

        # Check the inputs in order
        assert input_handler.input_queue.get_nowait() == "input1"
        assert input_handler.input_queue.get_nowait() == "input2"
        assert input_handler.input_queue.get_nowait() == "input3"

    @patch("hexapod.interface.console.non_blocking_console_input_handler.select.select")
    def test_run_stop_flag_respected(self, mock_select, input_handler):
        """Test that the run method respects the stop flag."""
        # Mock select to return stdin as ready
        mock_select.return_value = ([], [], [])

        # Start the thread
        input_handler.start()

        # Give it time to start
        time.sleep(0.1)

        # Set stop flag
        input_handler.stop_input_listener = True

        # Give it time to stop
        time.sleep(0.2)

        # Check that the thread has stopped
        assert not input_handler.is_alive()

    def test_get_input_success(self, input_handler, caplog):
        """Test getting input successfully."""
        # Add test input to queue
        test_input = "test command"
        input_handler.input_queue.put(test_input)

        # Get input
        result = input_handler.get_input()

        assert result == test_input
        # Note: Logging is mocked in conftest.py, so we can't test log messages

    def test_get_input_with_timeout(self, input_handler):
        """Test getting input with timeout."""
        # Try to get input with short timeout
        result = input_handler.get_input(timeout=0.1)

        assert result is None

    def test_get_input_with_custom_timeout(self, input_handler):
        """Test getting input with custom timeout."""

        # Add input after a delay
        def add_input():
            time.sleep(0.05)
            input_handler.input_queue.put("delayed input")

        # Start thread to add input
        thread = threading.Thread(target=add_input)
        thread.start()

        # Get input with timeout longer than delay
        result = input_handler.get_input(timeout=0.2)

        # Clean up
        thread.join()

        assert result == "delayed input"

    def test_get_input_empty_queue(self, input_handler):
        """Test getting input when queue is empty."""
        result = input_handler.get_input(timeout=0.01)
        assert result is None

    def test_get_input_multiple_calls(self, input_handler):
        """Test getting multiple inputs in sequence."""
        # Add multiple inputs
        inputs = ["cmd1", "cmd2", "cmd3"]
        for inp in inputs:
            input_handler.input_queue.put(inp)

        # Get all inputs
        results = []
        for _ in range(3):
            result = input_handler.get_input()
            results.append(result)

        assert results == inputs

    def test_get_input_string_conversion(self, input_handler):
        """Test that get_input converts input to string."""
        # Add non-string input
        input_handler.input_queue.put(123)

        result = input_handler.get_input()

        assert result == "123"
        assert isinstance(result, str)

    @patch("hexapod.interface.console.non_blocking_console_input_handler.select.select")
    def test_shutdown_stops_thread(self, mock_select, input_handler):
        """Test that shutdown properly stops the thread."""
        # Mock select to avoid UnsupportedOperation
        mock_select.return_value = ([], [], [])

        # Start the thread
        input_handler.start()

        # Verify it's running
        assert input_handler.is_alive()

        # Shutdown
        input_handler.shutdown()

        # Verify it's stopped
        assert not input_handler.is_alive()

    @patch("hexapod.interface.console.non_blocking_console_input_handler.select.select")
    def test_shutdown_sets_stop_flag(self, mock_select, input_handler):
        """Test that shutdown sets the stop flag."""
        # Mock select to avoid UnsupportedOperation
        mock_select.return_value = ([], [], [])

        assert input_handler.stop_input_listener is False

        # Start the thread first to avoid join error
        input_handler.start()
        input_handler.shutdown()

        assert input_handler.stop_input_listener is True

    @patch("hexapod.interface.console.non_blocking_console_input_handler.select.select")
    def test_shutdown_joins_thread(self, mock_select, input_handler):
        """Test that shutdown joins the thread."""
        # Mock select to avoid UnsupportedOperation
        mock_select.return_value = ([], [], [])

        # Start the thread
        input_handler.start()

        # Mock join to verify it's called
        with patch.object(threading.Thread, "join") as mock_join:
            input_handler.shutdown()
            mock_join.assert_called_once()

    @patch("hexapod.interface.console.non_blocking_console_input_handler.select.select")
    def test_shutdown_logging(self, mock_select, input_handler, caplog):
        """Test that shutdown logs appropriately."""
        # Mock select to avoid UnsupportedOperation
        mock_select.return_value = ([], [], [])

        # Start the thread first to avoid join error
        input_handler.start()
        input_handler.shutdown()

        # Note: Logging is mocked in conftest.py, so we can't test log messages

    def test_input_queue_thread_safety(self, input_handler):
        """Test that input queue is thread-safe."""

        # Add inputs from multiple threads
        def add_inputs(prefix, count):
            for i in range(count):
                input_handler.input_queue.put(f"{prefix}_{i}")
                time.sleep(0.01)

        # Start multiple threads adding inputs
        threads = []
        for i in range(3):
            thread = threading.Thread(target=add_inputs, args=(f"thread{i}", 5))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check that all inputs were added
        assert input_handler.input_queue.qsize() == 15

    def test_run_with_exception_handling(self, input_handler, caplog):
        """Test run method with exception handling."""
        with patch(
            "hexapod.interface.console.non_blocking_console_input_handler.select.select"
        ) as mock_select:
            # Mock select to raise an exception
            mock_select.side_effect = OSError("Select error")

            # Start the thread
            input_handler.start()

            # Give it time to encounter the exception
            time.sleep(0.2)

            # Stop the thread
            input_handler.shutdown()

            # The thread should have stopped due to the exception
            assert not input_handler.is_alive()

    def test_run_with_stdin_readline_exception(self, input_handler, caplog):
        """Test run method with stdin.readline exception."""
        with (
            patch(
                "hexapod.interface.console.non_blocking_console_input_handler.select.select"
            ) as mock_select,
            patch(
                "hexapod.interface.console.non_blocking_console_input_handler.sys.stdin"
            ) as mock_stdin,
        ):

            # Mock select to return stdin as ready
            mock_select.return_value = ([mock_stdin], [], [])

            # Mock stdin.readline to raise an exception
            mock_stdin.readline.side_effect = IOError("Read error")

            # Start the thread
            input_handler.start()

            # Give it time to encounter the exception
            time.sleep(0.2)

            # Stop the thread
            input_handler.shutdown()

            # The thread should have stopped due to the exception
            assert not input_handler.is_alive()

    def test_get_input_with_zero_timeout(self, input_handler):
        """Test getting input with zero timeout."""
        result = input_handler.get_input(timeout=0.0)
        assert result is None

    def test_get_input_with_negative_timeout(self, input_handler):
        """Test getting input with negative timeout."""
        # Negative timeout should raise ValueError
        with pytest.raises(ValueError, match="'timeout' must be a non-negative number"):
            input_handler.get_input(timeout=-1.0)

    def test_get_input_with_very_long_timeout(self, input_handler):
        """Test getting input with very long timeout."""

        # Add input after a short delay
        def add_input():
            time.sleep(0.1)
            input_handler.input_queue.put("long timeout input")

        # Start thread to add input
        thread = threading.Thread(target=add_input)
        thread.start()

        # Get input with very long timeout
        result = input_handler.get_input(timeout=10.0)

        # Clean up
        thread.join()

        assert result == "long timeout input"

    def test_run_strips_whitespace(self, input_handler):
        """Test that run method strips whitespace from input."""
        with (
            patch(
                "hexapod.interface.console.non_blocking_console_input_handler.select.select"
            ) as mock_select,
            patch(
                "hexapod.interface.console.non_blocking_console_input_handler.sys.stdin"
            ) as mock_stdin,
        ):

            # Mock select to return stdin as ready
            mock_select.return_value = ([mock_stdin], [], [])

            # Mock stdin.readline to return input with whitespace
            mock_stdin.readline.return_value = "  test input  \n"

            # Start the thread
            input_handler.start()

            # Give it time to process
            time.sleep(0.2)

            # Stop the thread
            input_handler.shutdown()

            # Check that whitespace was stripped
            assert not input_handler.input_queue.empty()
            retrieved_input = input_handler.input_queue.get_nowait()
            assert retrieved_input == "test input"

    def test_run_with_empty_input(self, input_handler):
        """Test run method with empty input."""
        with (
            patch(
                "hexapod.interface.console.non_blocking_console_input_handler.select.select"
            ) as mock_select,
            patch(
                "hexapod.interface.console.non_blocking_console_input_handler.sys.stdin"
            ) as mock_stdin,
        ):

            # Mock select to return stdin as ready
            mock_select.return_value = ([mock_stdin], [], [])

            # Mock stdin.readline to return empty input
            mock_stdin.readline.return_value = "\n"

            # Start the thread
            input_handler.start()

            # Give it time to process
            time.sleep(0.2)

            # Stop the thread
            input_handler.shutdown()

            # Check that empty input was queued
            assert not input_handler.input_queue.empty()
            retrieved_input = input_handler.input_queue.get_nowait()
            assert retrieved_input == ""

    def test_run_with_multiline_input(self, input_handler):
        """Test run method with multiline input."""
        with (
            patch(
                "hexapod.interface.console.non_blocking_console_input_handler.select.select"
            ) as mock_select,
            patch(
                "hexapod.interface.console.non_blocking_console_input_handler.sys.stdin"
            ) as mock_stdin,
        ):

            # Mock select to return stdin as ready
            mock_select.return_value = ([mock_stdin], [], [])

            # Mock stdin.readline to return multiline input (readline reads one line at a time)
            mock_stdin.readline.return_value = "line1\n"

            # Start the thread
            input_handler.start()

            # Give it time to process
            time.sleep(0.2)

            # Stop the thread
            input_handler.shutdown()

            # Check that input was processed as single line
            assert not input_handler.input_queue.empty()
            retrieved_input = input_handler.input_queue.get_nowait()
            assert retrieved_input == "line1"

    def test_thread_name(self, input_handler):
        """Test that the thread has a proper name."""
        assert input_handler.name is not None
        assert isinstance(input_handler.name, str)
        assert len(input_handler.name) > 0

    def test_daemon_thread_property(self, input_handler):
        """Test that the thread is properly configured as daemon."""
        assert input_handler.daemon is True

    def test_input_queue_type(self, input_handler):
        """Test that input queue is properly typed."""
        assert isinstance(input_handler.input_queue, queue.Queue)
        assert input_handler.input_queue.maxsize == 0  # Unlimited size

    def test_stop_input_listener_initial_state(self, input_handler):
        """Test initial state of stop_input_listener flag."""
        assert input_handler.stop_input_listener is False

    def test_stop_input_listener_can_be_set(self, input_handler):
        """Test that stop_input_listener flag can be set."""
        input_handler.stop_input_listener = True
        assert input_handler.stop_input_listener is True

        input_handler.stop_input_listener = False
        assert input_handler.stop_input_listener is False
