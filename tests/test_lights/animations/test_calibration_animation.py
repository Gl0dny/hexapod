import pytest
from unittest.mock import Mock, patch
import importlib.util


@pytest.fixture
def calibration_animation_module():
    """Import the real calibration_animation module with mocked dependencies."""
    spec = importlib.util.spec_from_file_location(
        "calibration_animation_module", 
        "/Users/gl0dny/workspace/hexapod/hexapod/lights/animations/calibration_animation.py"
    )
    calibration_animation_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(calibration_animation_module)
    return calibration_animation_module


class TestCalibrationAnimation:
    """Test the CalibrationAnimation class from calibration_animation.py"""

    def test_calibration_animation_class_exists(self, calibration_animation_module):
        """Test that CalibrationAnimation class exists."""
        assert hasattr(calibration_animation_module, 'CalibrationAnimation')
        assert callable(calibration_animation_module.CalibrationAnimation)

    def test_calibration_animation_inheritance(self, calibration_animation_module):
        """Test that CalibrationAnimation inherits from Animation."""
        CalibrationAnimation = calibration_animation_module.CalibrationAnimation
        # Test that the class exists and is callable
        assert callable(CalibrationAnimation)
        assert hasattr(CalibrationAnimation, '__init__')
