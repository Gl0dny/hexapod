"""
Unit tests for base input mapping.
"""
import pytest
from abc import ABC, abstractmethod
from unittest.mock import Mock

from hexapod.interface.input_mappings.base_input_mapping import InputMapping


class TestInputMapping:
    """Test cases for InputMapping abstract base class."""
    
    def test_input_mapping_is_abstract(self):
        """Test that InputMapping is an abstract base class."""
        assert issubclass(InputMapping, ABC)
        assert hasattr(InputMapping, '__abstractmethods__')
        assert len(InputMapping.__abstractmethods__) > 0
    
    def test_abstract_methods_exist(self):
        """Test that all required abstract methods are defined."""
        abstract_methods = InputMapping.__abstractmethods__
        
        expected_methods = {
            'get_axis_mappings',
            'get_button_mappings', 
            'get_hat_mappings',
            'get_interface_names',
            'get_axis_name',
            'get_button_name',
            'print_mappings_info'
        }
        
        assert expected_methods.issubset(abstract_methods)
    
    def test_cannot_instantiate_abstract_class(self):
        """Test that InputMapping cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            InputMapping()
    
    def test_concrete_implementation_required(self):
        """Test that concrete implementations must override all abstract methods."""
        class IncompleteMapping(InputMapping):
            def get_axis_mappings(self):
                return {}
            
            def get_button_mappings(self):
                return {}
            
            def get_hat_mappings(self):
                return {}
            
            def get_interface_names(self):
                return []
            
            def get_axis_name(self, axis_index: int):
                return f"axis_{axis_index}"
            
            def get_button_name(self, button_index: int):
                return f"button_{button_index}"
            
            # Missing print_mappings_info method
        
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteMapping()
    
    def test_complete_implementation_works(self):
        """Test that a complete implementation can be instantiated."""
        class CompleteMapping(InputMapping):
            def get_axis_mappings(self):
                return {"test_axis": 0}
            
            def get_button_mappings(self):
                return {"test_button": 0}
            
            def get_hat_mappings(self):
                return {"test_hat": "hat"}
            
            def get_interface_names(self):
                return ["test_interface"]
            
            def get_axis_name(self, axis_index: int):
                return f"axis_{axis_index}"
            
            def get_button_name(self, button_index: int):
                return f"button_{button_index}"
            
            def print_mappings_info(self):
                print("Test mapping info")
        
        # Should be able to instantiate
        mapping = CompleteMapping()
        assert mapping is not None
        
        # Test method calls
        assert mapping.get_axis_mappings() == {"test_axis": 0}
        assert mapping.get_button_mappings() == {"test_button": 0}
        assert mapping.get_hat_mappings() == {"test_hat": "hat"}
        assert mapping.get_interface_names() == ["test_interface"]
        assert mapping.get_axis_name(0) == "axis_0"
        assert mapping.get_button_name(0) == "button_0"
    
    def test_abstract_method_signatures(self):
        """Test that abstract methods have correct signatures."""
        # Check get_axis_mappings signature
        axis_method = InputMapping.get_axis_mappings
        assert axis_method.__annotations__['return'] == 'Dict[str, Any]'
        
        # Check get_button_mappings signature
        button_method = InputMapping.get_button_mappings
        assert button_method.__annotations__['return'] == 'Dict[str, Any]'
        
        # Check get_hat_mappings signature
        hat_method = InputMapping.get_hat_mappings
        assert hat_method.__annotations__['return'] == 'Dict[str, Any]'
        
        # Check get_interface_names signature
        interface_method = InputMapping.get_interface_names
        assert interface_method.__annotations__['return'] == 'List[str]'
        
        # Check get_axis_name signature
        axis_name_method = InputMapping.get_axis_name
        assert axis_name_method.__annotations__['axis_index'] == 'int'
        assert axis_name_method.__annotations__['return'] == 'str'
        
        # Check get_button_name signature
        button_name_method = InputMapping.get_button_name
        assert button_name_method.__annotations__['button_index'] == 'int'
        assert button_name_method.__annotations__['return'] == 'str'
        
        # Check print_mappings_info signature
        print_method = InputMapping.print_mappings_info
        assert print_method.__annotations__['return'] == 'None'
    
    def test_method_docstrings_exist(self):
        """Test that all abstract methods have docstrings."""
        methods = [
            'get_axis_mappings',
            'get_button_mappings',
            'get_hat_mappings', 
            'get_interface_names',
            'get_axis_name',
            'get_button_name',
            'print_mappings_info'
        ]
        
        for method_name in methods:
            method = getattr(InputMapping, method_name)
            assert method.__doc__ is not None
            assert len(method.__doc__.strip()) > 0
    
    def test_abstract_methods_are_abstract(self):
        """Test that all abstract methods are marked as abstract."""
        for method_name in InputMapping.__abstractmethods__:
            method = getattr(InputMapping, method_name)
            assert getattr(method, '__isabstractmethod__', False)
    
    def test_class_inheritance_chain(self):
        """Test the inheritance chain of InputMapping."""
        assert InputMapping.__bases__ == (ABC,)
        assert InputMapping.__mro__[0] == InputMapping
        assert ABC in InputMapping.__mro__
    
    def test_module_imports(self):
        """Test that the module imports correctly."""
        from hexapod.interface.input_mappings.base_input_mapping import InputMapping
        assert InputMapping is not None
        assert callable(InputMapping)
    
    def test_typing_imports(self):
        """Test that TYPE_CHECKING imports work correctly."""
        # This test ensures the TYPE_CHECKING block works
        # The actual types are only available during type checking
        import hexapod.interface.input_mappings.base_input_mapping as module
        assert hasattr(module, 'TYPE_CHECKING')
        assert module.TYPE_CHECKING is True or module.TYPE_CHECKING is False
