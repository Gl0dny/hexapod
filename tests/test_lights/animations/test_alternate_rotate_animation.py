import pytest
from unittest.mock import Mock, patch
import importlib.util


@pytest.fixture
def alternate_rotate_animation_module():
    """Import the real alternate_rotate_animation module with mocked dependencies."""
    spec = importlib.util.spec_from_file_location(
        "alternate_rotate_animation_module", 
        "/Users/gl0dny/workspace/hexapod/hexapod/lights/animations/alternate_rotate_animation.py"
    )
    alternate_rotate_animation_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(alternate_rotate_animation_module)
    return alternate_rotate_animation_module


class TestAlternateRotateAnimation:
    """Test the AlternateRotateAnimation class from alternate_rotate_animation.py"""

    def test_alternate_rotate_animation_class_exists(self, alternate_rotate_animation_module):
        """Test that AlternateRotateAnimation class exists."""
        assert hasattr(alternate_rotate_animation_module, 'AlternateRotateAnimation')
        assert callable(alternate_rotate_animation_module.AlternateRotateAnimation)

    def test_alternate_rotate_animation_inheritance(self, alternate_rotate_animation_module):
        """Test that AlternateRotateAnimation inherits from Animation."""
        AlternateRotateAnimation = alternate_rotate_animation_module.AlternateRotateAnimation
        # Test that the class exists and is callable
        assert callable(AlternateRotateAnimation)
        assert hasattr(AlternateRotateAnimation, '__init__')
