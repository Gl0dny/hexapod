import pytest
from unittest.mock import Mock, patch
import importlib.util


@pytest.fixture
def apa102_module():
    """Import the real apa102 module with mocked dependencies."""
    spec = importlib.util.spec_from_file_location(
        "apa102_module", 
        "/Users/gl0dny/workspace/hexapod/hexapod/lights/apa102.py"
    )
    apa102_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(apa102_module)
    return apa102_module


class TestAPA102:
    """Test the APA102 class from apa102.py"""

    def test_apa102_class_exists(self, apa102_module):
        """Test that APA102 class exists."""
        assert hasattr(apa102_module, 'APA102')
        assert callable(apa102_module.APA102)

    def test_apa102_initialization(self, apa102_module):
        """Test APA102 class initialization."""
        # Mock the hardware dependencies
        with patch('gpiozero.pins.rpigpio.RPiGPIOFactory') as mock_factory, \
             patch('gpiozero.LED') as mock_led:
            
            apa102 = apa102_module.APA102(num_led=12)
            
            # Verify initialization
            assert apa102.num_led == 12
            assert apa102.global_brightness == 31  # Default brightness

    def test_apa102_methods_exist(self, apa102_module):
        """Test that APA102 has required methods."""
        APA102 = apa102_module.APA102
        
        # Test that required methods exist
        required_methods = ['set_pixel', 'show', 'rotate']
        
        for method_name in required_methods:
            assert hasattr(APA102, method_name), f"APA102 should have {method_name} method"
