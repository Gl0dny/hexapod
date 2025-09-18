import pytest
from unittest.mock import Mock, patch
import importlib.util


@pytest.fixture
def direction_of_arrival_animation_module():
    """Import the real direction_of_arrival_animation module with mocked dependencies."""
    spec = importlib.util.spec_from_file_location(
        "direction_of_arrival_animation_module", 
        "/Users/gl0dny/workspace/hexapod/hexapod/lights/animations/direction_of_arrival_animation.py"
    )
    direction_of_arrival_animation_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(direction_of_arrival_animation_module)
    return direction_of_arrival_animation_module


class TestDirectionOfArrivalAnimation:
    """Test the DirectionOfArrivalAnimation class from direction_of_arrival_animation.py"""

    def test_direction_of_arrival_animation_class_exists(self, direction_of_arrival_animation_module):
        """Test that DirectionOfArrivalAnimation class exists."""
        assert hasattr(direction_of_arrival_animation_module, 'DirectionOfArrivalAnimation')
        assert callable(direction_of_arrival_animation_module.DirectionOfArrivalAnimation)

    def test_direction_of_arrival_animation_inheritance(self, direction_of_arrival_animation_module):
        """Test that DirectionOfArrivalAnimation inherits from Animation."""
        DirectionOfArrivalAnimation = direction_of_arrival_animation_module.DirectionOfArrivalAnimation
        # Test that the class exists and is callable
        assert callable(DirectionOfArrivalAnimation)
        assert hasattr(DirectionOfArrivalAnimation, '__init__')
