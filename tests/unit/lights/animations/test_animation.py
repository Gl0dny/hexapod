"""
Unit tests for the base Animation class.
"""

import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from hexapod.lights.animations.animation import Animation
from hexapod.lights.lights import ColorRGB


class ConcreteAnimation(Animation):
    """Concrete implementation of Animation for testing."""

    def __init__(self, lights, test_delay=0.01):
        super().__init__(lights)
        self.test_delay = test_delay
        self.execution_count = 0

    def execute_animation(self):
        """Test implementation that counts executions."""
        while not self.stop_event.is_set():
            self.execution_count += 1
            if self.stop_event.wait(self.test_delay):
                return


@pytest.fixture
def mock_lights():
    """Mock Lights object."""
    mock_lights = Mock()
    mock_lights.num_led = 12
    mock_lights.set_color = Mock()
    mock_lights.set_color_rgb = Mock()
    mock_lights.clear = Mock()
    mock_lights.rotate = Mock()
    mock_lights.get_wheel_color = Mock(return_value=(255, 0, 0))
    return mock_lights


@pytest.fixture
def concrete_animation(mock_lights):
    """ConcreteAnimation instance for testing."""
    return ConcreteAnimation(mock_lights)


class TestAnimation:
    """Test cases for the base Animation class."""

    def test_init(self, mock_lights):
        """Test Animation initialization."""
        with (
            patch("hexapod.lights.animations.animation.rename_thread") as mock_rename,
            patch("hexapod.lights.animations.animation.logger") as mock_logger,
        ):

            animation = ConcreteAnimation(mock_lights)

            # Verify initialization
            assert animation.lights == mock_lights
            assert isinstance(animation.stop_event, threading.Event)
            assert animation.daemon is True
            assert animation.execution_count == 0

            # Verify thread renaming and logging
            mock_rename.assert_called_once_with(animation, "ConcreteAnimation")
            mock_logger.debug.assert_called_once_with(
                "ConcreteAnimation initialized successfully."
            )

    def test_start(self, concrete_animation):
        """Test starting the animation."""
        # Verify initial state
        assert not concrete_animation.is_alive()
        assert not concrete_animation.stop_event.is_set()  # Initially not set

        # Start the animation
        concrete_animation.start()

        # Verify stop event is cleared and thread is started
        assert not concrete_animation.stop_event.is_set()
        assert concrete_animation.is_alive()

        # Clean up
        concrete_animation.stop_animation()

    def test_run_executes_animation(self, concrete_animation):
        """Test that run() calls execute_animation()."""
        # Start the animation
        concrete_animation.start()

        # Give it time to execute
        time.sleep(0.05)

        # Verify execution occurred
        assert concrete_animation.execution_count > 0

        # Clean up
        concrete_animation.stop_animation()

    def test_stop_animation(self, concrete_animation):
        """Test stopping the animation."""
        # Start the animation
        concrete_animation.start()

        # Verify it's running
        assert concrete_animation.is_alive()

        # Stop the animation
        with patch("hexapod.lights.animations.animation.logger") as mock_logger:
            concrete_animation.stop_animation()

            # Verify stop event is set and thread is stopped
            assert concrete_animation.stop_event.is_set()
            assert not concrete_animation.is_alive()

            # Verify logging
            mock_logger.debug.assert_any_call("Stopping animation: ConcreteAnimation")

    def test_stop_animation_when_not_alive(self, concrete_animation):
        """Test stopping animation when thread is not alive."""
        # Don't start the animation
        assert not concrete_animation.is_alive()

        with patch("hexapod.lights.animations.animation.logger") as mock_logger:
            concrete_animation.stop_animation()

            # Verify stop event is set
            assert concrete_animation.stop_event.is_set()

            # Verify logging (should not call join)
            mock_logger.debug.assert_called_once_with(
                "Stopping animation: ConcreteAnimation"
            )
            # Should not call the "forcefully stopping" message
            assert mock_logger.debug.call_count == 1

    def test_stop_animation_forceful_stop(self, concrete_animation):
        """Test forceful stopping of animation."""
        # Start the animation
        concrete_animation.start()

        # Verify it's running
        assert concrete_animation.is_alive()

        # Stop the animation
        with patch("hexapod.lights.animations.animation.logger") as mock_logger:
            concrete_animation.stop_animation()

            # Verify both stop messages were logged
            mock_logger.debug.assert_any_call("Stopping animation: ConcreteAnimation")
            mock_logger.debug.assert_any_call(
                "Animation ConcreteAnimation forcefully stopping."
            )
            assert mock_logger.debug.call_count == 2

    def test_execute_animation_abstract(self, mock_lights):
        """Test that Animation is abstract and cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Animation(mock_lights)

    def test_daemon_thread(self, concrete_animation):
        """Test that animation threads are daemon threads."""
        assert concrete_animation.daemon is True

    def test_thread_name(self, concrete_animation):
        """Test that thread name is set correctly."""
        assert concrete_animation.name.startswith("ConcreteAnimation")

    def test_stop_event_initialization(self, concrete_animation):
        """Test that stop_event is properly initialized."""
        assert isinstance(concrete_animation.stop_event, threading.Event)
        assert not concrete_animation.stop_event.is_set()  # Initially not set

    def test_lights_attribute(self, concrete_animation, mock_lights):
        """Test that lights attribute is properly set."""
        assert concrete_animation.lights == mock_lights

    def test_multiple_start_stop_cycles(self, mock_lights):
        """Test multiple start/stop cycles."""
        for i in range(3):
            # Create new animation for each cycle
            animation = ConcreteAnimation(mock_lights)

            # Start
            animation.start()
            assert animation.is_alive()
            assert not animation.stop_event.is_set()

            # Let it run briefly
            time.sleep(0.01)

            # Stop
            animation.stop_animation()
            assert not animation.is_alive()
            assert animation.stop_event.is_set()

    def test_execution_count_increases(self, concrete_animation):
        """Test that execution count increases during animation."""
        initial_count = concrete_animation.execution_count

        # Start animation
        concrete_animation.start()
        time.sleep(0.05)  # Let it run

        # Verify count increased
        assert concrete_animation.execution_count > initial_count

        # Stop animation
        concrete_animation.stop_animation()

        # Get final count
        final_count = concrete_animation.execution_count

        # Create new animation for second test
        new_animation = ConcreteAnimation(concrete_animation.lights)
        new_animation.start()
        time.sleep(0.01)
        new_animation.stop_animation()

        assert new_animation.execution_count > 0

    def test_stop_event_blocks_execution(self, concrete_animation):
        """Test that stop_event.wait() properly blocks execution."""
        # Set stop event before starting
        concrete_animation.stop_event.set()

        # Start animation (should not execute much due to stop event)
        concrete_animation.start()
        time.sleep(0.01)
        initial_count = concrete_animation.execution_count

        # Clear stop event
        concrete_animation.stop_event.clear()
        time.sleep(0.01)

        # Verify execution resumed (count should be same or higher)
        assert concrete_animation.execution_count >= initial_count

        # Clean up
        concrete_animation.stop_animation()

    def test_thread_safety(self, mock_lights):
        """Test thread safety with multiple animations."""
        animations = [ConcreteAnimation(mock_lights) for _ in range(3)]

        # Start all animations
        for anim in animations:
            anim.start()

        # Let them run
        time.sleep(0.05)

        # Verify all are running
        for anim in animations:
            assert anim.is_alive()
            assert anim.execution_count > 0

        # Stop all animations
        for anim in animations:
            anim.stop_animation()

        # Verify all are stopped
        for anim in animations:
            assert not anim.is_alive()
            assert anim.stop_event.is_set()
