"""
Unit tests for DirectionOfArrivalAnimation.
"""
import pytest
import math
from unittest.mock import Mock, patch
from hexapod.lights.animations.direction_of_arrival_animation import DirectionOfArrivalAnimation
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
    """DirectionOfArrivalAnimation with default parameters."""
    return DirectionOfArrivalAnimation(lights=mock_lights)


@pytest.fixture
def animation_custom(mock_lights):
    """DirectionOfArrivalAnimation with custom parameters."""
    custom_colors = [ColorRGB.RED, ColorRGB.BLUE, ColorRGB.GREEN]
    return DirectionOfArrivalAnimation(
        lights=mock_lights,
        refresh_delay=0.2,
        source_colors=custom_colors
    )


class TestDirectionOfArrivalAnimation:
    """Test cases for DirectionOfArrivalAnimation class."""
    
    def test_init_default_parameters(self, mock_lights):
        """Test initialization with default parameters."""
        with patch('hexapod.lights.animations.direction_of_arrival_animation.Animation.__init__') as mock_super_init:
            animation = DirectionOfArrivalAnimation(lights=mock_lights)
            
            # Verify parent initialization
            mock_super_init.assert_called_once_with(mock_lights)
            
            # Verify default parameters
            assert animation.refresh_delay == 0.1
            assert animation.source_colors == [ColorRGB.TEAL, ColorRGB.INDIGO, ColorRGB.YELLOW, ColorRGB.LIME]
            assert animation.tracked_sources == {}
            assert animation.active_leds == set()
    
    def test_init_custom_parameters(self, mock_lights):
        """Test initialization with custom parameters."""
        custom_colors = [ColorRGB.RED, ColorRGB.BLUE]
        with patch('hexapod.lights.animations.direction_of_arrival_animation.Animation.__init__') as mock_super_init:
            animation = DirectionOfArrivalAnimation(
                lights=mock_lights,
                refresh_delay=0.2,
                source_colors=custom_colors
            )
            
            # Verify parent initialization
            mock_super_init.assert_called_once_with(mock_lights)
            
            # Verify custom parameters
            assert animation.refresh_delay == 0.2
            assert animation.source_colors == custom_colors
            assert animation.tracked_sources == {}
            assert animation.active_leds == set()
    
    def test_update_sources(self, animation_default):
        """Test update_sources method."""
        azimuths = {0: 45.0, 1: 90.0, 2: 180.0}
        
        animation_default.update_sources(azimuths)
        
        assert animation_default.azimuths == azimuths
    
    def test_get_led_indices_from_azimuth_0_degrees(self, animation_default):
        """Test LED index calculation for 0 degrees azimuth."""
        led_indices = animation_default._get_led_indices_from_azimuth(0.0)
        
        # 0 degrees should map to LED 3 (front of hexapod)
        # With 12 LEDs: 0 degrees -> (π/2 - 0) / (2π) * 12 = 3
        expected = {2, 3, 4}  # main index and adjacent
        assert led_indices == expected
    
    def test_get_led_indices_from_azimuth_90_degrees(self, animation_default):
        """Test LED index calculation for 90 degrees azimuth."""
        led_indices = animation_default._get_led_indices_from_azimuth(90.0)
        
        # 90 degrees should map to LED 0 (right side of hexapod)
        # With 12 LEDs: 90 degrees -> (π/2 - π/2) / (2π) * 12 = 0
        expected = {11, 0, 1}  # main index and adjacent (wrapping around)
        assert led_indices == expected
    
    def test_get_led_indices_from_azimuth_180_degrees(self, animation_default):
        """Test LED index calculation for 180 degrees azimuth."""
        led_indices = animation_default._get_led_indices_from_azimuth(180.0)
        
        # 180 degrees should map to LED 9 (back of hexapod)
        # With 12 LEDs: 180 degrees -> (π/2 - π) / (2π) * 12 = 9
        expected = {8, 9, 10}  # main index and adjacent
        assert led_indices == expected
    
    def test_get_led_indices_from_azimuth_270_degrees(self, animation_default):
        """Test LED index calculation for 270 degrees azimuth."""
        led_indices = animation_default._get_led_indices_from_azimuth(270.0)
        
        # 270 degrees should map to LED 6 (left side of hexapod)
        # With 12 LEDs: 270 degrees -> (π/2 - 3π/2) / (2π) * 12 = 6
        expected = {5, 6, 7}  # main index and adjacent
        assert led_indices == expected
    
    def test_get_led_indices_from_azimuth_negative_angle(self, animation_default):
        """Test LED index calculation for negative azimuth."""
        led_indices = animation_default._get_led_indices_from_azimuth(-45.0)
        
        # -45 degrees should be equivalent to 315 degrees
        # With 12 LEDs: 315 degrees -> (π/2 - 315°) / (2π) * 12 = 3
        expected = {3, 4, 5}  # main index and adjacent
        assert led_indices == expected
    
    def test_get_led_indices_from_azimuth_large_angle(self, animation_default):
        """Test LED index calculation for angle > 360 degrees."""
        led_indices = animation_default._get_led_indices_from_azimuth(450.0)
        
        # 450 degrees should be equivalent to 90 degrees
        expected = {11, 0, 1}  # same as 90 degrees
        assert led_indices == expected
    
    def test_execute_animation_no_sources(self, animation_default, mock_lights):
        """Test execute_animation with no sound sources."""
        # Mock stop_event to return True after first iteration
        animation_default.stop_event.wait = Mock(return_value=True)
        
        animation_default.execute_animation()
        
        # Verify clear was called but no LEDs were set
        mock_lights.clear.assert_called_once()
        mock_lights.set_color.assert_not_called()
        assert animation_default.active_leds == set()
    
    def test_execute_animation_single_source(self, animation_default, mock_lights):
        """Test execute_animation with single sound source."""
        # Set up a single source
        animation_default.azimuths = {0: 0.0}  # Front direction
        
        # Mock stop_event to return True after first iteration
        animation_default.stop_event.wait = Mock(return_value=True)
        
        animation_default.execute_animation()
        
        # Verify clear was called
        mock_lights.clear.assert_called_once()
        
        # Verify LEDs were set for the source
        assert mock_lights.set_color.call_count == 3  # 3 LEDs (main + 2 adjacent)
        
        # Verify correct color was used (first color in default list)
        calls = mock_lights.set_color.call_args_list
        for call in calls:
            assert call[0][0] == ColorRGB.TEAL  # First color in default list
            assert call[1]['led_index'] in {2, 3, 4}  # LEDs for 0 degrees
        
        # Verify active_leds was updated
        assert animation_default.active_leds == {2, 3, 4}
    
    def test_execute_animation_multiple_sources(self, animation_default, mock_lights):
        """Test execute_animation with multiple sound sources."""
        # Set up multiple sources
        animation_default.azimuths = {
            0: 0.0,    # Front - should use TEAL
            1: 90.0,   # Right - should use INDIGO
            2: 180.0   # Back - should use YELLOW
        }
        
        # Mock stop_event to return True after first iteration
        animation_default.stop_event.wait = Mock(return_value=True)
        
        animation_default.execute_animation()
        
        # Verify clear was called
        mock_lights.clear.assert_called_once()
        
        # Verify LEDs were set for all sources
        assert mock_lights.set_color.call_count == 9  # 3 sources * 3 LEDs each
        
        # Verify different colors were used
        calls = mock_lights.set_color.call_args_list
        colors_used = {call[0][0] for call in calls}
        assert ColorRGB.TEAL in colors_used
        assert ColorRGB.INDIGO in colors_used
        assert ColorRGB.YELLOW in colors_used
    
    def test_execute_animation_more_than_four_sources(self, animation_default, mock_lights):
        """Test execute_animation with more than 4 sources (color cycling)."""
        # Set up 6 sources
        animation_default.azimuths = {
            0: 0.0,    # Should use TEAL (0 % 4 = 0)
            1: 60.0,   # Should use INDIGO (1 % 4 = 1)
            2: 120.0,  # Should use YELLOW (2 % 4 = 2)
            3: 180.0,  # Should use LIME (3 % 4 = 3)
            4: 240.0,  # Should use TEAL (4 % 4 = 0)
            5: 300.0   # Should use INDIGO (5 % 4 = 1)
        }
        
        # Mock stop_event to return True after first iteration
        animation_default.stop_event.wait = Mock(return_value=True)
        
        animation_default.execute_animation()
        
        # Verify LEDs were set for all sources
        assert mock_lights.set_color.call_count == 18  # 6 sources * 3 LEDs each
        
        # Verify colors cycle correctly
        calls = mock_lights.set_color.call_args_list
        colors_used = {call[0][0] for call in calls}
        assert ColorRGB.TEAL in colors_used
        assert ColorRGB.INDIGO in colors_used
        assert ColorRGB.YELLOW in colors_used
        assert ColorRGB.LIME in colors_used
    
    def test_execute_animation_custom_colors(self, animation_custom, mock_lights):
        """Test execute_animation with custom source colors."""
        # Set up sources
        animation_custom.azimuths = {
            0: 0.0,    # Should use RED
            1: 90.0,   # Should use BLUE
            2: 180.0   # Should use GREEN
        }
        
        # Mock stop_event to return True after first iteration
        animation_custom.stop_event.wait = Mock(return_value=True)
        
        animation_custom.execute_animation()
        
        # Verify custom colors were used
        calls = mock_lights.set_color.call_args_list
        colors_used = {call[0][0] for call in calls}
        assert ColorRGB.RED in colors_used
        assert ColorRGB.BLUE in colors_used
        assert ColorRGB.GREEN in colors_used
    
    def test_execute_animation_custom_refresh_delay(self, animation_custom):
        """Test that custom refresh delay is used."""
        delays = []
        def mock_wait(delay):
            delays.append(delay)
            return True  # Stop immediately
        
        animation_custom.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation_custom.execute_animation()
        
        # Verify custom delay was used
        assert all(delay == 0.2 for delay in delays)
    
    def test_execute_animation_stop_immediately(self, animation_default, mock_lights):
        """Test execute_animation when stopped immediately."""
        # Mock stop_event to return True immediately
        animation_default.stop_event.wait = Mock(return_value=True)
        
        animation_default.execute_animation()
        
        # Verify clear was called but no LEDs were set
        mock_lights.clear.assert_called_once()
        mock_lights.set_color.assert_not_called()
    
    def test_execute_animation_multiple_iterations(self, animation_default, mock_lights):
        """Test execute_animation for multiple iterations."""
        # Set up a source
        animation_default.azimuths = {0: 0.0}
        
        # Mock stop_event to allow 3 iterations
        call_count = 0
        def mock_wait(delay):
            nonlocal call_count
            call_count += 1
            return call_count > 3  # Stop after 3 iterations
        
        animation_default.stop_event.wait = Mock(side_effect=mock_wait)
        
        animation_default.execute_animation()
        
        # Verify 3 iterations occurred
        assert mock_lights.clear.call_count == 4  # 3 iterations + initial clear
        assert mock_lights.set_color.call_count == 12  # 4 iterations * 3 LEDs
    
    def test_execute_animation_led_overlap(self, animation_default, mock_lights):
        """Test execute_animation when sources have overlapping LED indices."""
        # Set up sources that will overlap
        animation_default.azimuths = {
            0: 0.0,    # LEDs 2, 3, 4
            1: 30.0    # Might overlap with first source
        }
        
        # Mock stop_event to return True after first iteration
        animation_default.stop_event.wait = Mock(return_value=True)
        
        animation_default.execute_animation()
        
        # Verify clear was called
        mock_lights.clear.assert_called_once()
        
        # Verify LEDs were set (may have overlapping indices)
        assert mock_lights.set_color.call_count >= 3  # At least 3 LEDs for first source
    
    def test_execute_animation_azimuths_attribute_missing(self, animation_default, mock_lights):
        """Test execute_animation when azimuths attribute is missing."""
        # Don't set azimuths attribute
        # Mock stop_event to return True after first iteration
        animation_default.stop_event.wait = Mock(return_value=True)
        
        animation_default.execute_animation()
        
        # Verify clear was called but no LEDs were set
        mock_lights.clear.assert_called_once()
        mock_lights.set_color.assert_not_called()
    
    def test_attributes_after_init(self, animation_custom):
        """Test that all attributes are properly set after initialization."""
        assert animation_custom.refresh_delay == 0.2
        assert animation_custom.source_colors == [ColorRGB.RED, ColorRGB.BLUE, ColorRGB.GREEN]
        assert animation_custom.tracked_sources == {}
        assert animation_custom.active_leds == set()
        assert hasattr(animation_custom, 'lights')
        assert hasattr(animation_custom, 'stop_event')
    
    def test_inheritance(self, animation_default):
        """Test that DirectionOfArrivalAnimation inherits from Animation."""
        from hexapod.lights.animations.animation import Animation
        assert isinstance(animation_default, Animation)
    
    def test_override_decorator(self, animation_default):
        """Test that execute_animation has the @override decorator."""
        import inspect
        source = inspect.getsource(animation_default.execute_animation)
        assert '@override' in source
    
    def test_math_operations(self, animation_default):
        """Test mathematical operations in LED index calculation."""
        # Test various angles to ensure math operations work correctly
        test_cases = [
            (0.0, 3),      # 0 degrees -> {2, 3, 4}
            (45.0, 0),     # 45 degrees -> {0, 1, 2}
            (90.0, 0),     # 90 degrees -> {0, 1, 11}
            (135.0, 9),    # 135 degrees -> {9, 10, 11}
            (180.0, 9),    # 180 degrees -> {8, 9, 10}
            (225.0, 6),    # 225 degrees -> {8, 6, 7}
            (270.0, 6),    # 270 degrees -> {5, 6, 7}
            (315.0, 3),    # 315 degrees -> {3, 4, 5}
        ]
        
        for azimuth, expected_main in test_cases:
            led_indices = animation_default._get_led_indices_from_azimuth(azimuth)
            # The main index should be in the set
            assert expected_main in led_indices
            # Should have 3 LEDs (main + 2 adjacent)
            assert len(led_indices) == 3
