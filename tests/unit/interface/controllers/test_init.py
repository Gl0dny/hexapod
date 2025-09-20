"""
Unit tests for controllers/__init__.py module.
"""

import pytest
from unittest.mock import Mock, patch

from hexapod.interface.controllers import (
    ManualHexapodController,
    GamepadHexapodController,
    BaseGamepadLEDController,
    DualSenseLEDController,
    GamepadLEDColor,
)


class TestControllersInit:
    """Test cases for controllers package __init__.py."""

    def test_module_imports(self):
        """Test that all expected classes can be imported."""
        from hexapod.interface.controllers import (
            ManualHexapodController,
            GamepadHexapodController,
            BaseGamepadLEDController,
            DualSenseLEDController,
            GamepadLEDColor,
        )
        
        # Verify all imports are available
        assert ManualHexapodController is not None
        assert GamepadHexapodController is not None
        assert BaseGamepadLEDController is not None
        assert DualSenseLEDController is not None
        assert GamepadLEDColor is not None

    def test_manual_hexapod_controller_import(self):
        """Test ManualHexapodController import."""
        from hexapod.interface.controllers.base_manual_controller import ManualHexapodController
        
        assert ManualHexapodController is not None
        assert hasattr(ManualHexapodController, '__init__')
        assert hasattr(ManualHexapodController, 'get_inputs')
        assert hasattr(ManualHexapodController, 'print_help')

    def test_gamepad_hexapod_controller_import(self):
        """Test GamepadHexapodController import."""
        from hexapod.interface.controllers.gamepad_hexapod_controller import GamepadHexapodController
        
        assert GamepadHexapodController is not None
        assert hasattr(GamepadHexapodController, '__init__')
        assert hasattr(GamepadHexapodController, 'find_gamepad')
        assert hasattr(GamepadHexapodController, 'get_gamepad_connection_type')

    def test_base_gamepad_led_controller_import(self):
        """Test BaseGamepadLEDController import."""
        from hexapod.interface.controllers.gamepad_led_controllers.gamepad_led_controller import BaseGamepadLEDController
        
        assert BaseGamepadLEDController is not None
        assert hasattr(BaseGamepadLEDController, '__init__')
        assert hasattr(BaseGamepadLEDController, 'set_color')
        assert hasattr(BaseGamepadLEDController, 'pulse')

    def test_dual_sense_led_controller_import(self):
        """Test DualSenseLEDController import."""
        from hexapod.interface.controllers.gamepad_led_controllers.dual_sense_led_controller import DualSenseLEDController
        
        assert DualSenseLEDController is not None
        assert hasattr(DualSenseLEDController, '__init__')
        assert hasattr(DualSenseLEDController, '_connect_controller')
        assert hasattr(DualSenseLEDController, '_set_color_internal')

    def test_gamepad_led_color_import(self):
        """Test GamepadLEDColor import."""
        from hexapod.interface.controllers.gamepad_led_controllers.gamepad_led_controller import GamepadLEDColor
        
        assert GamepadLEDColor is not None
        assert hasattr(GamepadLEDColor, 'RED')
        assert hasattr(GamepadLEDColor, 'GREEN')
        assert hasattr(GamepadLEDColor, 'BLUE')

    def test_all_exports_available(self):
        """Test that all items in __all__ are available."""
        from hexapod.interface.controllers import __all__
        
        expected_exports = [
            "ManualHexapodController",
            "GamepadHexapodController",
            "BaseGamepadLEDController",
            "DualSenseLEDController",
            "GamepadLEDColor",
        ]
        
        for export in expected_exports:
            assert export in __all__

    def test_all_exports_are_classes(self):
        """Test that all exports are classes (except enums)."""
        from hexapod.interface.controllers import (
            ManualHexapodController,
            GamepadHexapodController,
            BaseGamepadLEDController,
            DualSenseLEDController,
            GamepadLEDColor,
        )
        
        # Test that these are classes
        assert isinstance(ManualHexapodController, type)
        assert isinstance(GamepadHexapodController, type)
        assert isinstance(BaseGamepadLEDController, type)
        assert isinstance(DualSenseLEDController, type)
        
        # GamepadLEDColor is an enum, not a class
        assert hasattr(GamepadLEDColor, '__members__')

    def test_manual_hexapod_controller_is_abstract(self):
        """Test that ManualHexapodController is abstract."""
        from abc import ABC
        
        assert issubclass(ManualHexapodController, ABC)
        
        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            ManualHexapodController(Mock())

    def test_gamepad_hexapod_controller_inheritance(self):
        """Test that GamepadHexapodController inherits from ManualHexapodController."""
        assert issubclass(GamepadHexapodController, ManualHexapodController)

    def test_dual_sense_led_controller_inheritance(self):
        """Test that DualSenseLEDController inherits from BaseGamepadLEDController."""
        assert issubclass(DualSenseLEDController, BaseGamepadLEDController)

    def test_gamepad_led_color_enum_values(self):
        """Test GamepadLEDColor enum values."""
        assert GamepadLEDColor.RED.value == (255, 0, 0)
        assert GamepadLEDColor.GREEN.value == (0, 255, 0)
        assert GamepadLEDColor.BLUE.value == (0, 0, 255)
        assert GamepadLEDColor.BLACK.value == (0, 0, 0)

    def test_module_docstring(self):
        """Test that the module has a docstring."""
        import hexapod.interface.controllers
        
        assert hexapod.interface.controllers.__doc__ is not None
        assert "Hexapod controller package" in hexapod.interface.controllers.__doc__

    def test_import_from_submodules(self):
        """Test importing from submodules works correctly."""
        # Test importing from base_manual_controller
        from hexapod.interface.controllers.base_manual_controller import ManualHexapodController
        assert ManualHexapodController is not None
        
        # Test importing from gamepad_hexapod_controller
        from hexapod.interface.controllers.gamepad_hexapod_controller import GamepadHexapodController
        assert GamepadHexapodController is not None
        
        # Test importing from gamepad_led_controllers
        from hexapod.interface.controllers.gamepad_led_controllers import (
            BaseGamepadLEDController,
            DualSenseLEDController,
            GamepadLEDColor,
        )
        assert BaseGamepadLEDController is not None
        assert DualSenseLEDController is not None
        assert GamepadLEDColor is not None

    def test_circular_imports_work(self):
        """Test that circular imports work correctly."""
        # This test ensures that importing the package doesn't cause circular import issues
        import hexapod.interface.controllers
        
        # Try importing again to test for circular import issues
        from hexapod.interface.controllers import ManualHexapodController
        from hexapod.interface.controllers import GamepadHexapodController
        
        assert ManualHexapodController is not None
        assert GamepadHexapodController is not None

    def test_module_attributes(self):
        """Test that the module has expected attributes."""
        import hexapod.interface.controllers
        
        assert hasattr(hexapod.interface.controllers, '__all__')
        assert hasattr(hexapod.interface.controllers, '__doc__')
        assert hasattr(hexapod.interface.controllers, 'ManualHexapodController')
        assert hasattr(hexapod.interface.controllers, 'GamepadHexapodController')
        assert hasattr(hexapod.interface.controllers, 'BaseGamepadLEDController')
        assert hasattr(hexapod.interface.controllers, 'DualSenseLEDController')
        assert hasattr(hexapod.interface.controllers, 'GamepadLEDColor')

    def test_import_star_works(self):
        """Test that 'from module import *' works correctly."""
        # This is a bit tricky to test, but we can verify the __all__ list
        import hexapod.interface.controllers
        
        # Get all public attributes
        public_attrs = [attr for attr in dir(hexapod.interface.controllers) 
                       if not attr.startswith('_')]
        
        # Check that __all__ contains the expected items
        expected_items = [
            "ManualHexapodController",
            "GamepadHexapodController", 
            "BaseGamepadLEDController",
            "DualSenseLEDController",
            "GamepadLEDColor",
        ]
        
        for item in expected_items:
            assert item in public_attrs

    def test_class_names_are_correct(self):
        """Test that imported class names are correct."""
        from hexapod.interface.controllers import (
            ManualHexapodController,
            GamepadHexapodController,
            BaseGamepadLEDController,
            DualSenseLEDController,
            GamepadLEDColor,
        )
        
        assert ManualHexapodController.__name__ == "ManualHexapodController"
        assert GamepadHexapodController.__name__ == "GamepadHexapodController"
        assert BaseGamepadLEDController.__name__ == "BaseGamepadLEDController"
        assert DualSenseLEDController.__name__ == "DualSenseLEDController"
        assert GamepadLEDColor.__name__ == "GamepadLEDColor"

    def test_class_modules_are_correct(self):
        """Test that imported classes have correct module paths."""
        from hexapod.interface.controllers import (
            ManualHexapodController,
            GamepadHexapodController,
            BaseGamepadLEDController,
            DualSenseLEDController,
        )
        
        assert "hexapod.interface.controllers.base_manual_controller" in ManualHexapodController.__module__
        assert "hexapod.interface.controllers.gamepad_hexapod_controller" in GamepadHexapodController.__module__
        assert "hexapod.interface.controllers.gamepad_led_controllers.gamepad_led_controller" in BaseGamepadLEDController.__module__
        assert "hexapod.interface.controllers.gamepad_led_controllers.dual_sense_led_controller" in DualSenseLEDController.__module__

    def test_import_performance(self):
        """Test that imports are reasonably fast."""
        import time
        
        start_time = time.time()
        
        # Import the entire package
        import hexapod.interface.controllers
        from hexapod.interface.controllers import (
            ManualHexapodController,
            GamepadHexapodController,
            BaseGamepadLEDController,
            DualSenseLEDController,
            GamepadLEDColor,
        )
        
        end_time = time.time()
        import_time = end_time - start_time
        
        # Should import in less than 1 second (very generous)
        assert import_time < 1.0

    def test_no_side_effects_on_import(self):
        """Test that importing doesn't cause side effects."""
        # This test ensures that importing the module doesn't cause unexpected side effects
        # like initializing hardware, creating threads, etc.
        
        # Mock any potential side effects
        with patch('hexapod.interface.controllers.gamepad_hexapod_controller.pygame') as mock_pygame:
            with patch('dualsense_controller.DualSenseController'):
                # Import should not cause pygame.init() to be called
                import hexapod.interface.controllers
                
                # pygame.init() should not have been called during import
                mock_pygame.init.assert_not_called()
