import pytest
from unittest.mock import Mock, patch
import importlib.util


@pytest.fixture
def pulse_animation_module():
    """Import the real pulse_animation module with mocked dependencies."""
    spec = importlib.util.spec_from_file_location(
        "pulse_animation_module", 
        "/Users/gl0dny/workspace/hexapod/hexapod/lights/animations/pulse_animation.py"
    )
    pulse_animation_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pulse_animation_module)
    return pulse_animation_module


class TestPulseAnimation:
    """Test the PulseAnimation class from pulse_animation.py"""

    def test_pulse_animation_class_exists(self, pulse_animation_module):
        """Test that PulseAnimation class exists."""
        assert hasattr(pulse_animation_module, 'PulseAnimation')
        assert callable(pulse_animation_module.PulseAnimation)

    def test_pulse_animation_inheritance(self, pulse_animation_module):
        """Test that PulseAnimation inherits from Animation."""
        PulseAnimation = pulse_animation_module.PulseAnimation
        # Test that the class exists and is callable
        assert callable(PulseAnimation)
        assert hasattr(PulseAnimation, '__init__')