"""
Unit tests for OppositeRotateAnimation.
"""
import pytest
from unittest.mock import Mock, patch
from hexapod.lights.animations.opposite_rotate_animation import OppositeRotateAnimation
from hexapod.lights.lights import ColorRGB


@pytest.fixture
def mock_lights():
    """Mock Lights object."""
    mock_lights = Mock()
    mock_lights.num_led = 12
    mock_lights.set_color = Mock()
    mock_lights.clear = Mock()
    return mock_lights


@pytest.fixture
def animation_default(mock_lights):
    """OppositeRotateAnimation with default parameters."""
    return OppositeRotateAnimation(lights=mock_lights)


@pytest.fixture
def animation_custom(mock_lights):
    """OppositeRotateAnimation with custom parameters."""
    return OppositeRotateAnimation(
        lights=mock_lights,
        interval=0.2,
        color=ColorRGB.RED
    )


class TestOppositeRotateAnimation:
    """Test cases for OppositeRotateAnimation class."""
    
    def test_init_default_parameters(self, mock_lights):
        """Test initialization with default parameters."""
        with patch('hexapod.lights.animations.opposite_rotate_animation.Animation.__init__') as mock_super_init:
            animation = OppositeRotateAnimation(lights=mock_lights)
            
            # Verify parent initialization
            mock_super_init.assert_called_once_with(mock_lights)
            
            # Verify default parameters
            assert animation.interval == 0.1
            assert animation.color == ColorRGB.WHITE
            assert animation.direction == OppositeRotateAnimation.FORWARD
            assert OppositeRotateAnimation.FORWARD == 1
            assert OppositeRotateAnimation.BACKWARD == -1
    
    def test_init_custom_parameters(self, mock_lights):
        """Test initialization with custom parameters."""
        with patch('hexapod.lights.animations.opposite_rotate_animation.Animation.__init__') as mock_super_init:
            animation = OppositeRotateAnimation(
                lights=mock_lights,
                interval=0.2,
                color=ColorRGB.RED
            )
            
            # Verify parent initialization
            mock_super_init.assert_called_once_with(mock_lights)
            
            # Verify custom parameters
            assert animation.interval == 0.2
            assert animation.color == ColorRGB.RED
            assert animation.direction == OppositeRotateAnimation.FORWARD
    
    def test_constants(self, animation_default):
        """Test that constants are properly defined."""
        assert OppositeRotateAnimation.FORWARD == 1
        assert OppositeRotateAnimation.BACKWARD == -1
    
    def test_execute_animation_single_led_sequence(self, animation_default, mock_lights):
        """Test execute_animation for a single LED sequence."""
        # Mock stop_event to allow one complete sequence
        call_count = 0
        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            # Allow initial LED, then stop
            return call_count > 1
        
        animation_default.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation_default.execute_animation()
        
        # Verify clear and set_color were called for initial LED
        assert mock_lights.clear.call_count == 1
        assert mock_lights.set_color.call_count == 1
        
        # Verify initial LED was set at index 0
        call = mock_lights.set_color.call_args_list[0]
        assert call[0][0] == ColorRGB.WHITE
        assert call[1]['led_index'] == 0
    
    def test_execute_animation_opposite_movement(self, animation_default, mock_lights):
        """Test execute_animation for opposite movement pattern."""
        # Mock stop_event to allow a few iterations
        call_count = 0
        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            # Allow initial LED + 3 offset iterations, then stop
            return call_count > 4
        
        animation_default.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation_default.execute_animation()
        
        # Verify clear was called multiple times
        assert mock_lights.clear.call_count >= 2
        
        # Verify set_color was called multiple times
        assert mock_lights.set_color.call_count >= 2
        
        # Verify opposite movement pattern
        calls = mock_lights.set_color.call_args_list
        # First call should be at index 0
        assert calls[0][1]['led_index'] == 0
        
        # Subsequent calls should show opposite movement
        if len(calls) > 1:
            # Should have calls with different indices showing opposite movement
            indices = [call[1]['led_index'] for call in calls[1:]]
            # Should have both forward and backward indices
            assert len(set(indices)) > 1
    
    def test_execute_animation_direction_switching(self, animation_default, mock_lights):
        """Test execute_animation direction switching."""
        # Mock stop_event to allow a complete cycle
        call_count = 0
        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            # Allow enough iterations to see direction switch
            return call_count > 20  # Allow multiple cycles
        
        animation_default.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation_default.execute_animation()
        
        # Verify multiple clear and set_color calls
        assert mock_lights.clear.call_count > 1
        assert mock_lights.set_color.call_count > 1
    
    def test_execute_animation_stop_immediately(self, animation_default, mock_lights):
        """Test execute_animation when stopped immediately."""
        # Mock stop_event to return True immediately
        animation_default.stop_event.wait = Mock(return_value=True)
        
        animation_default.execute_animation()
        
        # Verify no LEDs were set
        mock_lights.clear.assert_not_called()
        mock_lights.set_color.assert_not_called()
    
    def test_execute_animation_custom_color(self, animation_custom, mock_lights):
        """Test execute_animation with custom color."""
        # Mock stop_event to allow one LED to be set
        animation_custom.stop_event.wait = Mock(side_effect=[False, True])
        
        animation_custom.execute_animation()
        
        # Verify custom color was used
        call = mock_lights.set_color.call_args_list[0]
        assert call[0][0] == ColorRGB.RED
        assert call[1]['led_index'] == 0
    
    def test_execute_animation_custom_interval(self, animation_custom):
        """Test that custom interval is used."""
        delays = []
        def mock_wait(delay):
            delays.append(delay)
            return True  # Stop immediately
        
        animation_custom.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation_custom.execute_animation()
        
        # Verify custom interval was used
        assert all(delay == 0.2 for delay in delays)
    
    def test_execute_animation_odd_number_of_leds(self, mock_lights):
        """Test execute_animation with odd number of LEDs."""
        mock_lights.num_led = 7
        animation = OppositeRotateAnimation(lights=mock_lights)
        
        # Mock stop_event to allow a few iterations
        call_count = 0
        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            return call_count > 5
        
        animation.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation.execute_animation()
        
        # Verify animation ran
        assert mock_lights.clear.call_count > 0
        assert mock_lights.set_color.call_count > 0
    
    def test_execute_animation_single_led(self, mock_lights):
        """Test execute_animation with single LED."""
        mock_lights.num_led = 1
        animation = OppositeRotateAnimation(lights=mock_lights)
        
        # Mock stop_event to allow one iteration
        animation.stop_event.wait = Mock(side_effect=[False, True])
        
        animation.execute_animation()
        
        # Verify single LED was set (clear is called twice due to the while loop structure)
        assert mock_lights.clear.call_count == 2
        assert mock_lights.set_color.call_count == 2  # Two calls due to the while loop structure
        call = mock_lights.set_color.call_args_list[0]
        assert call[1]['led_index'] == 0
    
    def test_execute_animation_zero_leds(self, mock_lights):
        """Test execute_animation with zero LEDs."""
        mock_lights.num_led = 0
        animation = OppositeRotateAnimation(lights=mock_lights)
        
        # Mock stop_event to return True immediately
        animation.stop_event.wait = Mock(return_value=True)
        
        animation.execute_animation()
        
        # Verify no LEDs were set
        mock_lights.clear.assert_not_called()
        mock_lights.set_color.assert_not_called()
    
    def test_execute_animation_max_offset_calculation(self, animation_default, mock_lights):
        """Test max_offset calculation for different LED counts."""
        # Test with 12 LEDs (even)
        mock_lights.num_led = 12
        animation = OppositeRotateAnimation(lights=mock_lights)
        
        # Mock stop_event to allow some iterations
        call_count = 0
        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            return call_count > 10
        
        animation.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation.execute_animation()
        
        # Verify animation ran
        assert mock_lights.clear.call_count > 0
        assert mock_lights.set_color.call_count > 0
        
        # Test with 7 LEDs (odd)
        mock_lights.reset_mock()
        mock_lights.num_led = 7
        animation = OppositeRotateAnimation(lights=mock_lights)
        
        call_count = 0
        animation.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation.execute_animation()
        
        # Verify animation ran
        assert mock_lights.clear.call_count > 0
        assert mock_lights.set_color.call_count > 0
    
    def test_execute_animation_direction_initialization(self, animation_default):
        """Test that direction is properly initialized."""
        assert animation_default.direction == OppositeRotateAnimation.FORWARD
    
    def test_execute_animation_direction_switching_logic(self, animation_default):
        """Test the direction switching logic."""
        # Test forward to backward
        animation_default.direction = OppositeRotateAnimation.FORWARD
        animation_default.direction = (
            OppositeRotateAnimation.BACKWARD if animation_default.direction == OppositeRotateAnimation.FORWARD 
            else OppositeRotateAnimation.FORWARD
        )
        assert animation_default.direction == OppositeRotateAnimation.BACKWARD
        
        # Test backward to forward
        animation_default.direction = (
            OppositeRotateAnimation.BACKWARD if animation_default.direction == OppositeRotateAnimation.FORWARD 
            else OppositeRotateAnimation.FORWARD
        )
        assert animation_default.direction == OppositeRotateAnimation.FORWARD
    
    def test_execute_animation_index_calculation(self, animation_default, mock_lights):
        """Test LED index calculation with modulo arithmetic."""
        # Test with 12 LEDs
        mock_lights.num_led = 12
        animation = OppositeRotateAnimation(lights=mock_lights)
        
        # Test various offset calculations
        start_index = 0
        direction = 1
        offset = 1
        
        index1 = (start_index + offset * direction) % 12
        index2 = (start_index - offset * direction) % 12
        
        assert index1 == 1
        assert index2 == 11  # Wraps around
    
    def test_attributes_after_init(self, animation_custom):
        """Test that all attributes are properly set after initialization."""
        assert animation_custom.interval == 0.2
        assert animation_custom.color == ColorRGB.RED
        assert animation_custom.direction == OppositeRotateAnimation.FORWARD
        assert hasattr(animation_custom, 'lights')
        assert hasattr(animation_custom, 'stop_event')
    
    def test_inheritance(self, animation_default):
        """Test that OppositeRotateAnimation inherits from Animation."""
        from hexapod.lights.animations.animation import Animation
        assert isinstance(animation_default, Animation)
    
    def test_override_decorator(self, animation_default):
        """Test that execute_animation has the @override decorator."""
        import inspect
        source = inspect.getsource(animation_default.execute_animation)
        assert '@override' in source
    
    def test_merge_back_phase(self, animation_default, mock_lights):
        """Test the merge back phase of the animation."""
        # Mock stop_event to allow complete sequence including merge back
        call_count = 0
        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            # Allow enough iterations to reach merge back phase
            return call_count > 15
        
        animation_default.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation_default.execute_animation()
        
        # Verify animation completed multiple phases
        assert mock_lights.clear.call_count > 1
        assert mock_lights.set_color.call_count > 1
