"""
Unit tests for input_mappings module __init__.py.
"""
import pytest

from hexapod.interface.input_mappings import (
    InputMapping,
    DualSenseUSBMapping,
    DualSenseBluetoothMapping
)


class TestInputMappingsInit:
    """Test cases for input_mappings module initialization."""
    
    def test_module_imports(self):
        """Test that the module can be imported successfully."""
        import hexapod.interface.input_mappings as input_mappings_module
        assert input_mappings_module is not None
    
    def test_input_mapping_import(self):
        """Test that InputMapping can be imported from the module."""
        from hexapod.interface.input_mappings import InputMapping
        assert InputMapping is not None
        assert callable(InputMapping)
    
    def test_dual_sense_usb_mapping_import(self):
        """Test that DualSenseUSBMapping can be imported from the module."""
        from hexapod.interface.input_mappings import DualSenseUSBMapping
        assert DualSenseUSBMapping is not None
        assert callable(DualSenseUSBMapping)
    
    def test_dual_sense_bluetooth_mapping_import(self):
        """Test that DualSenseBluetoothMapping can be imported from the module."""
        from hexapod.interface.input_mappings import DualSenseBluetoothMapping
        assert DualSenseBluetoothMapping is not None
        assert callable(DualSenseBluetoothMapping)
    
    def test_all_exports_available(self):
        """Test that all expected classes are available in __all__."""
        import hexapod.interface.input_mappings as input_mappings_module
        
        expected_exports = [
            "InputMapping",
            "DualSenseUSBMapping", 
            "DualSenseBluetoothMapping"
        ]
        
        for export in expected_exports:
            assert hasattr(input_mappings_module, export)
            assert getattr(input_mappings_module, export) is not None
    
    def test_all_exports_are_classes(self):
        """Test that all exports are classes."""
        from hexapod.interface.input_mappings import (
            InputMapping,
            DualSenseUSBMapping,
            DualSenseBluetoothMapping
        )
        
        assert isinstance(InputMapping, type)
        assert isinstance(DualSenseUSBMapping, type)
        assert isinstance(DualSenseBluetoothMapping, type)
    
    def test_input_mapping_is_abstract(self):
        """Test that InputMapping is abstract."""
        from hexapod.interface.input_mappings import InputMapping
        from abc import ABC
        
        assert issubclass(InputMapping, ABC)
        assert hasattr(InputMapping, '__abstractmethods__')
        assert len(InputMapping.__abstractmethods__) > 0
    
    def test_concrete_mappings_are_not_abstract(self):
        """Test that concrete mapping classes are not abstract."""
        from hexapod.interface.input_mappings import (
            DualSenseUSBMapping,
            DualSenseBluetoothMapping
        )
        
        # These should not have abstract methods
        assert not hasattr(DualSenseUSBMapping, '__abstractmethods__') or len(DualSenseUSBMapping.__abstractmethods__) == 0
        assert not hasattr(DualSenseBluetoothMapping, '__abstractmethods__') or len(DualSenseBluetoothMapping.__abstractmethods__) == 0
    
    def test_concrete_mappings_inherit_from_input_mapping(self):
        """Test that concrete mappings inherit from InputMapping."""
        from hexapod.interface.input_mappings import (
            InputMapping,
            DualSenseUSBMapping,
            DualSenseBluetoothMapping
        )
        
        assert issubclass(DualSenseUSBMapping, InputMapping)
        assert issubclass(DualSenseBluetoothMapping, InputMapping)
    
    def test_concrete_mappings_can_be_instantiated(self):
        """Test that concrete mapping classes can be instantiated."""
        from hexapod.interface.input_mappings import (
            DualSenseUSBMapping,
            DualSenseBluetoothMapping
        )
        
        # Should be able to instantiate both
        usb_mapping = DualSenseUSBMapping()
        bluetooth_mapping = DualSenseBluetoothMapping()
        
        assert usb_mapping is not None
        assert bluetooth_mapping is not None
        assert isinstance(usb_mapping, DualSenseUSBMapping)
        assert isinstance(bluetooth_mapping, DualSenseBluetoothMapping)
    
    def test_module_docstring(self):
        """Test that the module has a proper docstring."""
        import hexapod.interface.input_mappings as input_mappings_module
        
        assert input_mappings_module.__doc__ is not None
        assert "Input mappings package" in input_mappings_module.__doc__
        assert "hexapod controllers" in input_mappings_module.__doc__
    
    def test_import_from_submodules(self):
        """Test that imports work from submodules."""
        # Test importing from base_input_mapping
        from hexapod.interface.input_mappings.base_input_mapping import InputMapping
        assert InputMapping is not None
        
        # Test importing from dual_sense_usb_mapping
        from hexapod.interface.input_mappings.dual_sense_usb_mapping import DualSenseUSBMapping
        assert DualSenseUSBMapping is not None
        
        # Test importing from dual_sense_bluetooth_mapping
        from hexapod.interface.input_mappings.dual_sense_bluetooth_mapping import DualSenseBluetoothMapping
        assert DualSenseBluetoothMapping is not None
    
    def test_circular_imports_work(self):
        """Test that circular imports work correctly."""
        # This tests that the __init__.py doesn't cause circular import issues
        from hexapod.interface.input_mappings import InputMapping
        from hexapod.interface.input_mappings.base_input_mapping import InputMapping as BaseInputMapping
        
        # Should be the same class
        assert InputMapping is BaseInputMapping
    
    def test_module_attributes(self):
        """Test that the module has expected attributes."""
        import hexapod.interface.input_mappings as input_mappings_module
        
        # Check for __all__ attribute
        assert hasattr(input_mappings_module, '__all__')
        assert isinstance(input_mappings_module.__all__, list)
        assert len(input_mappings_module.__all__) == 3
        
        # Check that __all__ contains expected items
        expected_items = [
            "InputMapping",
            "DualSenseUSBMapping",
            "DualSenseBluetoothMapping"
        ]
        for item in expected_items:
            assert item in input_mappings_module.__all__
    
    def test_import_star_works(self):
        """Test that 'from module import *' works correctly."""
        # This tests that __all__ is properly defined
        import hexapod.interface.input_mappings as input_mappings_module
        
        # Get the module's globals
        module_globals = input_mappings_module.__dict__
        
        # Check that all items in __all__ are available
        for item in input_mappings_module.__all__:
            assert item in module_globals
            assert module_globals[item] is not None
    
    def test_class_names_are_correct(self):
        """Test that class names are correct."""
        from hexapod.interface.input_mappings import (
            InputMapping,
            DualSenseUSBMapping,
            DualSenseBluetoothMapping
        )
        
        assert InputMapping.__name__ == "InputMapping"
        assert DualSenseUSBMapping.__name__ == "DualSenseUSBMapping"
        assert DualSenseBluetoothMapping.__name__ == "DualSenseBluetoothMapping"
    
    def test_class_modules_are_correct(self):
        """Test that classes have correct module names."""
        from hexapod.interface.input_mappings import (
            InputMapping,
            DualSenseUSBMapping,
            DualSenseBluetoothMapping
        )
        
        assert InputMapping.__module__ == "hexapod.interface.input_mappings.base_input_mapping"
        assert DualSenseUSBMapping.__module__ == "hexapod.interface.input_mappings.dual_sense_usb_mapping"
        assert DualSenseBluetoothMapping.__module__ == "hexapod.interface.input_mappings.dual_sense_bluetooth_mapping"
    
    def test_import_performance(self):
        """Test that imports are reasonably fast."""
        import time
        
        start_time = time.time()
        from hexapod.interface.input_mappings import (
            InputMapping,
            DualSenseUSBMapping,
            DualSenseBluetoothMapping
        )
        end_time = time.time()
        
        # Should import quickly (less than 1 second)
        assert (end_time - start_time) < 1.0
    
    def test_no_side_effects_on_import(self):
        """Test that importing the module doesn't cause side effects."""
        import sys
        import os
        
        # Store initial state
        initial_modules = set(sys.modules.keys())
        initial_env = dict(os.environ)
        
        # Import the module
        from hexapod.interface.input_mappings import (
            InputMapping,
            DualSenseUSBMapping,
            DualSenseBluetoothMapping
        )
        
        # Check that no unexpected modules were loaded
        new_modules = set(sys.modules.keys()) - initial_modules
        # Should only load expected modules
        expected_new_modules = {
            'hexapod.interface.input_mappings',
            'hexapod.interface.input_mappings.base_input_mapping',
            'hexapod.interface.input_mappings.dual_sense_usb_mapping',
            'hexapod.interface.input_mappings.dual_sense_bluetooth_mapping',
            'hexapod.interface.input_mappings',
            'hexapod.interface',
            'hexapod'
        }
        
        # Allow for some additional modules that might be loaded
        unexpected_modules = new_modules - expected_new_modules
        # Should not have loaded any major unexpected modules
        assert len(unexpected_modules) < 10  # Allow for some system modules
        
        # Check that environment wasn't modified
        assert dict(os.environ) == initial_env
