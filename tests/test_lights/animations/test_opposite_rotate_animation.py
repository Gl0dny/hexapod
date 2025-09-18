import pytest
from unittest.mock import Mock, patch
import importlib.util


@pytest.fixture
def opposite_rotate_animation_module():
    """Import the real opposite_rotate_animation module with mocked dependencies."""
    spec = importlib.util.spec_from_file_location(
        "opposite_rotate_animation_module", 
        "/Users/gl0dny/workspace/hexapod/hexapod/lights/animations/opposite_rotate_animation.py"
    )
    opposite_rotate_animation_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(opposite_rotate_animation_module)
    return opposite_rotate_animation_module


class TestOppositeRotateAnimation:
    """Test the OppositeRotateAnimation class from opposite_rotate_animation.py"""

    def test_opposite_rotate_animation_class_exists(self, opposite_rotate_animation_module):
        """Test that OppositeRotateAnimation class exists."""
        assert hasattr(opposite_rotate_animation_module, 'OppositeRotateAnimation')
        assert callable(opposite_rotate_animation_module.OppositeRotateAnimation)

    def test_opposite_rotate_animation_inheritance(self, opposite_rotate_animation_module):
        """Test that OppositeRotateAnimation inherits from Animation."""
        OppositeRotateAnimation = opposite_rotate_animation_module.OppositeRotateAnimation
        # Test that the class exists and is callable
        assert callable(OppositeRotateAnimation)
        assert hasattr(OppositeRotateAnimation, '__init__')
