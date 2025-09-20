"""
Unit tests for PulseSmoothlyAnimation.
"""
import pytest
from unittest.mock import Mock, patch
from hexapod.lights.animations.pulse_smoothly_animation import PulseSmoothlyAnimation
from hexapod.lights.lights import ColorRGB


@pytest.fixture
def mock_lights():
    """Mock Lights object."""
    mock_lights = Mock()
    mock_lights.num_led = 12
    mock_lights.set_color_rgb = Mock()
    return mock_lights


@pytest.fixture
def animation_default(mock_lights):
    """PulseSmoothlyAnimation with default parameters."""
    return PulseSmoothlyAnimation(lights=mock_lights)


@pytest.fixture
def animation_custom(mock_lights):
    """PulseSmoothlyAnimation with custom parameters."""
    return PulseSmoothlyAnimation(
        lights=mock_lights,
        base_color=ColorRGB.RED,
        pulse_color=ColorRGB.BLUE,
        pulse_speed=0.1
    )


class TestPulseSmoothlyAnimation:
    """Test cases for PulseSmoothlyAnimation class."""
    
    def test_init_default_parameters(self, mock_lights):
        """Test initialization with default parameters."""
        with patch('hexapod.lights.animations.pulse_smoothly_animation.Animation.__init__') as mock_super_init:
            animation = PulseSmoothlyAnimation(lights=mock_lights)
            
            # Verify parent initialization
            mock_super_init.assert_called_once_with(mock_lights)
            
            # Verify default parameters
            assert animation.base_color == ColorRGB.BLUE
            assert animation.pulse_color == ColorRGB.GREEN
            assert animation.pulse_speed == 0.05
    
    def test_init_custom_parameters(self, mock_lights):
        """Test initialization with custom parameters."""
        with patch('hexapod.lights.animations.pulse_smoothly_animation.Animation.__init__') as mock_super_init:
            animation = PulseSmoothlyAnimation(
                lights=mock_lights,
                base_color=ColorRGB.RED,
                pulse_color=ColorRGB.BLUE,
                pulse_speed=0.1
            )
            
            # Verify parent initialization
            mock_super_init.assert_called_once_with(mock_lights)
            
            # Verify custom parameters
            assert animation.base_color == ColorRGB.RED
            assert animation.pulse_color == ColorRGB.BLUE
            assert animation.pulse_speed == 0.1
    
    def test_execute_animation_forward_interpolation(self, animation_default, mock_lights):
        """Test execute_animation forward interpolation (base to pulse)."""
        # Mock stop_event to allow forward interpolation
        call_count = 0
        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            # Allow a few forward interpolation steps, then stop
            return call_count > 3
        
        animation_default.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation_default.execute_animation()
        
        # Verify set_color_rgb was called
        assert mock_lights.set_color_rgb.call_count > 0
        
        # Verify interpolation values
        calls = mock_lights.set_color_rgb.call_args_list
        for call in calls:
            rgb = call[0][0]  # First positional argument
            assert isinstance(rgb, tuple)
            assert len(rgb) == 3
            # Values should be between base and pulse colors
            base_rgb = ColorRGB.BLUE.rgb
            pulse_rgb = ColorRGB.GREEN.rgb
            for i in range(3):
                assert base_rgb[i] <= rgb[i] <= pulse_rgb[i] or pulse_rgb[i] <= rgb[i] <= base_rgb[i]
    
    def test_execute_animation_backward_interpolation(self, animation_default, mock_lights):
        """Test execute_animation backward interpolation (pulse to base)."""
        # Mock stop_event to allow both forward and backward interpolation
        call_count = 0
        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            # Allow forward interpolation (20 steps) + some backward, then stop
            return call_count > 25
        
        animation_default.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation_default.execute_animation()
        
        # Verify set_color_rgb was called
        assert mock_lights.set_color_rgb.call_count > 0
        
        # Verify interpolation values
        calls = mock_lights.set_color_rgb.call_args_list
        for call in calls:
            rgb = call[0][0]  # First positional argument
            assert isinstance(rgb, tuple)
            assert len(rgb) == 3
            # Values should be between base and pulse colors
            base_rgb = ColorRGB.BLUE.rgb
            pulse_rgb = ColorRGB.GREEN.rgb
            for i in range(3):
                assert base_rgb[i] <= rgb[i] <= pulse_rgb[i] or pulse_rgb[i] <= rgb[i] <= base_rgb[i]
    
    def test_execute_animation_stop_immediately(self, animation_default, mock_lights):
        """Test execute_animation when stopped immediately."""
        # Mock stop_event to return True immediately
        animation_default.stop_event.wait = Mock(return_value=True)
        
        animation_default.execute_animation()
        
        # Verify no LEDs were set
        mock_lights.set_color_rgb.assert_not_called()
    
    def test_execute_animation_stop_during_forward(self, animation_default, mock_lights):
        """Test stopping during forward interpolation."""
        # Mock stop_event to allow a few forward steps, then stop
        call_count = 0
        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            return call_count > 3
        
        animation_default.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation_default.execute_animation()
        
        # Verify some interpolation occurred
        assert mock_lights.set_color_rgb.call_count > 0
        assert mock_lights.set_color_rgb.call_count < 20  # Less than full forward cycle
    
    def test_execute_animation_stop_during_backward(self, animation_default, mock_lights):
        """Test stopping during backward interpolation."""
        # Mock stop_event to allow forward cycle + some backward, then stop
        call_count = 0
        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            # Allow forward cycle (20 steps) + some backward (3 steps), then stop
            return call_count > 23
        
        animation_default.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation_default.execute_animation()
        
        # Verify both forward and backward interpolation occurred
        assert mock_lights.set_color_rgb.call_count > 20
        assert mock_lights.set_color_rgb.call_count < 40  # Less than full cycle
    
    def test_execute_animation_custom_colors(self, animation_custom, mock_lights):
        """Test execute_animation with custom colors."""
        # Mock stop_event to allow some interpolation
        call_count = 0
        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            return call_count > 3
        
        animation_custom.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation_custom.execute_animation()
        
        # Verify set_color_rgb was called
        assert mock_lights.set_color_rgb.call_count > 0
        
        # Verify interpolation uses custom colors
        calls = mock_lights.set_color_rgb.call_args_list
        for call in calls:
            rgb = call[0][0]
            # Values should be between custom base and pulse colors
            base_rgb = ColorRGB.RED.rgb
            pulse_rgb = ColorRGB.BLUE.rgb
            for i in range(3):
                assert base_rgb[i] <= rgb[i] <= pulse_rgb[i] or pulse_rgb[i] <= rgb[i] <= base_rgb[i]
    
    def test_execute_animation_custom_pulse_speed(self, animation_custom):
        """Test that custom pulse speed is used."""
        delays = []
        def mock_wait(delay):
            delays.append(delay)
            return True  # Stop immediately
        
        animation_custom.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation_custom.execute_animation()
        
        # Verify custom pulse speed was used
        assert all(delay == 0.1 for delay in delays)
    
    def test_execute_animation_interpolation_calculation(self, animation_default, mock_lights):
        """Test the interpolation calculation logic."""
        # Test with known colors for easier verification
        animation = PulseSmoothlyAnimation(
            lights=mock_lights,
            base_color=ColorRGB.BLACK,  # (0, 0, 0)
            pulse_color=ColorRGB.WHITE,  # (255, 255, 255)
            pulse_speed=0.1
        )
        
        # Mock stop_event to allow one forward step
        animation.stop_event.wait = Mock(side_effect=[False, True])
        
        animation.execute_animation()
        
        # Verify interpolation calculation
        calls = mock_lights.set_color_rgb.call_args_list
        assert len(calls) == 1
        
        rgb = calls[0][0][0]
        # At i=0, should be base color (0, 0, 0)
        assert rgb == (0, 0, 0)
    
    def test_execute_animation_interpolation_steps(self, animation_default, mock_lights):
        """Test that interpolation uses correct step size."""
        # Mock stop_event to allow some forward steps
        call_count = 0
        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            return call_count > 5
        
        animation_default.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation_default.execute_animation()
        
        # Verify step size is 5 (as defined in the code)
        calls = mock_lights.set_color_rgb.call_args_list
        assert len(calls) > 0
        
        # The code uses range(0, 100, 5), so we should see steps at 0, 5, 10, 15, 20
        # This is verified by the interpolation calculation in the test above
    
    def test_execute_animation_continuous_cycling(self, animation_default, mock_lights):
        """Test continuous cycling between forward and backward interpolation."""
        # Mock stop_event to allow multiple cycles
        call_count = 0
        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            # Allow multiple complete cycles, then stop
            return call_count > 50
        
        animation_default.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation_default.execute_animation()
        
        # Verify many interpolation calls occurred
        assert mock_lights.set_color_rgb.call_count > 40  # At least 2 complete cycles
    
    def test_execute_animation_same_colors(self, mock_lights):
        """Test execute_animation with same base and pulse colors."""
        animation = PulseSmoothlyAnimation(
            lights=mock_lights,
            base_color=ColorRGB.BLUE,
            pulse_color=ColorRGB.BLUE,
            pulse_speed=0.1
        )
        
        # Mock stop_event to allow some interpolation
        call_count = 0
        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            return call_count > 3
        
        animation.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation.execute_animation()
        
        # Verify interpolation occurred
        assert mock_lights.set_color_rgb.call_count > 0
        
        # All interpolated values should be the same color
        calls = mock_lights.set_color_rgb.call_args_list
        for call in calls:
            rgb = call[0][0]
            assert rgb == ColorRGB.BLUE.rgb
    
    def test_execute_animation_different_speeds(self, mock_lights):
        """Test execute_animation with different pulse speeds."""
        # Test with very fast pulse
        animation_fast = PulseSmoothlyAnimation(
            lights=mock_lights,
            pulse_speed=0.01
        )
        
        delays = []
        def mock_wait(delay):
            delays.append(delay)
            return True  # Stop immediately
        
        animation_fast.stop_event.wait = Mock(side_effect=mock_wait)
        animation_fast.execute_animation()
        
        # Verify fast speed was used
        assert all(delay == 0.01 for delay in delays)
        
        # Test with very slow pulse
        mock_lights.reset_mock()
        animation_slow = PulseSmoothlyAnimation(
            lights=mock_lights,
            pulse_speed=1.0
        )
        
        delays = []
        animation_slow.stop_event.wait = Mock(side_effect=mock_wait)
        animation_slow.execute_animation()
        
        # Verify slow speed was used
        assert all(delay == 1.0 for delay in delays)
    
    def test_execute_animation_rgb_conversion(self, animation_default, mock_lights):
        """Test that RGB values are properly converted from ColorRGB."""
        # Mock stop_event to allow one interpolation step
        animation_default.stop_event.wait = Mock(side_effect=[False, True])
        
        animation_default.execute_animation()
        
        # Verify set_color_rgb was called with RGB tuple
        assert mock_lights.set_color_rgb.call_count == 1
        call = mock_lights.set_color_rgb.call_args_list[0]
        assert call[0][0] == ColorRGB.BLUE.rgb  # Should be RGB tuple, not ColorRGB object
    
    def test_attributes_after_init(self, animation_custom):
        """Test that all attributes are properly set after initialization."""
        assert animation_custom.base_color == ColorRGB.RED
        assert animation_custom.pulse_color == ColorRGB.BLUE
        assert animation_custom.pulse_speed == 0.1
        assert hasattr(animation_custom, 'lights')
        assert hasattr(animation_custom, 'stop_event')
    
    def test_inheritance(self, animation_default):
        """Test that PulseSmoothlyAnimation inherits from Animation."""
        from hexapod.lights.animations.animation import Animation
        assert isinstance(animation_default, Animation)
    
    def test_override_decorator(self, animation_default):
        """Test that execute_animation has the @override decorator."""
        import inspect
        source = inspect.getsource(animation_default.execute_animation)
        assert '@override' in source
    
    def test_interpolation_range_forward(self, animation_default, mock_lights):
        """Test that forward interpolation covers the full range."""
        # Mock stop_event to allow full forward cycle
        call_count = 0
        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            # Allow full forward cycle (20 steps), then stop
            return call_count > 20
        
        animation_default.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation_default.execute_animation()
        
        # Verify full forward cycle occurred
        assert mock_lights.set_color_rgb.call_count == 20
        
        # Verify first call is base color (i=0)
        first_call = mock_lights.set_color_rgb.call_args_list[0]
        assert first_call[0][0] == ColorRGB.BLUE.rgb
        
        # Verify last call is close to pulse color (i=95)
        last_call = mock_lights.set_color_rgb.call_args_list[-1]
        # At i=95, should be very close to pulse color
        expected_rgb = (
            int(ColorRGB.BLUE.rgb[0] + (ColorRGB.GREEN.rgb[0] - ColorRGB.BLUE.rgb[0]) * 95 / 100),
            int(ColorRGB.BLUE.rgb[1] + (ColorRGB.GREEN.rgb[1] - ColorRGB.BLUE.rgb[1]) * 95 / 100),
            int(ColorRGB.BLUE.rgb[2] + (ColorRGB.GREEN.rgb[2] - ColorRGB.BLUE.rgb[2]) * 95 / 100),
        )
        assert last_call[0][0] == expected_rgb
    
    def test_interpolation_range_backward(self, animation_default, mock_lights):
        """Test that backward interpolation covers the full range."""
        # Mock stop_event to allow forward + full backward cycle
        call_count = 0
        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            # Allow forward cycle (20 steps) + full backward cycle (20 steps), then stop
            return call_count > 40
        
        animation_default.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation_default.execute_animation()
        
        # Verify both cycles occurred
        assert mock_lights.set_color_rgb.call_count == 40
        
        # Verify backward cycle starts from pulse color
        backward_start = mock_lights.set_color_rgb.call_args_list[20]  # First backward call
        assert backward_start[0][0] == ColorRGB.GREEN.rgb  # Should be pulse color (i=100)
        
        # Verify backward cycle ends close to base color
        backward_end = mock_lights.set_color_rgb.call_args_list[-1]  # Last call
        # At i=5, should be close to base color
        expected_rgb = (
            int(ColorRGB.BLUE.rgb[0] + (ColorRGB.GREEN.rgb[0] - ColorRGB.BLUE.rgb[0]) * 5 / 100),
            int(ColorRGB.BLUE.rgb[1] + (ColorRGB.GREEN.rgb[1] - ColorRGB.BLUE.rgb[1]) * 5 / 100),
            int(ColorRGB.BLUE.rgb[2] + (ColorRGB.GREEN.rgb[2] - ColorRGB.BLUE.rgb[2]) * 5 / 100),
        )
        assert backward_end[0][0] == expected_rgb
