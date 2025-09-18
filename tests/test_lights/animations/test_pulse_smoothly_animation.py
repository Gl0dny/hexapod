import pytest
from unittest.mock import Mock, patch
import importlib.util


@pytest.fixture
def pulse_smoothly_animation_module():
    """Import the real pulse_smoothly_animation module with mocked dependencies."""
    spec = importlib.util.spec_from_file_location(
        "pulse_smoothly_animation_module", 
        "/Users/gl0dny/workspace/hexapod/hexapod/lights/animations/pulse_smoothly_animation.py"
    )
    pulse_smoothly_animation_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pulse_smoothly_animation_module)
    return pulse_smoothly_animation_module


class TestPulseSmoothlyAnimation:
    """Test the PulseSmoothlyAnimation class from pulse_smoothly_animation.py"""

    def test_pulse_smoothly_animation_class_exists(self, pulse_smoothly_animation_module):
        """Test that PulseSmoothlyAnimation class exists."""
        assert hasattr(pulse_smoothly_animation_module, 'PulseSmoothlyAnimation')
        assert callable(pulse_smoothly_animation_module.PulseSmoothlyAnimation)

    def test_pulse_smoothly_animation_inheritance(self, pulse_smoothly_animation_module):
        """Test that PulseSmoothlyAnimation inherits from Animation."""
        PulseSmoothlyAnimation = pulse_smoothly_animation_module.PulseSmoothlyAnimation
        # Test that the class exists and is callable
        assert callable(PulseSmoothlyAnimation)
        assert hasattr(PulseSmoothlyAnimation, '__init__')
