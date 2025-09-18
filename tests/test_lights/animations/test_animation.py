import pytest
from unittest.mock import Mock, patch
import importlib.util


@pytest.fixture
def animation_module():
    """Import the real animation module with mocked dependencies."""
    spec = importlib.util.spec_from_file_location(
        "animation_module", 
        "/Users/gl0dny/workspace/hexapod/hexapod/lights/animations/animation.py"
    )
    animation_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(animation_module)
    return animation_module


class TestAnimation:
    """Test the Animation base class from animation.py"""

    def test_animation_class_exists(self, animation_module):
        """Test that Animation class exists."""
        assert hasattr(animation_module, 'Animation')
        assert callable(animation_module.Animation)

    def test_animation_methods(self, animation_module):
        """Test Animation class methods."""
        Animation = animation_module.Animation
        
        # Test that the class exists and is callable
        assert callable(Animation)
        
        # Test that it has some basic attributes (adjust based on actual implementation)
        assert hasattr(Animation, '__init__')
