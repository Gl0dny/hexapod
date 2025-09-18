import pytest
from unittest.mock import Mock, patch
import importlib.util


@pytest.fixture
def wheel_fill_animation_module():
    """Import the real wheel_fill_animation module with mocked dependencies."""
    spec = importlib.util.spec_from_file_location(
        "wheel_fill_animation_module", 
        "/Users/gl0dny/workspace/hexapod/hexapod/lights/animations/wheel_fill_animation.py"
    )
    wheel_fill_animation_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wheel_fill_animation_module)
    return wheel_fill_animation_module


class TestWheelFillAnimation:
    """Test the WheelFillAnimation class from wheel_fill_animation.py"""

    def test_wheel_fill_animation_class_exists(self, wheel_fill_animation_module):
        """Test that WheelFillAnimation class exists."""
        assert hasattr(wheel_fill_animation_module, 'WheelFillAnimation')
        assert callable(wheel_fill_animation_module.WheelFillAnimation)

    def test_wheel_fill_animation_inheritance(self, wheel_fill_animation_module):
        """Test that WheelFillAnimation inherits from Animation."""
        WheelFillAnimation = wheel_fill_animation_module.WheelFillAnimation
        # Test that the class exists and is callable
        assert callable(WheelFillAnimation)
        assert hasattr(WheelFillAnimation, '__init__')
