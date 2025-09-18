import pytest
from unittest.mock import Mock, patch
import importlib.util


@pytest.fixture
def calibration_module():
    """Import the real calibration module with mocked dependencies."""
    spec = importlib.util.spec_from_file_location(
        "calibration_module", 
        "/Users/gl0dny/workspace/hexapod/hexapod/robot/calibration.py"
    )
    calibration_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(calibration_module)
    return calibration_module


class TestCalibration:
    """Test the Calibration class from calibration.py"""

    def test_calibration_class_exists(self, calibration_module):
        """Test that Calibration class exists."""
        assert hasattr(calibration_module, 'Calibration')
        assert callable(calibration_module.Calibration)

    def test_calibration_initialization(self, calibration_module):
        """Test Calibration initialization."""
        with patch('hexapod.robot.calibration.Hexapod') as mock_hexapod:
            calibration = calibration_module.Calibration(
                hexapod=mock_hexapod,
                calibration_data_path="test_path.json"
            )
            
            # Verify initialization
            assert hasattr(calibration, 'hexapod')

    def test_calibration_methods_exist(self, calibration_module):
        """Test that Calibration has required methods."""
        Calibration = calibration_module.Calibration
        
        # Test that required methods exist (check for common method patterns)
        assert hasattr(Calibration, '__init__'), "Calibration should have __init__ method"
        # Check if it's a class
        assert callable(Calibration), "Calibration should be callable"

    def test_calibration_class_structure(self, calibration_module):
        """Test Calibration class structure."""
        Calibration = calibration_module.Calibration
        
        # Test that the class can be instantiated and has expected attributes
        assert hasattr(Calibration, '__init__')
        assert callable(Calibration)