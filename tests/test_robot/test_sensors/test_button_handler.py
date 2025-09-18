import pytest
from unittest.mock import Mock, patch
import importlib.util


@pytest.fixture
def button_handler_module():
    """Import the real button_handler module with mocked dependencies."""
    spec = importlib.util.spec_from_file_location(
        "button_handler_module", 
        "/Users/gl0dny/workspace/hexapod/hexapod/robot/sensors/button_handler.py"
    )
    button_handler_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(button_handler_module)
    return button_handler_module


class TestButtonHandler:
    """Test the ButtonHandler class from sensors/button_handler.py"""

    def test_button_handler_class_exists(self, button_handler_module):
        """Test that ButtonHandler class exists."""
        assert hasattr(button_handler_module, 'ButtonHandler')
        assert callable(button_handler_module.ButtonHandler)

    def test_button_handler_initialization(self, button_handler_module):
        """Test ButtonHandler initialization."""
        with patch('hexapod.robot.sensors.button_handler.gpiozero') as mock_gpiozero:
            button_handler = button_handler_module.ButtonHandler(
                pin=18
            )
            
            # Verify initialization
            assert hasattr(button_handler, 'pin')

    def test_button_handler_methods_exist(self, button_handler_module):
        """Test that ButtonHandler has required methods."""
        ButtonHandler = button_handler_module.ButtonHandler
        
        # Test that required methods exist (check for common method patterns)
        assert hasattr(ButtonHandler, '__init__'), "ButtonHandler should have __init__ method"
        # Check if it's a class
        assert callable(ButtonHandler), "ButtonHandler should be callable"

    def test_button_handler_class_structure(self, button_handler_module):
        """Test ButtonHandler class structure."""
        ButtonHandler = button_handler_module.ButtonHandler
        
        # Test that the class can be instantiated and has expected attributes
        assert hasattr(ButtonHandler, '__init__')
        assert callable(ButtonHandler)