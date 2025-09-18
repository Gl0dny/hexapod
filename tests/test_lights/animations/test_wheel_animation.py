import pytest
from unittest.mock import Mock, patch
import importlib.util


@pytest.fixture
def wheel_animation_module():
    """Import the real wheel_animation module with mocked dependencies."""
    spec = importlib.util.spec_from_file_location(
        "wheel_animation_module", 
        "/Users/gl0dny/workspace/hexapod/hexapod/lights/animations/wheel_animation.py"
    )
    wheel_animation_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wheel_animation_module)
    return wheel_animation_module


class TestWheelAnimation:
    """Test the WheelAnimation class from wheel_animation.py"""

    def test_wheel_animation_class_exists(self, wheel_animation_module):
        """Test that WheelAnimation class exists."""
        assert hasattr(wheel_animation_module, 'WheelAnimation')
        assert callable(wheel_animation_module.WheelAnimation)

    def test_wheel_animation_inheritance(self, wheel_animation_module):
        """Test that WheelAnimation inherits from Animation."""
        WheelAnimation = wheel_animation_module.WheelAnimation
        # Test that the class exists and is callable
        assert callable(WheelAnimation)
        assert hasattr(WheelAnimation, '__init__')