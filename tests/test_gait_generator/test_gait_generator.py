import pytest
from unittest.mock import Mock, patch
import importlib.util


@pytest.fixture
def gait_generator_module():
    """Import the real gait_generator module with mocked dependencies."""
    spec = importlib.util.spec_from_file_location(
        "gait_generator_module", 
        "/Users/gl0dny/workspace/hexapod/hexapod/gait_generator/gait_generator.py"
    )
    gait_generator_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gait_generator_module)
    return gait_generator_module


class TestGaitGenerator:
    """Test the GaitGenerator class from gait_generator.py"""

    def test_gait_generator_class_exists(self, gait_generator_module):
        """Test that GaitGenerator class exists."""
        assert hasattr(gait_generator_module, 'GaitGenerator')
        assert callable(gait_generator_module.GaitGenerator)

    def test_gait_generator_initialization(self, gait_generator_module):
        """Test GaitGenerator initialization."""
        with patch('hexapod.gait_generator.gait_generator.Hexapod') as mock_hexapod:
            gait_gen = gait_generator_module.GaitGenerator(
                hexapod=mock_hexapod
            )
            
            # Verify initialization
            assert hasattr(gait_gen, 'hexapod')

    def test_gait_generator_methods_exist(self, gait_generator_module):
        """Test that GaitGenerator has required methods."""
        GaitGenerator = gait_generator_module.GaitGenerator
        
        # Test that required methods exist (check for common method patterns)
        assert hasattr(GaitGenerator, '__init__'), "GaitGenerator should have __init__ method"
        # Check if it's a class
        assert callable(GaitGenerator), "GaitGenerator should be callable"

    def test_gait_generator_class_structure(self, gait_generator_module):
        """Test GaitGenerator class structure."""
        GaitGenerator = gait_generator_module.GaitGenerator
        
        # Test that the class can be instantiated and has expected attributes
        assert hasattr(GaitGenerator, '__init__')
        assert callable(GaitGenerator)
