"""
Unit tests for joint control system.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from hexapod.robot.joint import Joint


class TestJoint:
    """Test cases for Joint class."""

    @pytest.fixture
    def mock_controller(self):
        """Create a mock MaestroUART controller."""
        controller = Mock()
        controller.set_target = Mock()
        return controller

    @pytest.fixture
    def joint_default(self, mock_controller):
        """Create a Joint instance with default parameters."""
        return Joint(
            controller=mock_controller,
            length=10.0,
            channel=0,
            angle_min=-90.0,
            angle_max=90.0,
        )

    @pytest.fixture
    def joint_custom(self, mock_controller):
        """Create a Joint instance with custom parameters."""
        return Joint(
            controller=mock_controller,
            length=15.0,
            channel=5,
            angle_min=-120.0,
            angle_max=120.0,
            servo_min=1000,
            servo_max=2000,
            angle_limit_min=-100.0,
            angle_limit_max=100.0,
            invert=True,
        )

    def test_init_default_parameters(self, joint_default):
        """Test Joint initialization with default parameters."""
        assert joint_default.controller is not None
        assert joint_default.length == 10.0
        assert joint_default.channel == 0
        assert joint_default.angle_min == -90.0
        assert joint_default.angle_max == 90.0
        assert (
            joint_default.servo_min
            == Joint.SERVO_INPUT_MIN * Joint.SERVO_UNIT_MULTIPLIER
        )
        assert (
            joint_default.servo_max
            == Joint.SERVO_INPUT_MAX * Joint.SERVO_UNIT_MULTIPLIER
        )
        assert joint_default.angle_limit_min is None
        assert joint_default.angle_limit_max is None
        assert joint_default.invert is False

    def test_init_custom_parameters(self, joint_custom):
        """Test Joint initialization with custom parameters."""
        assert joint_custom.controller is not None
        assert joint_custom.length == 15.0
        assert joint_custom.channel == 5
        assert joint_custom.angle_min == -120.0
        assert joint_custom.angle_max == 120.0
        assert joint_custom.servo_min == 1000
        assert joint_custom.servo_max == 2000
        assert joint_custom.angle_limit_min == -100.0
        assert joint_custom.angle_limit_max == 100.0
        assert joint_custom.invert is True

    def test_constants(self):
        """Test Joint class constants."""
        assert Joint.DEFAULT_SPEED == 32
        assert Joint.DEFAULT_ACCEL == 5
        assert Joint.SERVO_INPUT_MIN == 992
        assert Joint.SERVO_INPUT_MAX == 2000
        assert Joint.SERVO_UNIT_MULTIPLIER == 4

    def test_set_angle_valid_default_limits(self, joint_default):
        """Test setting valid joint angle with default limits."""
        joint_default.set_angle(45.0)

        # Verify controller.set_target was called
        joint_default.controller.set_target.assert_called_once()
        call_args = joint_default.controller.set_target.call_args[0]
        assert call_args[0] == 0  # channel
        assert isinstance(call_args[1], int)  # target value

    def test_set_angle_valid_custom_limits(self, joint_custom):
        """Test setting valid joint angle with custom limits."""
        joint_custom.set_angle(50.0)

        # Verify controller.set_target was called
        joint_custom.controller.set_target.assert_called_once()
        call_args = joint_custom.controller.set_target.call_args[0]
        assert call_args[0] == 5  # channel
        assert isinstance(call_args[1], int)  # target value

    def test_set_angle_inverted(self, joint_custom):
        """Test setting angle with inversion enabled."""
        joint_custom.set_angle(30.0)

        # Verify controller.set_target was called
        joint_custom.controller.set_target.assert_called_once()
        call_args = joint_custom.controller.set_target.call_args[0]
        assert call_args[0] == 5  # channel
        assert isinstance(call_args[1], int)  # target value

    def test_set_angle_below_minimum(self, joint_default):
        """Test setting angle below minimum limit."""
        with pytest.raises(ValueError, match="angle -95.0° is out of bounds"):
            joint_default.set_angle(-95.0)

    def test_set_angle_above_maximum(self, joint_default):
        """Test setting angle above maximum limit."""
        with pytest.raises(ValueError, match="angle 95.0° is out of bounds"):
            joint_default.set_angle(95.0)

    def test_set_angle_below_custom_limit(self, joint_custom):
        """Test setting angle below custom limit."""
        with pytest.raises(ValueError, match="angle 110.0° is above custom limit"):
            joint_custom.set_angle(-110.0)  # Gets inverted to +110.0

    def test_set_angle_above_custom_limit(self, joint_custom):
        """Test setting angle above custom limit."""
        with pytest.raises(ValueError, match="angle -110.0° is below custom limit"):
            joint_custom.set_angle(110.0)  # Gets inverted to -110.0

    def test_set_angle_skip_custom_limits(self, joint_custom):
        """Test setting angle with custom limits disabled."""
        # This should work even though it's outside custom limits
        joint_custom.set_angle(110.0, check_custom_limits=False)
        joint_custom.controller.set_target.assert_called_once()

    def test_angle_to_servo_target_minimum(self, joint_default):
        """Test angle to servo target conversion at minimum angle."""
        target = joint_default.angle_to_servo_target(-90.0)
        assert target == joint_default.servo_min

    def test_angle_to_servo_target_maximum(self, joint_default):
        """Test angle to servo target conversion at maximum angle."""
        target = joint_default.angle_to_servo_target(90.0)
        assert target == joint_default.servo_max

    def test_angle_to_servo_target_middle(self, joint_default):
        """Test angle to servo target conversion at middle angle."""
        target = joint_default.angle_to_servo_target(0.0)
        expected = (joint_default.servo_min + joint_default.servo_max) // 2
        assert target == expected

    def test_angle_to_servo_target_custom_limits(self, joint_custom):
        """Test angle to servo target conversion with custom servo limits."""
        target = joint_custom.angle_to_servo_target(-120.0)
        assert target == joint_custom.servo_min

        target = joint_custom.angle_to_servo_target(120.0)
        assert target == joint_custom.servo_max

    def test_angle_to_servo_target_float_input(self, joint_default):
        """Test angle to servo target conversion with float input."""
        target = joint_default.angle_to_servo_target(45.5)
        assert isinstance(target, int)
        assert joint_default.servo_min <= target <= joint_default.servo_max

    def test_update_calibration(self, joint_default):
        """Test updating servo calibration values."""
        new_servo_min = 1000
        new_servo_max = 2000

        joint_default.update_calibration(new_servo_min, new_servo_max)

        assert joint_default.servo_min == new_servo_min
        assert joint_default.servo_max == new_servo_max

    def test_validate_angle_within_limits(self, joint_default):
        """Test angle validation within limits."""
        # Should not raise any exception
        joint_default._validate_angle(0.0, True)
        joint_default._validate_angle(-90.0, True)
        joint_default._validate_angle(90.0, True)

    def test_validate_angle_outside_default_limits(self, joint_default):
        """Test angle validation outside default limits."""
        with pytest.raises(ValueError, match="angle -95.0° is out of bounds"):
            joint_default._validate_angle(-95.0, True)

        with pytest.raises(ValueError, match="angle 95.0° is out of bounds"):
            joint_default._validate_angle(95.0, True)

    def test_validate_angle_outside_custom_limits(self, joint_custom):
        """Test angle validation outside custom limits."""
        # Within default limits but outside custom limits
        with pytest.raises(ValueError, match="angle -110.0° is below custom limit"):
            joint_custom._validate_angle(-110.0, True)

        with pytest.raises(ValueError, match="angle 110.0° is above custom limit"):
            joint_custom._validate_angle(110.0, True)

    def test_validate_angle_skip_custom_limits(self, joint_custom):
        """Test angle validation with custom limits disabled."""
        # Should not raise exception even if outside custom limits
        joint_custom._validate_angle(-110.0, False)
        joint_custom._validate_angle(110.0, False)

    def test_validate_angle_no_custom_limits(self, joint_default):
        """Test angle validation when no custom limits are set."""
        # Should not raise exception when custom limits are None
        joint_default._validate_angle(0.0, True)

    def test_set_angle_logging(self, joint_default, caplog):
        """Test that set_angle logs appropriate messages."""
        with caplog.at_level("INFO"):
            joint_default.set_angle(45.0)

        assert "Setting angle to 45.0°" in caplog.text
        assert "Angle set to 45.0°" in caplog.text

    def test_set_angle_inverted_logging(self, joint_custom, caplog):
        """Test that set_angle logs inversion messages."""
        with caplog.at_level("DEBUG"):
            joint_custom.set_angle(30.0)

        assert "Invert: True" in caplog.text
        assert "Inverted angle: -30.0°" in caplog.text

    def test_angle_to_servo_target_logging(self, joint_default, caplog):
        """Test that angle_to_servo_target logs debug messages."""
        with caplog.at_level("DEBUG"):
            joint_default.angle_to_servo_target(45.0)

        assert "Mapping angle 45.0° to servo target" in caplog.text

    def test_validate_angle_logging(self, joint_default, caplog):
        """Test that _validate_angle logs debug messages."""
        with caplog.at_level("DEBUG"):
            joint_default._validate_angle(45.0, True)

        assert "Validating angle: 45.0°" in caplog.text
        assert "Check custom limits: True" in caplog.text

    def test_update_calibration_logging(self, joint_default, caplog):
        """Test that update_calibration logs debug messages."""
        with caplog.at_level("DEBUG"):
            joint_default.update_calibration(1000, 2000)

        assert "Updated calibration for channel 0" in caplog.text
        assert "servo_min=1000, servo_max=2000" in caplog.text

    def test_error_logging_angle_out_of_bounds(self, joint_default, caplog):
        """Test error logging for angle out of bounds."""
        with caplog.at_level("ERROR"):
            with pytest.raises(ValueError):
                joint_default.set_angle(95.0)

        assert "angle 95.0° is out of bounds" in caplog.text

    def test_error_logging_angle_below_custom_limit(self, joint_custom, caplog):
        """Test error logging for angle below custom limit."""
        with caplog.at_level("ERROR"):
            with pytest.raises(ValueError):
                joint_custom.set_angle(-110.0)  # Gets inverted to +110.0

        assert "angle 110.0° is above custom limit" in caplog.text

    def test_error_logging_angle_above_custom_limit(self, joint_custom, caplog):
        """Test error logging for angle above custom limit."""
        with caplog.at_level("ERROR"):
            with pytest.raises(ValueError):
                joint_custom.set_angle(110.0)  # Gets inverted to -110.0

        assert "angle -110.0° is below custom limit" in caplog.text

    def test_controller_communication_error(self, joint_default):
        """Test error handling for controller communication failures."""
        # Mock controller to raise an exception
        joint_default.controller.set_target.side_effect = Exception(
            "Communication error"
        )

        with pytest.raises(Exception, match="Communication error"):
            joint_default.set_angle(45.0)

    def test_edge_case_angle_min_boundary(self, joint_default):
        """Test angle at minimum boundary."""
        joint_default.set_angle(-90.0)
        joint_default.controller.set_target.assert_called_once()

    def test_edge_case_angle_max_boundary(self, joint_default):
        """Test angle at maximum boundary."""
        joint_default.set_angle(90.0)
        joint_default.controller.set_target.assert_called_once()

    def test_edge_case_angle_zero(self, joint_default):
        """Test angle at zero."""
        joint_default.set_angle(0.0)
        joint_default.controller.set_target.assert_called_once()

    def test_edge_case_custom_limit_min_boundary(self, joint_custom):
        """Test angle at custom limit minimum boundary."""
        joint_custom.set_angle(-100.0)
        joint_custom.controller.set_target.assert_called_once()

    def test_edge_case_custom_limit_max_boundary(self, joint_custom):
        """Test angle at custom limit maximum boundary."""
        joint_custom.set_angle(100.0)
        joint_custom.controller.set_target.assert_called_once()

    def test_angle_to_servo_target_precision(self, joint_default):
        """Test angle to servo target conversion precision."""
        # Test with larger increments to ensure different values
        target1 = joint_default.angle_to_servo_target(0.0)
        target2 = joint_default.angle_to_servo_target(1.0)

        # Should be different values
        assert target1 != target2
        assert abs(target1 - target2) > 0

    def test_servo_target_range_validation(self, joint_default):
        """Test that servo targets are within expected range."""
        # Test various angles
        for angle in [-90, -45, 0, 45, 90]:
            target = joint_default.angle_to_servo_target(angle)
            assert joint_default.servo_min <= target <= joint_default.servo_max

    def test_invert_angle_calculation(self, joint_custom):
        """Test that inversion correctly negates the angle."""
        # Test that inverted angle is properly calculated
        original_angle = 30.0
        joint_custom.set_angle(original_angle)

        # The internal calculation should use -30.0
        # We can verify this by checking the logging or by testing the mapping
        target = joint_custom.angle_to_servo_target(-original_angle)
        call_args = joint_custom.controller.set_target.call_args[0]
        assert call_args[1] == target

    def test_joint_string_representation(self, joint_default):
        """Test Joint string representation in error messages."""
        # This tests the __str__ method indirectly through error messages
        with pytest.raises(ValueError) as exc_info:
            joint_default.set_angle(95.0)

        # The error message should contain the joint representation
        assert str(joint_default) in str(exc_info.value)

    def test_angle_validation_debug_logging(self, joint_default, caplog):
        """Test debug logging in angle validation."""
        with caplog.at_level("DEBUG"):
            joint_default._validate_angle(45.0, True)

        assert "Validating angle: 45.0°" in caplog.text
        assert "Check custom limits: True" in caplog.text
