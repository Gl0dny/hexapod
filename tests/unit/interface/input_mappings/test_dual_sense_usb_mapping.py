"""
Unit tests for DualSense USB input mapping.
"""

import pytest
from unittest.mock import patch, call
from io import StringIO

from hexapod.interface.input_mappings.dual_sense_usb_mapping import DualSenseUSBMapping


class TestDualSenseUSBMapping:
    """Test cases for DualSenseUSBMapping class."""

    def test_inheritance(self):
        """Test that DualSenseUSBMapping inherits from InputMapping."""
        from hexapod.interface.input_mappings.base_input_mapping import InputMapping

        assert issubclass(DualSenseUSBMapping, InputMapping)

    def test_can_instantiate(self):
        """Test that DualSenseUSBMapping can be instantiated."""
        mapping = DualSenseUSBMapping()
        assert mapping is not None
        assert isinstance(mapping, DualSenseUSBMapping)

    def test_axis_constants(self):
        """Test that axis constants are defined correctly."""
        mapping = DualSenseUSBMapping()

        # Test axis constants
        assert mapping.AXIS_LEFT_X == 0
        assert mapping.AXIS_LEFT_Y == 1
        assert mapping.AXIS_RIGHT_X == 2
        assert mapping.AXIS_RIGHT_Y == 3
        assert mapping.AXIS_L2 == 4
        assert mapping.AXIS_R2 == 5

    def test_button_constants(self):
        """Test that button constants are defined correctly."""
        mapping = DualSenseUSBMapping()

        # Test main button constants
        assert mapping.BUTTON_X == 0
        assert mapping.BUTTON_CIRCLE == 1
        assert mapping.BUTTON_SQUARE == 2
        assert mapping.BUTTON_TRIANGLE == 3
        assert mapping.BUTTON_CREATE == 4
        assert mapping.BUTTON_PS5 == 5
        assert mapping.BUTTON_OPTIONS == 6
        assert mapping.BUTTON_L3 == 7
        assert mapping.BUTTON_R3 == 8
        assert mapping.BUTTON_L1 == 9
        assert mapping.BUTTON_R1 == 10
        assert mapping.BUTTON_MUTE == 15
        assert mapping.BUTTON_TOUCHPAD == 16

        # Test D-pad button constants
        assert mapping.BUTTON_DPAD_UP == 11
        assert mapping.BUTTON_DPAD_DOWN == 12
        assert mapping.BUTTON_DPAD_LEFT == 13
        assert mapping.BUTTON_DPAD_RIGHT == 14

    def test_get_axis_mappings(self):
        """Test get_axis_mappings method."""
        mapping = DualSenseUSBMapping()
        axis_mappings = mapping.get_axis_mappings()

        expected_mappings = {
            "left_x": 0,
            "left_y": 1,
            "right_x": 2,
            "right_y": 3,
            "l2": 4,
            "r2": 5,
        }

        assert axis_mappings == expected_mappings
        assert isinstance(axis_mappings, dict)
        assert len(axis_mappings) == 6

    def test_get_button_mappings(self):
        """Test get_button_mappings method."""
        mapping = DualSenseUSBMapping()
        button_mappings = mapping.get_button_mappings()

        expected_mappings = {
            "square": 2,
            "x": 0,
            "circle": 1,
            "triangle": 3,
            "l1": 9,
            "r1": 10,
            "create": 4,
            "options": 6,
            "l3": 7,
            "r3": 8,
            "ps5": 5,
            "touchpad": 16,
            "mute": 15,
            "dpad_up": 11,
            "dpad_down": 12,
            "dpad_left": 13,
            "dpad_right": 14,
        }

        assert button_mappings == expected_mappings
        assert isinstance(button_mappings, dict)
        assert len(button_mappings) == 17

    def test_get_hat_mappings(self):
        """Test get_hat_mappings method."""
        mapping = DualSenseUSBMapping()
        hat_mappings = mapping.get_hat_mappings()

        expected_mappings = {"dpad": "buttons"}

        assert hat_mappings == expected_mappings
        assert isinstance(hat_mappings, dict)
        assert len(hat_mappings) == 1

    def test_get_interface_names(self):
        """Test get_interface_names method."""
        mapping = DualSenseUSBMapping()
        interface_names = mapping.get_interface_names()

        expected_names = ["dualsense", "ps5", "playstation 5"]

        assert interface_names == expected_names
        assert isinstance(interface_names, list)
        assert len(interface_names) == 3

    def test_get_axis_name_valid_indices(self):
        """Test get_axis_name method with valid indices."""
        mapping = DualSenseUSBMapping()

        # Test all valid axis indices
        assert mapping.get_axis_name(0) == "Left X"
        assert mapping.get_axis_name(1) == "Left Y (inverted)"
        assert mapping.get_axis_name(2) == "Right X"
        assert mapping.get_axis_name(3) == "Right Y (inverted)"
        assert mapping.get_axis_name(4) == "L2 (analog)"
        assert mapping.get_axis_name(5) == "R2 (analog)"

    def test_get_axis_name_invalid_indices(self):
        """Test get_axis_name method with invalid indices."""
        mapping = DualSenseUSBMapping()

        # Test invalid axis indices
        assert mapping.get_axis_name(-1) == "Unknown Axis -1"
        assert mapping.get_axis_name(6) == "Unknown Axis 6"
        assert mapping.get_axis_name(100) == "Unknown Axis 100"

    def test_get_button_name_valid_indices(self):
        """Test get_button_name method with valid indices."""
        mapping = DualSenseUSBMapping()

        # Test all valid button indices
        assert mapping.get_button_name(0) == "X"
        assert mapping.get_button_name(1) == "Circle"
        assert mapping.get_button_name(2) == "Square"
        assert mapping.get_button_name(3) == "Triangle"
        assert mapping.get_button_name(4) == "Create"
        assert mapping.get_button_name(5) == "PS5"
        assert mapping.get_button_name(6) == "Options"
        assert mapping.get_button_name(7) == "L3"
        assert mapping.get_button_name(8) == "R3"
        assert mapping.get_button_name(9) == "L1"
        assert mapping.get_button_name(10) == "R1"
        assert mapping.get_button_name(11) == "D-pad Up"
        assert mapping.get_button_name(12) == "D-pad Down"
        assert mapping.get_button_name(13) == "D-pad Left"
        assert mapping.get_button_name(14) == "D-pad Right"
        assert mapping.get_button_name(15) == "Mute"
        assert mapping.get_button_name(16) == "Touchpad"

    def test_get_button_name_invalid_indices(self):
        """Test get_button_name method with invalid indices."""
        mapping = DualSenseUSBMapping()

        # Test invalid button indices
        assert mapping.get_button_name(-1) == "Unknown Button -1"
        assert mapping.get_button_name(17) == "Unknown Button 17"
        assert mapping.get_button_name(100) == "Unknown Button 100"

    def test_print_mappings_info(self):
        """Test print_mappings_info method."""
        mapping = DualSenseUSBMapping()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mapping.print_mappings_info()
            output = mock_stdout.getvalue()

        # Check that the output contains expected sections
        assert "PS5 DualSense Controller Mappings (USB):" in output
        assert "Axes:" in output
        assert "Buttons:" in output
        assert "Hats:" in output
        assert "=" * 40 in output

        # Check specific axis entries
        assert "[0] Left X" in output
        assert "[1] Left Y (inverted)" in output
        assert "[2] Right X" in output
        assert "[3] Right Y (inverted)" in output
        assert "[4] L2 (analog)" in output
        assert "[5] R2 (analog)" in output

        # Check specific button entries
        assert "[0] X" in output
        assert "[1] Circle" in output
        assert "[2] Square" in output
        assert "[3] Triangle" in output
        assert "[4] Create" in output
        assert "[5] PS5" in output
        assert "[6] Options" in output
        assert "[7] L3" in output
        assert "[8] R3" in output
        assert "[9] L1" in output
        assert "[10] R1" in output
        assert "[11] D-pad Up" in output
        assert "[12] D-pad Down" in output
        assert "[13] D-pad Left" in output
        assert "[14] D-pad Right" in output
        assert "[15] Mute" in output
        assert "[16] Touchpad" in output

        # Check hat entry
        assert "[dpad] D-pad (implemented as buttons)" in output

    def test_print_mappings_info_formatting(self):
        """Test that print_mappings_info has proper formatting."""
        mapping = DualSenseUSBMapping()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            mapping.print_mappings_info()
            output = mock_stdout.getvalue()

        lines = output.strip().split("\n")

        # Check that we have the expected number of lines
        assert len(lines) >= 25  # Should have header, axes, buttons, hats sections

        # Check that each line has proper formatting
        for line in lines:
            if line.startswith("[") and "]" in line:
                # Should be formatted as [index] name
                assert line.count("[") == 1
                assert line.count("]") == 1
                assert line.index("[") < line.index("]")

    def test_axis_mappings_consistency(self):
        """Test that axis mappings are consistent with constants."""
        mapping = DualSenseUSBMapping()
        axis_mappings = mapping.get_axis_mappings()

        # Check that all axis constants are represented in mappings
        assert axis_mappings["left_x"] == mapping.AXIS_LEFT_X
        assert axis_mappings["left_y"] == mapping.AXIS_LEFT_Y
        assert axis_mappings["right_x"] == mapping.AXIS_RIGHT_X
        assert axis_mappings["right_y"] == mapping.AXIS_RIGHT_Y
        assert axis_mappings["l2"] == mapping.AXIS_L2
        assert axis_mappings["r2"] == mapping.AXIS_R2

    def test_button_mappings_consistency(self):
        """Test that button mappings are consistent with constants."""
        mapping = DualSenseUSBMapping()
        button_mappings = mapping.get_button_mappings()

        # Check that all button constants are represented in mappings
        assert button_mappings["x"] == mapping.BUTTON_X
        assert button_mappings["circle"] == mapping.BUTTON_CIRCLE
        assert button_mappings["square"] == mapping.BUTTON_SQUARE
        assert button_mappings["triangle"] == mapping.BUTTON_TRIANGLE
        assert button_mappings["create"] == mapping.BUTTON_CREATE
        assert button_mappings["ps5"] == mapping.BUTTON_PS5
        assert button_mappings["options"] == mapping.BUTTON_OPTIONS
        assert button_mappings["l3"] == mapping.BUTTON_L3
        assert button_mappings["r3"] == mapping.BUTTON_R3
        assert button_mappings["l1"] == mapping.BUTTON_L1
        assert button_mappings["r1"] == mapping.BUTTON_R1
        assert button_mappings["mute"] == mapping.BUTTON_MUTE
        assert button_mappings["touchpad"] == mapping.BUTTON_TOUCHPAD
        assert button_mappings["dpad_up"] == mapping.BUTTON_DPAD_UP
        assert button_mappings["dpad_down"] == mapping.BUTTON_DPAD_DOWN
        assert button_mappings["dpad_left"] == mapping.BUTTON_DPAD_LEFT
        assert button_mappings["dpad_right"] == mapping.BUTTON_DPAD_RIGHT

    def test_axis_name_consistency(self):
        """Test that axis names are consistent with mappings."""
        mapping = DualSenseUSBMapping()

        # Test that axis names match the mappings
        for name, index in mapping.get_axis_mappings().items():
            axis_name = mapping.get_axis_name(index)
            assert axis_name != f"Unknown Axis {index}"
            assert isinstance(axis_name, str)
            assert len(axis_name) > 0

    def test_button_name_consistency(self):
        """Test that button names are consistent with mappings."""
        mapping = DualSenseUSBMapping()

        # Test that button names match the mappings
        for name, index in mapping.get_button_mappings().items():
            button_name = mapping.get_button_name(index)
            assert button_name != f"Unknown Button {index}"
            assert isinstance(button_name, str)
            assert len(button_name) > 0

    def test_interface_names_format(self):
        """Test that interface names are properly formatted."""
        mapping = DualSenseUSBMapping()
        interface_names = mapping.get_interface_names()

        for name in interface_names:
            assert isinstance(name, str)
            assert len(name) > 0
            assert name.lower() in name  # Should contain lowercase text

    def test_hat_mappings_format(self):
        """Test that hat mappings are properly formatted."""
        mapping = DualSenseUSBMapping()
        hat_mappings = mapping.get_hat_mappings()

        assert isinstance(hat_mappings, dict)
        assert "dpad" in hat_mappings
        assert hat_mappings["dpad"] == "buttons"

    def test_class_docstring(self):
        """Test that the class has a proper docstring."""
        assert DualSenseUSBMapping.__doc__ is not None
        assert "PS5 DualSense Controller" in DualSenseUSBMapping.__doc__
        assert "USB" in DualSenseUSBMapping.__doc__

    def test_method_docstrings(self):
        """Test that all methods have docstrings."""
        methods = [
            "get_axis_mappings",
            "get_button_mappings",
            "get_hat_mappings",
            "get_interface_names",
            "get_axis_name",
            "get_button_name",
            "print_mappings_info",
        ]

        for method_name in methods:
            method = getattr(DualSenseUSBMapping, method_name)
            assert method.__doc__ is not None
            assert len(method.__doc__.strip()) > 0

    def test_axis_index_uniqueness(self):
        """Test that all axis indices are unique."""
        mapping = DualSenseUSBMapping()
        axis_mappings = mapping.get_axis_mappings()

        indices = list(axis_mappings.values())
        assert len(indices) == len(set(indices))  # All indices should be unique

    def test_button_index_uniqueness(self):
        """Test that all button indices are unique."""
        mapping = DualSenseUSBMapping()
        button_mappings = mapping.get_button_mappings()

        indices = list(button_mappings.values())
        assert len(indices) == len(set(indices))  # All indices should be unique

    def test_dpad_buttons_included(self):
        """Test that D-pad buttons are included in button mappings."""
        mapping = DualSenseUSBMapping()
        button_mappings = mapping.get_button_mappings()

        # Check that D-pad buttons are included
        assert "dpad_up" in button_mappings
        assert "dpad_down" in button_mappings
        assert "dpad_left" in button_mappings
        assert "dpad_right" in button_mappings

        # Check that they have valid indices
        assert button_mappings["dpad_up"] == 11
        assert button_mappings["dpad_down"] == 12
        assert button_mappings["dpad_left"] == 13
        assert button_mappings["dpad_right"] == 14

    def test_mute_button_included(self):
        """Test that mute button is included in button mappings."""
        mapping = DualSenseUSBMapping()
        button_mappings = mapping.get_button_mappings()

        assert "mute" in button_mappings
        assert button_mappings["mute"] == 15

    def test_usb_specific_features(self):
        """Test USB-specific features that differ from Bluetooth."""
        mapping = DualSenseUSBMapping()

        # USB has different axis order (right_y before triggers)
        axis_mappings = mapping.get_axis_mappings()
        assert axis_mappings["right_y"] == 3
        assert axis_mappings["l2"] == 4
        assert axis_mappings["r2"] == 5

        # USB has D-pad as buttons, not hat
        hat_mappings = mapping.get_hat_mappings()
        assert hat_mappings["dpad"] == "buttons"

        # USB has different interface names
        interface_names = mapping.get_interface_names()
        assert "dualsense" in interface_names
        assert "ps5" in interface_names
        assert "playstation 5" in interface_names

    def test_button_order_differences(self):
        """Test that button order differs from Bluetooth mapping."""
        mapping = DualSenseUSBMapping()
        button_mappings = mapping.get_button_mappings()

        # USB has different button order
        assert button_mappings["x"] == 0  # First in USB
        assert button_mappings["circle"] == 1
        assert button_mappings["square"] == 2
        assert button_mappings["triangle"] == 3

        # L1/R1 are later in USB
        assert button_mappings["l1"] == 9
        assert button_mappings["r1"] == 10
