"""
Unit tests for DualSense Bluetooth input mapping.
"""
import pytest
from unittest.mock import patch, call
from io import StringIO

from hexapod.interface.input_mappings.dual_sense_bluetooth_mapping import DualSenseBluetoothMapping


class TestDualSenseBluetoothMapping:
    """Test cases for DualSenseBluetoothMapping class."""
    
    def test_inheritance(self):
        """Test that DualSenseBluetoothMapping inherits from InputMapping."""
        from hexapod.interface.input_mappings.base_input_mapping import InputMapping
        assert issubclass(DualSenseBluetoothMapping, InputMapping)
    
    def test_can_instantiate(self):
        """Test that DualSenseBluetoothMapping can be instantiated."""
        mapping = DualSenseBluetoothMapping()
        assert mapping is not None
        assert isinstance(mapping, DualSenseBluetoothMapping)
    
    def test_axis_constants(self):
        """Test that axis constants are defined correctly."""
        mapping = DualSenseBluetoothMapping()
        
        # Test axis constants
        assert mapping.AXIS_LEFT_X == 0
        assert mapping.AXIS_LEFT_Y == 1
        assert mapping.AXIS_RIGHT_X == 2
        assert mapping.AXIS_L2 == 3
        assert mapping.AXIS_R2 == 4
        assert mapping.AXIS_RIGHT_Y == 5
    
    def test_button_constants(self):
        """Test that button constants are defined correctly."""
        mapping = DualSenseBluetoothMapping()
        
        # Test button constants
        assert mapping.BUTTON_SQUARE == 0
        assert mapping.BUTTON_X == 1
        assert mapping.BUTTON_CIRCLE == 2
        assert mapping.BUTTON_TRIANGLE == 3
        assert mapping.BUTTON_L1 == 4
        assert mapping.BUTTON_R1 == 5
        assert mapping.BUTTON_L2 == 6
        assert mapping.BUTTON_R2 == 7
        assert mapping.BUTTON_CREATE == 8
        assert mapping.BUTTON_OPTIONS == 9
        assert mapping.BUTTON_L3 == 10
        assert mapping.BUTTON_R3 == 11
        assert mapping.BUTTON_PS5 == 12
        assert mapping.BUTTON_TOUCHPAD == 13
    
    def test_get_axis_mappings(self):
        """Test get_axis_mappings method."""
        mapping = DualSenseBluetoothMapping()
        axis_mappings = mapping.get_axis_mappings()
        
        expected_mappings = {
            "left_x": 0,
            "left_y": 1,
            "right_x": 2,
            "l2": 3,
            "r2": 4,
            "right_y": 5,
        }
        
        assert axis_mappings == expected_mappings
        assert isinstance(axis_mappings, dict)
        assert len(axis_mappings) == 6
    
    def test_get_button_mappings(self):
        """Test get_button_mappings method."""
        mapping = DualSenseBluetoothMapping()
        button_mappings = mapping.get_button_mappings()
        
        expected_mappings = {
            "square": 0,
            "x": 1,
            "circle": 2,
            "triangle": 3,
            "l1": 4,
            "r1": 5,
            "create": 8,
            "options": 9,
            "l3": 10,
            "r3": 11,
            "ps5": 12,
            "touchpad": 13,
        }
        
        assert button_mappings == expected_mappings
        assert isinstance(button_mappings, dict)
        assert len(button_mappings) == 12
    
    def test_get_hat_mappings(self):
        """Test get_hat_mappings method."""
        mapping = DualSenseBluetoothMapping()
        hat_mappings = mapping.get_hat_mappings()
        
        expected_mappings = {"dpad": "hat"}
        
        assert hat_mappings == expected_mappings
        assert isinstance(hat_mappings, dict)
        assert len(hat_mappings) == 1
    
    def test_get_interface_names(self):
        """Test get_interface_names method."""
        mapping = DualSenseBluetoothMapping()
        interface_names = mapping.get_interface_names()
        
        expected_names = ["dualsense wireless controller", "wireless controller", "bluetooth"]
        
        assert interface_names == expected_names
        assert isinstance(interface_names, list)
        assert len(interface_names) == 3
    
    def test_get_axis_name_valid_indices(self):
        """Test get_axis_name method with valid indices."""
        mapping = DualSenseBluetoothMapping()
        
        # Test all valid axis indices
        assert mapping.get_axis_name(0) == "Left X"
        assert mapping.get_axis_name(1) == "Left Y (inverted)"
        assert mapping.get_axis_name(2) == "Right X"
        assert mapping.get_axis_name(3) == "L2 (analog)"
        assert mapping.get_axis_name(4) == "R2 (analog)"
        assert mapping.get_axis_name(5) == "Right Y (inverted)"
    
    def test_get_axis_name_invalid_indices(self):
        """Test get_axis_name method with invalid indices."""
        mapping = DualSenseBluetoothMapping()
        
        # Test invalid axis indices
        assert mapping.get_axis_name(-1) == "Unknown Axis -1"
        assert mapping.get_axis_name(6) == "Unknown Axis 6"
        assert mapping.get_axis_name(100) == "Unknown Axis 100"
    
    def test_get_button_name_valid_indices(self):
        """Test get_button_name method with valid indices."""
        mapping = DualSenseBluetoothMapping()
        
        # Test all valid button indices
        assert mapping.get_button_name(0) == "Square"
        assert mapping.get_button_name(1) == "X"
        assert mapping.get_button_name(2) == "Circle"
        assert mapping.get_button_name(3) == "Triangle"
        assert mapping.get_button_name(4) == "L1"
        assert mapping.get_button_name(5) == "R1"
        assert mapping.get_button_name(8) == "Create"
        assert mapping.get_button_name(9) == "Options"
        assert mapping.get_button_name(10) == "L3"
        assert mapping.get_button_name(11) == "R3"
        assert mapping.get_button_name(12) == "PS5"
        assert mapping.get_button_name(13) == "Touchpad"
    
    def test_get_button_name_invalid_indices(self):
        """Test get_button_name method with invalid indices."""
        mapping = DualSenseBluetoothMapping()
        
        # Test invalid button indices
        assert mapping.get_button_name(-1) == "Unknown Button -1"
        assert mapping.get_button_name(6) == "Unknown Button 6"
        assert mapping.get_button_name(7) == "Unknown Button 7"
        assert mapping.get_button_name(14) == "Unknown Button 14"
        assert mapping.get_button_name(100) == "Unknown Button 100"
    
    def test_print_mappings_info(self):
        """Test print_mappings_info method."""
        mapping = DualSenseBluetoothMapping()
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            mapping.print_mappings_info()
            output = mock_stdout.getvalue()
        
        # Check that the output contains expected sections
        assert "PS5 DualSense Controller Mappings (Bluetooth):" in output
        assert "Axes:" in output
        assert "Buttons:" in output
        assert "Hats:" in output
        assert "=" * 40 in output
        
        # Check specific axis entries
        assert "[0] Left X" in output
        assert "[1] Left Y (inverted)" in output
        assert "[2] Right X" in output
        assert "[3] L2 (analog)" in output
        assert "[4] R2 (analog)" in output
        assert "[5] Right Y (inverted)" in output
        
        # Check specific button entries
        assert "[0] Square" in output
        assert "[1] X" in output
        assert "[2] Circle" in output
        assert "[3] Triangle" in output
        assert "[4] L1" in output
        assert "[5] R1" in output
        assert "[8] Create" in output
        assert "[9] Options" in output
        assert "[10] L3" in output
        assert "[11] R3" in output
        assert "[12] PS5" in output
        assert "[13] Touchpad" in output
        
        # Check hat entry
        assert "[0] D-pad (actual hat)" in output
    
    def test_print_mappings_info_formatting(self):
        """Test that print_mappings_info has proper formatting."""
        mapping = DualSenseBluetoothMapping()
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            mapping.print_mappings_info()
            output = mock_stdout.getvalue()
        
        lines = output.strip().split('\n')
        
        # Check that we have the expected number of lines
        assert len(lines) >= 20  # Should have header, axes, buttons, hats sections
        
        # Check that each line has proper formatting
        for line in lines:
            if line.startswith('[') and ']' in line:
                # Should be formatted as [index] name
                assert line.count('[') == 1
                assert line.count(']') == 1
                assert line.index('[') < line.index(']')
    
    def test_axis_mappings_consistency(self):
        """Test that axis mappings are consistent with constants."""
        mapping = DualSenseBluetoothMapping()
        axis_mappings = mapping.get_axis_mappings()
        
        # Check that all axis constants are represented in mappings
        assert axis_mappings["left_x"] == mapping.AXIS_LEFT_X
        assert axis_mappings["left_y"] == mapping.AXIS_LEFT_Y
        assert axis_mappings["right_x"] == mapping.AXIS_RIGHT_X
        assert axis_mappings["l2"] == mapping.AXIS_L2
        assert axis_mappings["r2"] == mapping.AXIS_R2
        assert axis_mappings["right_y"] == mapping.AXIS_RIGHT_Y
    
    def test_button_mappings_consistency(self):
        """Test that button mappings are consistent with constants."""
        mapping = DualSenseBluetoothMapping()
        button_mappings = mapping.get_button_mappings()
        
        # Check that all button constants are represented in mappings
        assert button_mappings["square"] == mapping.BUTTON_SQUARE
        assert button_mappings["x"] == mapping.BUTTON_X
        assert button_mappings["circle"] == mapping.BUTTON_CIRCLE
        assert button_mappings["triangle"] == mapping.BUTTON_TRIANGLE
        assert button_mappings["l1"] == mapping.BUTTON_L1
        assert button_mappings["r1"] == mapping.BUTTON_R1
        assert button_mappings["create"] == mapping.BUTTON_CREATE
        assert button_mappings["options"] == mapping.BUTTON_OPTIONS
        assert button_mappings["l3"] == mapping.BUTTON_L3
        assert button_mappings["r3"] == mapping.BUTTON_R3
        assert button_mappings["ps5"] == mapping.BUTTON_PS5
        assert button_mappings["touchpad"] == mapping.BUTTON_TOUCHPAD
    
    def test_axis_name_consistency(self):
        """Test that axis names are consistent with mappings."""
        mapping = DualSenseBluetoothMapping()
        
        # Test that axis names match the mappings
        for name, index in mapping.get_axis_mappings().items():
            axis_name = mapping.get_axis_name(index)
            assert axis_name != f"Unknown Axis {index}"
            assert isinstance(axis_name, str)
            assert len(axis_name) > 0
    
    def test_button_name_consistency(self):
        """Test that button names are consistent with mappings."""
        mapping = DualSenseBluetoothMapping()
        
        # Test that button names match the mappings
        for name, index in mapping.get_button_mappings().items():
            button_name = mapping.get_button_name(index)
            assert button_name != f"Unknown Button {index}"
            assert isinstance(button_name, str)
            assert len(button_name) > 0
    
    def test_interface_names_format(self):
        """Test that interface names are properly formatted."""
        mapping = DualSenseBluetoothMapping()
        interface_names = mapping.get_interface_names()
        
        for name in interface_names:
            assert isinstance(name, str)
            assert len(name) > 0
            assert name.lower() in name  # Should contain lowercase text
    
    def test_hat_mappings_format(self):
        """Test that hat mappings are properly formatted."""
        mapping = DualSenseBluetoothMapping()
        hat_mappings = mapping.get_hat_mappings()
        
        assert isinstance(hat_mappings, dict)
        assert "dpad" in hat_mappings
        assert hat_mappings["dpad"] == "hat"
    
    def test_class_docstring(self):
        """Test that the class has a proper docstring."""
        assert DualSenseBluetoothMapping.__doc__ is not None
        assert "PS5 DualSense Controller" in DualSenseBluetoothMapping.__doc__
        assert "Bluetooth" in DualSenseBluetoothMapping.__doc__
    
    def test_method_docstrings(self):
        """Test that all methods have docstrings."""
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
            method = getattr(DualSenseBluetoothMapping, method_name)
            assert method.__doc__ is not None
            assert len(method.__doc__.strip()) > 0
    
    def test_axis_index_uniqueness(self):
        """Test that all axis indices are unique."""
        mapping = DualSenseBluetoothMapping()
        axis_mappings = mapping.get_axis_mappings()
        
        indices = list(axis_mappings.values())
        assert len(indices) == len(set(indices))  # All indices should be unique
    
    def test_button_index_uniqueness(self):
        """Test that all button indices are unique."""
        mapping = DualSenseBluetoothMapping()
        button_mappings = mapping.get_button_mappings()
        
        indices = list(button_mappings.values())
        assert len(indices) == len(set(indices))  # All indices should be unique
