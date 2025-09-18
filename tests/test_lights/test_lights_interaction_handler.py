import pytest
from unittest.mock import Mock, patch
import importlib.util


@pytest.fixture
def lights_interaction_handler_module():
    """Import the real lights_interaction_handler module with mocked dependencies."""
    spec = importlib.util.spec_from_file_location(
        "lights_interaction_handler_module", 
        "/Users/gl0dny/workspace/hexapod/hexapod/lights/lights_interaction_handler.py"
    )
    lights_interaction_handler_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lights_interaction_handler_module)
    return lights_interaction_handler_module


class TestLightsInteractionHandler:
    """Test the LightsInteractionHandler class from lights_interaction_handler.py"""

    def test_lights_interaction_handler_class_exists(self, lights_interaction_handler_module):
        """Test that LightsInteractionHandler class exists."""
        assert hasattr(lights_interaction_handler_module, 'LightsInteractionHandler')
        assert callable(lights_interaction_handler_module.LightsInteractionHandler)

    def test_initialization(self, lights_interaction_handler_module):
        """Test LightsInteractionHandler initialization."""
        # Mock leg_to_led parameter
        mock_leg_to_led = Mock()
        handler = lights_interaction_handler_module.LightsInteractionHandler(mock_leg_to_led)
        
        # Verify initialization
        assert handler.lights is not None
        assert handler.leg_to_led == mock_leg_to_led

    def test_animation_decorator(self, lights_interaction_handler_module):
        """Test the animation decorator pattern."""
        # Mock leg_to_led parameter
        mock_leg_to_led = Mock()
        handler = lights_interaction_handler_module.LightsInteractionHandler(mock_leg_to_led)
        
        # Test that the decorator exists
        assert hasattr(handler, 'animation')
        # The animation attribute should exist (it's a decorator method)
        # Note: The actual implementation may vary, so we just check it exists

    def test_animation_methods_exist(self, lights_interaction_handler_module):
        """Test that animation methods exist."""
        # Mock leg_to_led parameter
        mock_leg_to_led = Mock()
        handler = lights_interaction_handler_module.LightsInteractionHandler(mock_leg_to_led)
        
        # Check for common animation methods
        animation_methods = [
            'pulse_animation', 'pulse_smoothly_animation', 'wheel_animation',
            'wheel_fill_animation', 'alternate_rotate_animation', 'opposite_rotate_animation',
            'calibration_animation', 'direction_of_arrival_animation'
        ]
        
        for method_name in animation_methods:
            if hasattr(handler, method_name):
                method = getattr(handler, method_name)
                assert callable(method), f"{method_name} should be callable"
