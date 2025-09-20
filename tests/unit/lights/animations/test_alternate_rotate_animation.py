"""
Unit tests for AlternateRotateAnimation.
"""
import pytest
import time
from unittest.mock import Mock, patch
from hexapod.lights.animations.alternate_rotate_animation import AlternateRotateAnimation
from hexapod.lights.lights import ColorRGB


@pytest.fixture
def mock_lights():
    """Mock Lights object."""
    mock_lights = Mock()
    mock_lights.num_led = 12
    mock_lights.set_color = Mock()
    mock_lights.rotate = Mock()
    return mock_lights


@pytest.fixture
def animation_default(mock_lights):
    """AlternateRotateAnimation with default parameters."""
    return AlternateRotateAnimation(lights=mock_lights)


@pytest.fixture
def animation_custom(mock_lights):
    """AlternateRotateAnimation with custom parameters."""
    return AlternateRotateAnimation(
        lights=mock_lights,
        color_even=ColorRGB.RED,
        color_odd=ColorRGB.BLUE,
        delay=0.1,
        positions=6
    )


class TestAlternateRotateAnimation:
    """Test cases for AlternateRotateAnimation class."""
    
    def test_init_default_parameters(self, mock_lights):
        """Test initialization with default parameters."""
        with patch('hexapod.lights.animations.alternate_rotate_animation.Animation.__init__') as mock_super_init:
            animation = AlternateRotateAnimation(lights=mock_lights)
            
            # Verify parent initialization
            mock_super_init.assert_called_once_with(mock_lights)
            
            # Verify default parameters
            assert animation.color_even == ColorRGB.INDIGO
            assert animation.color_odd == ColorRGB.GOLDEN
            assert animation.delay == 0.25
            assert animation.positions == 12
    
    def test_init_custom_parameters(self, mock_lights):
        """Test initialization with custom parameters."""
        with patch('hexapod.lights.animations.alternate_rotate_animation.Animation.__init__') as mock_super_init:
            animation = AlternateRotateAnimation(
                lights=mock_lights,
                color_even=ColorRGB.RED,
                color_odd=ColorRGB.BLUE,
                delay=0.1,
                positions=6
            )
            
            # Verify parent initialization
            mock_super_init.assert_called_once_with(mock_lights)
            
            # Verify custom parameters
            assert animation.color_even == ColorRGB.RED
            assert animation.color_odd == ColorRGB.BLUE
            assert animation.delay == 0.1
            assert animation.positions == 6
    
    def test_execute_animation_initial_setup(self, animation_default, mock_lights):
        """Test the initial LED setup phase of execute_animation."""
        # Mock stop_event to allow all 12 LEDs to be set, then stop
        animation_default.stop_event.wait = Mock(side_effect=[False] * 12 + [True])
        
        animation_default.execute_animation()
        
        # Verify all LEDs were set with alternating colors
        assert mock_lights.set_color.call_count == 12
        
        # Verify alternating pattern
        calls = mock_lights.set_color.call_args_list
        for i, call in enumerate(calls):
            expected_color = ColorRGB.INDIGO if i % 2 == 0 else ColorRGB.GOLDEN
            assert call[0][0] == expected_color
            assert call[1]['led_index'] == i
    
    def test_execute_animation_rotation_phase(self, animation_default, mock_lights):
        """Test the rotation phase of execute_animation."""
        # Mock stop_event to allow initial setup, then rotation, then stop
        call_count = 0
        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            if call_count <= 12:  # Initial setup
                return False
            elif call_count <= 12 + 6:  # First rotation cycle
                return False
            else:  # Stop
                return True
        
        animation_default.stop_event.wait = Mock(side_effect=mock_wait)
        animation_default.positions = 6  # Set smaller number for testing
        
        animation_default.execute_animation()
        
        # Verify rotation was called
        assert mock_lights.rotate.call_count == 6
        # Verify all calls were with position 1
        for call in mock_lights.rotate.call_args_list:
            assert call[0][0] == 1
    
    def test_execute_animation_stop_during_initial_setup(self, animation_default, mock_lights):
        """Test stopping during initial LED setup."""
        # Mock stop_event to return True immediately
        animation_default.stop_event.wait = Mock(return_value=True)
        
        animation_default.execute_animation()
        
        # Verify no LEDs were set
        mock_lights.set_color.assert_not_called()
        mock_lights.rotate.assert_not_called()
    
    def test_execute_animation_stop_during_rotation(self, animation_default, mock_lights):
        """Test stopping during rotation phase."""
        # Mock stop_event to allow initial setup, then stop during rotation
        call_count = 0
        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            if call_count <= 12:  # Initial setup
                return False
            elif call_count == 13:  # First rotation call
                return False
            else:  # Stop
                return True
        
        animation_default.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation_default.execute_animation()
        
        # Verify initial setup was completed
        assert mock_lights.set_color.call_count == 12
        # Verify only one rotation occurred
        assert mock_lights.rotate.call_count == 1
    
    def test_execute_animation_custom_colors(self, animation_custom, mock_lights):
        """Test execute_animation with custom colors."""
        # Mock stop_event to return True after first iteration
        animation_custom.stop_event.wait = Mock(side_effect=[False, True])
        
        animation_custom.execute_animation()
        
        # Verify custom colors were used
        calls = mock_lights.set_color.call_args_list
        for i, call in enumerate(calls):
            expected_color = ColorRGB.RED if i % 2 == 0 else ColorRGB.BLUE
            assert call[0][0] == expected_color
            assert call[1]['led_index'] == i
    
    def test_execute_animation_custom_delay(self, animation_custom):
        """Test that custom delay is used."""
        # Mock stop_event to track delay values
        delays = []
        def mock_wait(delay):
            delays.append(delay)
            return True  # Stop immediately
        
        animation_custom.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation_custom.execute_animation()
        
        # Verify custom delay was used
        assert all(delay == 0.1 for delay in delays)
    
    def test_execute_animation_custom_positions(self, animation_custom, mock_lights):
        """Test execute_animation with custom positions."""
        # Mock stop_event to allow initial setup and some rotations
        call_count = 0
        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            if call_count <= 12:  # Initial setup
                return False
            elif call_count <= 12 + 3:  # Partial rotation cycle
                return False
            else:  # Stop
                return True
        
        animation_custom.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation_custom.execute_animation()
        
        # Verify custom positions were used (3 rotations out of 6)
        assert mock_lights.rotate.call_count == 3
    
    def test_execute_animation_continuous_rotation(self, animation_default, mock_lights):
        """Test continuous rotation without stopping."""
        # Mock stop_event to allow multiple rotation cycles
        call_count = 0
        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            if call_count <= 12:  # Initial setup
                return False
            elif call_count <= 12 + 24:  # Two full rotation cycles (12 positions each)
                return False
            else:  # Stop
                return True
        
        animation_default.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation_default.execute_animation()
        
        # Verify two full rotation cycles occurred
        assert mock_lights.rotate.call_count == 24
    
    def test_execute_animation_odd_number_of_leds(self, mock_lights):
        """Test animation with odd number of LEDs."""
        mock_lights.num_led = 7
        animation = AlternateRotateAnimation(lights=mock_lights)
        
        # Mock stop_event to return True after initial setup
        animation.stop_event.wait = Mock(side_effect=[False, False, False, False, False, False, False, True])
        
        animation.execute_animation()
        
        # Verify all 7 LEDs were set
        assert mock_lights.set_color.call_count == 7
        
        # Verify alternating pattern
        calls = mock_lights.set_color.call_args_list
        for i, call in enumerate(calls):
            expected_color = ColorRGB.INDIGO if i % 2 == 0 else ColorRGB.GOLDEN
            assert call[0][0] == expected_color
            assert call[1]['led_index'] == i
    
    def test_execute_animation_single_led(self, mock_lights):
        """Test animation with single LED."""
        mock_lights.num_led = 1
        animation = AlternateRotateAnimation(lights=mock_lights)
        
        # Mock stop_event to return True after initial setup
        animation.stop_event.wait = Mock(side_effect=[False, True])
        
        animation.execute_animation()
        
        # Verify single LED was set
        assert mock_lights.set_color.call_count == 1
        call = mock_lights.set_color.call_args_list[0]
        assert call[0][0] == ColorRGB.INDIGO  # Even index (0)
        assert call[1]['led_index'] == 0
    
    def test_execute_animation_zero_leds(self, mock_lights):
        """Test animation with zero LEDs."""
        mock_lights.num_led = 0
        animation = AlternateRotateAnimation(lights=mock_lights)
        
        # Mock stop_event to return True immediately
        animation.stop_event.wait = Mock(return_value=True)
        
        animation.execute_animation()
        
        # Verify no LEDs were set
        mock_lights.set_color.assert_not_called()
        mock_lights.rotate.assert_not_called()
    
    def test_attributes_after_init(self, animation_custom):
        """Test that all attributes are properly set after initialization."""
        assert animation_custom.color_even == ColorRGB.RED
        assert animation_custom.color_odd == ColorRGB.BLUE
        assert animation_custom.delay == 0.1
        assert animation_custom.positions == 6
        assert hasattr(animation_custom, 'lights')
        assert hasattr(animation_custom, 'stop_event')
    
    def test_inheritance(self, animation_default):
        """Test that AlternateRotateAnimation inherits from Animation."""
        from hexapod.lights.animations.animation import Animation
        assert isinstance(animation_default, Animation)
    
    def test_override_decorator(self, animation_default):
        """Test that execute_animation has the @override decorator."""
        # This is more of a static analysis test
        import inspect
        source = inspect.getsource(animation_default.execute_animation)
        assert '@override' in source
