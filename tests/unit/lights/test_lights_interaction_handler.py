"""
Unit tests for lights interaction handler.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from hexapod.lights.lights_interaction_handler import LightsInteractionHandler
from hexapod.lights.lights import ColorRGB


@pytest.fixture
def mock_lights():
    """Mock Lights object."""
    mock_lights = Mock()
    mock_lights.clear = Mock()
    mock_lights.set_color = Mock()
    mock_lights.set_brightness = Mock()
    return mock_lights


@pytest.fixture
def mock_animation():
    """Mock Animation object."""
    mock_anim = Mock()
    mock_anim.stop_animation = Mock()
    mock_anim.start = Mock()
    return mock_anim


@pytest.fixture
def sample_leg_to_led():
    """Sample leg to LED mapping."""
    return {0: 0, 1: 2, 2: 4, 3: 6, 4: 8, 5: 10}


@pytest.fixture
def handler_default(mock_lights, sample_leg_to_led):
    """LightsInteractionHandler instance with default parameters."""
    with patch('hexapod.lights.lights_interaction_handler.Lights', return_value=mock_lights), \
         patch('hexapod.lights.lights_interaction_handler.logger'):
        return LightsInteractionHandler(leg_to_led=sample_leg_to_led)


@pytest.fixture
def handler_with_animation(mock_lights, mock_animation, sample_leg_to_led):
    """LightsInteractionHandler instance with an active animation."""
    with patch('hexapod.lights.lights_interaction_handler.Lights', return_value=mock_lights), \
         patch('hexapod.lights.lights_interaction_handler.logger'):
        handler = LightsInteractionHandler(leg_to_led=sample_leg_to_led)
        # Set animation after creation to avoid it being reset
        handler.animation = mock_animation
        return handler


class TestLightsInteractionHandler:
    """Test cases for LightsInteractionHandler class."""
    
    def test_init_default_parameters(self, mock_lights, sample_leg_to_led):
        """Test LightsInteractionHandler initialization with default parameters."""
        with patch('hexapod.lights.lights_interaction_handler.Lights', return_value=mock_lights) as mock_lights_class, \
             patch('hexapod.lights.lights_interaction_handler.logger') as mock_logger:
            
            handler = LightsInteractionHandler(leg_to_led=sample_leg_to_led)
            
            assert handler.lights == mock_lights
            assert handler.animation is None
            assert handler.leg_to_led == sample_leg_to_led
            
            # Verify initialization calls
            mock_lights_class.assert_called_once()
            mock_logger.info.assert_called_once_with("LightsInteractionHandler initialized successfully.")
    
    def test_init_custom_parameters(self, mock_lights):
        """Test LightsInteractionHandler initialization with custom parameters."""
        custom_leg_to_led = {0: 1, 1: 3, 2: 5}
        
        with patch('hexapod.lights.lights_interaction_handler.Lights', return_value=mock_lights), \
             patch('hexapod.lights.lights_interaction_handler.logger'):
            
            handler = LightsInteractionHandler(leg_to_led=custom_leg_to_led)
            
            assert handler.lights == mock_lights
            assert handler.animation is None
            assert handler.leg_to_led == custom_leg_to_led
    
    def test_stop_animation_with_active_animation(self, handler_default, mock_animation):
        """Test stopping an active animation."""
        # Set up handler with animation
        handler_default.animation = mock_animation
        
        with patch('hexapod.lights.lights_interaction_handler.logger') as mock_logger:
            handler_default.stop_animation()
            
            # Verify animation was stopped
            mock_animation.stop_animation.assert_called_once()
            assert handler_default.animation is None
            mock_logger.info.assert_called_with(f"Stopping currently running animation {mock_animation}")
    
    def test_stop_animation_without_active_animation(self, handler_default):
        """Test stopping when no animation is active."""
        with patch('hexapod.lights.lights_interaction_handler.logger') as mock_logger:
            handler_default.stop_animation()
            
            # Verify no animation was stopped
            mock_logger.info.assert_called_with("No active animation to stop.")
    
    def test_stop_animation_with_none_animation(self, handler_default):
        """Test stopping when animation is None."""
        handler_default.animation = None
        
        with patch('hexapod.lights.lights_interaction_handler.logger') as mock_logger:
            handler_default.stop_animation()
            
            # Verify no animation was stopped
            mock_logger.info.assert_called_with("No active animation to stop.")
    
    def test_off(self, handler_default, mock_animation):
        """Test turning off lights and stopping animation."""
        # Set up handler with animation
        handler_default.animation = mock_animation
        
        with patch('hexapod.lights.lights_interaction_handler.logger') as mock_logger:
            handler_default.off()
            
            # Verify animation was stopped and lights were cleared
            mock_animation.stop_animation.assert_called_once()
            handler_default.lights.clear.assert_called_once()
            assert handler_default.animation is None
            mock_logger.debug.assert_called_with("Lights turned off.")
    
    def test_set_single_color_all_leds(self, handler_default):
        """Test setting all LEDs to a single color."""
        with patch('hexapod.lights.lights_interaction_handler.logger') as mock_logger:
            handler_default.set_single_color(ColorRGB.RED)
            
            # Verify lights were turned off and color was set
            handler_default.lights.clear.assert_called_once()
            handler_default.lights.set_color.assert_called_once_with(ColorRGB.RED)
            mock_logger.debug.assert_called_with("All LEDs set to RED.")
    
    def test_set_single_color_specific_led(self, handler_default):
        """Test setting a specific LED to a single color."""
        with patch('hexapod.lights.lights_interaction_handler.logger') as mock_logger:
            handler_default.set_single_color(ColorRGB.BLUE, led_index=5)
            
            # Verify lights were turned off and specific LED color was set
            handler_default.lights.clear.assert_called_once()
            handler_default.lights.set_color.assert_called_once_with(ColorRGB.BLUE, led_index=5)
            mock_logger.debug.assert_called_with("LED 5 set to BLUE.")
    
    def test_set_brightness(self, handler_default):
        """Test setting brightness."""
        with patch('hexapod.lights.lights_interaction_handler.logger') as mock_logger:
            handler_default.set_brightness(75)
            
            # Verify brightness was set
            handler_default.lights.set_brightness.assert_called_once_with(75)
            mock_logger.info.assert_called_with("Brightness set to 75%.")
    
    def test_anim_decorator_success(self, handler_default, mock_animation):
        """Test the @anim decorator with successful animation setup."""
        with patch('hexapod.lights.lights_interaction_handler.logger') as mock_logger, \
             patch('hexapod.lights.lights_interaction_handler.animations.WheelFillAnimation', return_value=mock_animation):
            
            # Call a method decorated with @anim
            handler_default.rainbow()
            
            # Verify animation was set and started
            assert handler_default.animation == mock_animation
            mock_animation.start.assert_called_once()
            # Check that both logging calls were made (off() calls stop_animation first)
            assert mock_logger.info.call_count == 2  # "No active animation to stop." + "Starting animation rainbow."
            mock_logger.debug.assert_called_with(f"'rainbow' successfully set animation attribute: {mock_animation}")
    
    def test_anim_decorator_missing_animation_attribute(self, handler_default):
        """Test the @anim decorator when animation attribute is not set."""
        # Create a method that doesn't set self.animation
        def bad_method(self):
            pass
        
        # Apply the decorator
        decorated_method = LightsInteractionHandler.anim(bad_method)
        
        with patch('hexapod.lights.lights_interaction_handler.logger') as mock_logger:
            with pytest.raises(AttributeError, match="bad_method must set 'self.animation' attribute"):
                decorated_method(handler_default)
            
            mock_logger.error.assert_called_with("bad_method must set 'self.animation' attribute.")
    
    def test_anim_decorator_exception_handling(self, handler_default):
        """Test the @anim decorator exception handling."""
        # Create a method that raises an exception
        def error_method(self):
            raise ValueError("Test error")
        
        # Apply the decorator
        decorated_method = LightsInteractionHandler.anim(error_method)
        
        with patch('hexapod.lights.lights_interaction_handler.logger') as mock_logger:
            with pytest.raises(ValueError, match="Test error"):
                decorated_method(handler_default)
            
            mock_logger.exception.assert_called_with("Error in error_method: Test error")
    
    def test_rainbow_animation_default(self, handler_default, mock_animation):
        """Test rainbow animation with default parameters."""
        with patch('hexapod.lights.lights_interaction_handler.animations.WheelFillAnimation', return_value=mock_animation):
            handler_default.rainbow()
            
            # Verify animation was created with correct parameters
            from hexapod.lights.lights_interaction_handler import animations
            animations.WheelFillAnimation.assert_called_once_with(
                lights=handler_default.lights,
                use_rainbow=True,
                color=ColorRGB.WHITE,
                interval=0.2
            )
    
    def test_rainbow_animation_custom(self, handler_default, mock_animation):
        """Test rainbow animation with custom parameters."""
        with patch('hexapod.lights.lights_interaction_handler.animations.WheelFillAnimation', return_value=mock_animation):
            handler_default.rainbow(use_rainbow=False, color=ColorRGB.BLUE, interval=0.5)
            
            # Verify animation was created with custom parameters
            from hexapod.lights.lights_interaction_handler import animations
            animations.WheelFillAnimation.assert_called_once_with(
                lights=handler_default.lights,
                use_rainbow=False,
                color=ColorRGB.BLUE,
                interval=0.5
            )
    
    def test_listen_wakeword_animation(self, handler_default, mock_animation):
        """Test listen_wakeword animation."""
        with patch('hexapod.lights.lights_interaction_handler.animations.PulseSmoothlyAnimation', return_value=mock_animation):
            handler_default.listen_wakeword(
                base_color=ColorRGB.RED,
                pulse_color=ColorRGB.YELLOW,
                pulse_speed=0.1
            )
            
            # Verify animation was created with correct parameters
            from hexapod.lights.lights_interaction_handler import animations
            animations.PulseSmoothlyAnimation.assert_called_once_with(
                lights=handler_default.lights,
                base_color=ColorRGB.RED,
                pulse_color=ColorRGB.YELLOW,
                pulse_speed=0.1
            )
    
    def test_listen_wakeword_animation_default(self, handler_default, mock_animation):
        """Test listen_wakeword animation with default parameters."""
        with patch('hexapod.lights.lights_interaction_handler.animations.PulseSmoothlyAnimation', return_value=mock_animation):
            handler_default.listen_wakeword()
            
            # Verify animation was created with default parameters
            from hexapod.lights.lights_interaction_handler import animations
            animations.PulseSmoothlyAnimation.assert_called_once_with(
                lights=handler_default.lights,
                base_color=ColorRGB.BLUE,
                pulse_color=ColorRGB.GREEN,
                pulse_speed=0.05
            )
    
    def test_listen_intent_animation(self, handler_default, mock_animation):
        """Test listen_intent animation."""
        with patch('hexapod.lights.lights_interaction_handler.animations.AlternateRotateAnimation', return_value=mock_animation):
            handler_default.listen_intent(
                color_even=ColorRGB.GREEN,
                color_odd=ColorRGB.RED,
                delay=0.3
            )
            
            # Verify animation was created with correct parameters
            from hexapod.lights.lights_interaction_handler import animations
            animations.AlternateRotateAnimation.assert_called_once_with(
                lights=handler_default.lights,
                color_even=ColorRGB.GREEN,
                color_odd=ColorRGB.RED,
                delay=0.3
            )
    
    def test_think_animation(self, handler_default, mock_animation):
        """Test think animation."""
        with patch('hexapod.lights.lights_interaction_handler.animations.OppositeRotateAnimation', return_value=mock_animation):
            handler_default.think(color=ColorRGB.PURPLE, interval=0.2)
            
            # Verify animation was created with correct parameters
            from hexapod.lights.lights_interaction_handler import animations
            animations.OppositeRotateAnimation.assert_called_once_with(
                lights=handler_default.lights,
                interval=0.2,
                color=ColorRGB.PURPLE
            )
    
    def test_police_animation(self, handler_default, mock_animation):
        """Test police animation."""
        with patch('hexapod.lights.lights_interaction_handler.animations.PulseAnimation', return_value=mock_animation):
            handler_default.police(pulse_speed=0.5)
            
            # Verify animation was created with correct parameters
            from hexapod.lights.lights_interaction_handler import animations
            animations.PulseAnimation.assert_called_once_with(
                lights=handler_default.lights,
                base_color=ColorRGB.BLUE,
                pulse_color=ColorRGB.RED,
                pulse_speed=0.5
            )
    
    def test_shutdown_animation(self, handler_default, mock_animation):
        """Test shutdown animation."""
        with patch('hexapod.lights.lights_interaction_handler.animations.WheelFillAnimation', return_value=mock_animation):
            handler_default.shutdown(interval=2.0)
            
            # Verify animation was created with correct parameters
            from hexapod.lights.lights_interaction_handler import animations
            animations.WheelFillAnimation.assert_called_once_with(
                lights=handler_default.lights,
                use_rainbow=False,
                color=ColorRGB.RED,
                interval=2.0
            )
    
    def test_update_calibration_leds_status(self, handler_default, mock_animation):
        """Test update_calibration_leds_status animation."""
        calibration_status = {0: "good", 1: "bad", 2: "good"}
        
        with patch('hexapod.lights.lights_interaction_handler.animations.CalibrationAnimation', return_value=mock_animation):
            handler_default.update_calibration_leds_status(calibration_status)
            
            # Verify animation was created with correct parameters
            from hexapod.lights.lights_interaction_handler import animations
            animations.CalibrationAnimation.assert_called_once_with(
                lights=handler_default.lights,
                calibration_status=calibration_status,
                leg_to_led=handler_default.leg_to_led
            )
    
    def test_speak_animation_not_implemented(self, handler_default):
        """Test speak animation raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="The 'speak' method is not implemented yet."):
            handler_default.speak()
    
    def test_direction_of_arrival_animation_default(self, handler_default, mock_animation):
        """Test direction_of_arrival animation with default parameters."""
        with patch('hexapod.lights.lights_interaction_handler.animations.DirectionOfArrivalAnimation', return_value=mock_animation):
            handler_default.direction_of_arrival()
            
            # Verify animation was created with default parameters
            from hexapod.lights.lights_interaction_handler import animations
            animations.DirectionOfArrivalAnimation.assert_called_once_with(
                lights=handler_default.lights,
                refresh_delay=0.1,
                source_colors=[ColorRGB.TEAL, ColorRGB.INDIGO, ColorRGB.YELLOW, ColorRGB.LIME]
            )
    
    def test_direction_of_arrival_animation_custom(self, handler_default, mock_animation):
        """Test direction_of_arrival animation with custom parameters."""
        custom_colors = [ColorRGB.RED, ColorRGB.BLUE, ColorRGB.GREEN]
        
        with patch('hexapod.lights.lights_interaction_handler.animations.DirectionOfArrivalAnimation', return_value=mock_animation):
            handler_default.direction_of_arrival(refresh_delay=0.2, source_colors=custom_colors)
            
            # Verify animation was created with custom parameters
            from hexapod.lights.lights_interaction_handler import animations
            animations.DirectionOfArrivalAnimation.assert_called_once_with(
                lights=handler_default.lights,
                refresh_delay=0.2,
                source_colors=custom_colors
            )
    
    def test_odas_loading_animation(self, handler_default, mock_animation):
        """Test odas_loading animation."""
        with patch('hexapod.lights.lights_interaction_handler.animations.WheelFillAnimation', return_value=mock_animation):
            handler_default.odas_loading(interval=0.1)
            
            # Verify animation was created with correct parameters
            from hexapod.lights.lights_interaction_handler import animations
            animations.WheelFillAnimation.assert_called_once_with(
                lights=handler_default.lights,
                use_rainbow=False,
                color=ColorRGB.TEAL,
                interval=0.1
            )
    
    def test_odas_loading_animation_default(self, handler_default, mock_animation):
        """Test odas_loading animation with default parameters."""
        with patch('hexapod.lights.lights_interaction_handler.animations.WheelFillAnimation', return_value=mock_animation):
            handler_default.odas_loading()
            
            # Verify animation was created with default parameters
            from hexapod.lights.lights_interaction_handler import animations
            animations.WheelFillAnimation.assert_called_once_with(
                lights=handler_default.lights,
                use_rainbow=False,
                color=ColorRGB.TEAL,
                interval=1.5 / 12
            )
    
    def test_pulse_smoothly_animation(self, handler_default, mock_animation):
        """Test pulse_smoothly animation."""
        with patch('hexapod.lights.lights_interaction_handler.animations.PulseSmoothlyAnimation', return_value=mock_animation):
            handler_default.pulse_smoothly(
                base_color=ColorRGB.GREEN,
                pulse_color=ColorRGB.BLACK,
                pulse_speed=0.1
            )
            
            # Verify animation was created with correct parameters
            from hexapod.lights.lights_interaction_handler import animations
            animations.PulseSmoothlyAnimation.assert_called_once_with(
                lights=handler_default.lights,
                base_color=ColorRGB.GREEN,
                pulse_color=ColorRGB.BLACK,
                pulse_speed=0.1
            )
    
    def test_wheel_animation_default(self, handler_default, mock_animation):
        """Test wheel animation with default parameters."""
        with patch('hexapod.lights.lights_interaction_handler.animations.WheelAnimation', return_value=mock_animation):
            handler_default.wheel()
            
            # Verify animation was created with default parameters
            from hexapod.lights.lights_interaction_handler import animations
            animations.WheelAnimation.assert_called_once_with(
                lights=handler_default.lights,
                use_rainbow=True,
                color=None,
                interval=0.1
            )
    
    def test_wheel_animation_custom(self, handler_default, mock_animation):
        """Test wheel animation with custom parameters."""
        with patch('hexapod.lights.lights_interaction_handler.animations.WheelAnimation', return_value=mock_animation):
            handler_default.wheel(use_rainbow=False, color=ColorRGB.ORANGE, interval=0.3)
            
            # Verify animation was created with custom parameters
            from hexapod.lights.lights_interaction_handler import animations
            animations.WheelAnimation.assert_called_once_with(
                lights=handler_default.lights,
                use_rainbow=False,
                color=ColorRGB.ORANGE,
                interval=0.3
            )
    
    def test_all_animation_methods_call_off(self, handler_default, mock_animation):
        """Test that all animation methods call off() first."""
        # Map method names to their actual animation class names and required parameters
        animation_methods = [
            ('rainbow', 'WheelFillAnimation', []),
            ('listen_wakeword', 'PulseSmoothlyAnimation', []),
            ('listen_intent', 'AlternateRotateAnimation', []),
            ('think', 'OppositeRotateAnimation', []),
            ('police', 'PulseAnimation', []),
            ('shutdown', 'WheelFillAnimation', []),
            ('update_calibration_leds_status', 'CalibrationAnimation', [{0: "good", 1: "bad"}]),
            ('direction_of_arrival', 'DirectionOfArrivalAnimation', []),
            ('odas_loading', 'WheelFillAnimation', []),
            ('pulse_smoothly', 'PulseSmoothlyAnimation', []),
            ('wheel', 'WheelAnimation', [])
        ]
        
        for method_name, animation_class, args in animation_methods:
            if method_name == 'speak':
                continue  # Skip speak as it raises NotImplementedError
            
            # Reset the mock
            handler_default.lights.clear.reset_mock()
            
            with patch(f'hexapod.lights.lights_interaction_handler.animations.{animation_class}', return_value=mock_animation):
                method = getattr(handler_default, method_name)
                method(*args)
                
                # Verify off() was called (which calls lights.clear())
                handler_default.lights.clear.assert_called_once()
    
    def test_leg_to_led_mapping_preserved(self, sample_leg_to_led):
        """Test that leg_to_led mapping is preserved correctly."""
        with patch('hexapod.lights.lights_interaction_handler.Lights'), \
             patch('hexapod.lights.lights_interaction_handler.logger'):
            
            handler = LightsInteractionHandler(leg_to_led=sample_leg_to_led)
            assert handler.leg_to_led == sample_leg_to_led
    
    def test_animation_attribute_management(self, handler_default, mock_animation):
        """Test proper animation attribute management."""
        # Initially no animation
        assert handler_default.animation is None
        
        # Set an animation
        handler_default.animation = mock_animation
        assert handler_default.animation == mock_animation
        
        # Stop animation
        handler_default.stop_animation()
        assert handler_default.animation is None
    
    def test_anim_decorator_logging(self, handler_default, mock_animation):
        """Test that @anim decorator logs appropriately."""
        with patch('hexapod.lights.lights_interaction_handler.logger') as mock_logger, \
             patch('hexapod.lights.lights_interaction_handler.animations.WheelFillAnimation', return_value=mock_animation):
            
            handler_default.rainbow()
            
            # Verify logging calls (off() calls stop_animation first, then decorator logs)
            assert mock_logger.info.call_count == 2  # "No active animation to stop." + "Starting animation rainbow."
            mock_logger.debug.assert_called_with(f"'rainbow' successfully set animation attribute: {mock_animation}")
    
    def test_anim_decorator_wraps_preserved(self, handler_default):
        """Test that @anim decorator preserves function metadata."""
        # The decorator should preserve the original function's metadata
        assert handler_default.rainbow.__name__ == 'rainbow'
        assert handler_default.rainbow.__doc__ is not None
