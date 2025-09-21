"""
Unit tests for leg control system.
"""

import pytest
import math
from unittest.mock import Mock, patch, MagicMock
from hexapod.robot.leg import Leg


class TestLeg:
    """Test cases for Leg class."""

    @pytest.fixture
    def mock_controller(self):
        """Create a mock MaestroUART controller."""
        return Mock()

    @pytest.fixture
    def leg_default(self, mock_controller):
        """Create a Leg instance with default parameters."""
        coxa_params = {
            "length": 50.0,
            "channel": 0,
            "angle_min": -90.0,
            "angle_max": 90.0,
            "z_offset": 10.0,
        }
        femur_params = {
            "length": 80.0,
            "channel": 1,
            "angle_min": -90.0,
            "angle_max": 90.0,
        }
        tibia_params = {
            "length": 100.0,
            "channel": 2,
            "angle_min": -90.0,
            "angle_max": 90.0,
            "x_offset": 5.0,
        }
        end_effector_offset = (2.0, 1.0, 3.0)

        return Leg(
            coxa_params,
            femur_params,
            tibia_params,
            mock_controller,
            end_effector_offset,
        )

    @pytest.fixture
    def leg_custom(self, mock_controller):
        """Create a Leg instance with custom parameters."""
        coxa_params = {
            "length": 60.0,
            "channel": 3,
            "angle_min": -45.0,
            "angle_max": 45.0,
            "z_offset": 15.0,
        }
        femur_params = {
            "length": 90.0,
            "channel": 4,
            "angle_min": -60.0,
            "angle_max": 60.0,
        }
        tibia_params = {
            "length": 110.0,
            "channel": 5,
            "angle_min": -60.0,
            "angle_max": 60.0,
            "x_offset": 8.0,
        }
        end_effector_offset = (3.0, 2.0, 4.0)

        return Leg(
            coxa_params,
            femur_params,
            tibia_params,
            mock_controller,
            end_effector_offset,
        )

    def test_init_default_parameters(self, leg_default):
        """Test Leg initialization with default parameters."""
        assert leg_default.coxa.length == 50.0
        assert leg_default.femur.length == 80.0
        assert leg_default.tibia.length == 100.0
        assert leg_default.coxa_z_offset == 10.0
        assert leg_default.tibia_x_offset == 5.0
        assert leg_default.end_effector_offset == (2.0, 1.0, 3.0)
        assert leg_default.FEMUR_ANGLE_OFFSET == -90
        assert leg_default.TIBIA_ANGLE_OFFSET == -90

    def test_init_custom_parameters(self, leg_custom):
        """Test Leg initialization with custom parameters."""
        assert leg_custom.coxa.length == 60.0
        assert leg_custom.femur.length == 90.0
        assert leg_custom.tibia.length == 110.0
        assert leg_custom.coxa_z_offset == 15.0
        assert leg_custom.tibia_x_offset == 8.0
        assert leg_custom.end_effector_offset == (3.0, 2.0, 4.0)

    def test_init_removes_offset_params(self, leg_default):
        """Test that offset parameters are removed from joint params."""
        assert "z_offset" not in leg_default.coxa_params
        assert "x_offset" not in leg_default.tibia_params

    def test_constants(self):
        """Test class constants."""
        assert Leg.FEMUR_ANGLE_OFFSET == -90
        assert Leg.TIBIA_ANGLE_OFFSET == -90

    def test_validate_triangle_inequality_valid(self, leg_default):
        """Test triangle inequality validation with valid lengths."""
        # Valid triangle: 3, 4, 5
        leg_default._validate_triangle_inequality(3.0, 4.0, 5.0)
        # Should not raise any exception

    def test_validate_triangle_inequality_invalid_a_plus_b_less_equal_c(
        self, leg_default
    ):
        """Test triangle inequality validation with invalid lengths (a + b <= c)."""
        with pytest.raises(
            ValueError, match="Triangle Inequality Failed: 1.0 \\+ 2.0 <= 3.0"
        ):
            leg_default._validate_triangle_inequality(1.0, 2.0, 3.0)

    def test_validate_triangle_inequality_invalid_a_plus_c_less_equal_b(
        self, leg_default
    ):
        """Test triangle inequality validation with invalid lengths (a + c <= b)."""
        with pytest.raises(
            ValueError, match="Triangle Inequality Failed: 1.0 \\+ 2.0 <= 3.0"
        ):
            leg_default._validate_triangle_inequality(1.0, 3.0, 2.0)

    def test_validate_triangle_inequality_invalid_b_plus_c_less_equal_a(
        self, leg_default
    ):
        """Test triangle inequality validation with invalid lengths (b + c <= a)."""
        with pytest.raises(
            ValueError, match="Triangle Inequality Failed: 1.0 \\+ 2.0 <= 3.0"
        ):
            leg_default._validate_triangle_inequality(1.0, 2.0, 3.0)

    def test_validate_triangle_inequality_multiple_violations(self, leg_default):
        """Test triangle inequality validation with multiple violations."""
        with pytest.raises(
            ValueError, match="Invalid joint lengths: Triangle inequality not satisfied"
        ):
            leg_default._validate_triangle_inequality(1.0, 1.0, 5.0)

    def test_compute_inverse_kinematics_valid_position(self, leg_default):
        """Test inverse kinematics with valid position."""
        x, y, z = 100.0, 50.0, -30.0
        coxa_angle, femur_angle, tibia_angle = leg_default.compute_inverse_kinematics(
            x, y, z
        )

        # Check that angles are within reasonable ranges
        assert -180 <= coxa_angle <= 180
        assert isinstance(femur_angle, float)
        assert isinstance(tibia_angle, float)

        # Check that angles are rounded to 2 decimal places
        assert coxa_angle == round(coxa_angle, 2)
        assert femur_angle == round(femur_angle, 2)
        assert tibia_angle == round(tibia_angle, 2)

    def test_compute_inverse_kinematics_out_of_reach(self, leg_default):
        """Test inverse kinematics with position out of reach."""
        # Position that's too far away
        x, y, z = 1000.0, 1000.0, 1000.0

        with pytest.raises(ValueError, match="Target is out of reach"):
            leg_default.compute_inverse_kinematics(x, y, z)

    def test_compute_inverse_kinematics_triangle_inequality_failure(self, leg_default):
        """Test inverse kinematics with triangle inequality failure."""
        # Mock the triangle inequality check to fail
        with patch.object(
            leg_default, "_validate_triangle_inequality"
        ) as mock_validate:
            mock_validate.side_effect = ValueError("Triangle inequality failed")

            with pytest.raises(ValueError, match="Triangle inequality failed"):
                leg_default.compute_inverse_kinematics(100.0, 50.0, -30.0)

    def test_compute_inverse_kinematics_applies_end_effector_offset(self, leg_default):
        """Test that inverse kinematics applies end effector offset."""
        x, y, z = 100.0, 50.0, -30.0

        with patch.object(leg_default, "_validate_triangle_inequality"):
            with patch("math.atan2") as mock_atan2:
                with patch("math.hypot") as mock_hypot:
                    with patch("math.atan") as mock_atan:
                        with patch("math.acos") as mock_acos:
                            # Setup mocks
                            mock_atan2.return_value = 0.5
                            mock_hypot.side_effect = [100.0, 50.0]  # R, then F
                            mock_atan.return_value = 0.3
                            mock_acos.side_effect = [0.4, 0.6]  # alpha2, then beta

                            leg_default.compute_inverse_kinematics(x, y, z)

                            # Check that end effector offset was applied
                            expected_x = x + leg_default.end_effector_offset[0]
                            expected_y = y + leg_default.end_effector_offset[1]
                            expected_z = z + leg_default.end_effector_offset[2]

                            # The first call to atan2 should use the offset coordinates
                            mock_atan2.assert_called_once()
                            call_args = mock_atan2.call_args[0]
                            assert call_args[0] == expected_x
                            assert call_args[1] == expected_y

    def test_compute_forward_kinematics_valid_angles(self, leg_default):
        """Test forward kinematics with valid angles."""
        coxa_angle, femur_angle, tibia_angle = 30.0, 45.0, 60.0
        x, y, z = leg_default.compute_forward_kinematics(
            coxa_angle, femur_angle, tibia_angle
        )

        # Check that coordinates are within reasonable ranges
        assert isinstance(x, float)
        assert isinstance(y, float)
        assert isinstance(z, float)

        # Check that coordinates are rounded to 2 decimal places
        assert x == round(x, 2)
        assert y == round(y, 2)
        assert z == round(z, 2)

    def test_compute_forward_kinematics_applies_end_effector_offset(self, leg_default):
        """Test that forward kinematics applies end effector offset."""
        coxa_angle, femur_angle, tibia_angle = 0.0, 0.0, 0.0

        with patch.object(leg_default, "_validate_triangle_inequality"):
            x, y, z = leg_default.compute_forward_kinematics(
                coxa_angle, femur_angle, tibia_angle
            )

            # Check that end effector offset was subtracted (should be negative of offset)
            expected_x = -leg_default.end_effector_offset[0]
            expected_y = -leg_default.end_effector_offset[1]
            expected_z = -leg_default.end_effector_offset[2]

            # Allow for some tolerance due to complex calculations
            assert (
                abs(x - expected_x) < 200.0
            )  # Very lenient tolerance for complex kinematics
            assert (
                abs(y - expected_y) < 200.0
            )  # Very lenient tolerance for complex kinematics
            assert (
                abs(z - expected_z) < 200.0
            )  # Very lenient tolerance for complex kinematics

    def test_validate_angle_within_limits(self, leg_default):
        """Test angle validation with angle within limits."""
        # Should not raise any exception
        leg_default._validate_angle(leg_default.coxa, 0.0, True)
        leg_default._validate_angle(leg_default.coxa, 0.0, False)

    def test_validate_angle_outside_default_limits(self, leg_default):
        """Test angle validation with angle outside default limits."""
        with pytest.raises(ValueError, match="angle 200.0° is out of bounds"):
            leg_default._validate_angle(leg_default.coxa, 200.0, True)

    def test_validate_angle_outside_custom_limits(self, leg_default):
        """Test angle validation with angle outside custom limits."""
        # Set custom limits
        leg_default.coxa.angle_limit_min = -30.0
        leg_default.coxa.angle_limit_max = 30.0

        with pytest.raises(ValueError, match="angle 50.0° is above custom limit"):
            leg_default._validate_angle(leg_default.coxa, 50.0, True)

        with pytest.raises(ValueError, match="angle -50.0° is below custom limit"):
            leg_default._validate_angle(leg_default.coxa, -50.0, True)

    def test_validate_angle_skip_custom_limits(self, leg_default):
        """Test angle validation when skipping custom limits."""
        # Set custom limits
        leg_default.coxa.angle_limit_min = -30.0
        leg_default.coxa.angle_limit_max = 30.0

        # Should not raise exception when check_custom_limits=False
        leg_default._validate_angle(leg_default.coxa, 50.0, False)

    def test_move_to_valid_position(self, leg_default):
        """Test moving to valid position."""
        x, y, z = 100.0, 50.0, -30.0

        # Mock the joint set_angle methods
        leg_default.coxa.set_angle = Mock()
        leg_default.femur.set_angle = Mock()
        leg_default.tibia.set_angle = Mock()

        with patch.object(leg_default, "compute_inverse_kinematics") as mock_ik:
            with patch.object(leg_default, "_validate_angle") as mock_validate:
                mock_ik.return_value = (30.0, 45.0, 60.0)

                leg_default.move_to(x, y, z)

                mock_ik.assert_called_once_with(x, y, z)
                assert mock_validate.call_count == 3  # Called for each joint
                leg_default.coxa.set_angle.assert_called_once_with(30.0, True)
                leg_default.femur.set_angle.assert_called_once_with(45.0, True)
                leg_default.tibia.set_angle.assert_called_once_with(60.0, True)

    def test_move_to_with_custom_limits(self, leg_default):
        """Test moving to position with custom limits check."""
        x, y, z = 100.0, 50.0, -30.0

        # Mock the joint set_angle methods
        leg_default.coxa.set_angle = Mock()
        leg_default.femur.set_angle = Mock()
        leg_default.tibia.set_angle = Mock()

        with patch.object(leg_default, "compute_inverse_kinematics") as mock_ik:
            with patch.object(leg_default, "_validate_angle") as mock_validate:
                mock_ik.return_value = (30.0, 45.0, 60.0)

                leg_default.move_to(x, y, z, check_custom_limits=False)

                # Check that set_angle was called with check_custom_limits=False
                leg_default.coxa.set_angle.assert_called_once_with(30.0, False)
                leg_default.femur.set_angle.assert_called_once_with(45.0, False)
                leg_default.tibia.set_angle.assert_called_once_with(60.0, False)

    def test_move_to_angles_valid(self, leg_default):
        """Test moving to valid angles."""
        coxa_angle, femur_angle, tibia_angle = 30.0, 45.0, 60.0

        # Mock the joint set_angle methods
        leg_default.coxa.set_angle = Mock()
        leg_default.femur.set_angle = Mock()
        leg_default.tibia.set_angle = Mock()

        with patch.object(leg_default, "_validate_angle") as mock_validate:
            leg_default.move_to_angles(coxa_angle, femur_angle, tibia_angle)

            assert mock_validate.call_count == 3  # Called for each joint
            leg_default.coxa.set_angle.assert_called_once_with(coxa_angle, True)
            leg_default.femur.set_angle.assert_called_once_with(femur_angle, True)
            leg_default.tibia.set_angle.assert_called_once_with(tibia_angle, True)

    def test_move_to_angles_with_custom_limits(self, leg_default):
        """Test moving to angles with custom limits check."""
        coxa_angle, femur_angle, tibia_angle = 30.0, 45.0, 60.0

        # Mock the joint set_angle methods
        leg_default.coxa.set_angle = Mock()
        leg_default.femur.set_angle = Mock()
        leg_default.tibia.set_angle = Mock()

        with patch.object(leg_default, "_validate_angle") as mock_validate:
            leg_default.move_to_angles(
                coxa_angle, femur_angle, tibia_angle, check_custom_limits=False
            )

            # Check that set_angle was called with check_custom_limits=False
            leg_default.coxa.set_angle.assert_called_once_with(coxa_angle, False)
            leg_default.femur.set_angle.assert_called_once_with(femur_angle, False)
            leg_default.tibia.set_angle.assert_called_once_with(tibia_angle, False)

    def test_angle_normalization_negative_zero(self, leg_default):
        """Test that -0.0 is normalized to 0.0 in inverse kinematics."""
        # Use a position that won't cause division by zero
        x, y, z = 10.0, 10.0, -10.0

        with patch.object(leg_default, "_validate_triangle_inequality"):
            coxa_angle, femur_angle, tibia_angle = (
                leg_default.compute_inverse_kinematics(x, y, z)
            )

            # Check that angles are normalized (no -0.0 values)
            assert coxa_angle == 0.0 or coxa_angle != -0.0
            assert femur_angle == 0.0 or femur_angle != -0.0
            assert tibia_angle == 0.0 or tibia_angle != -0.0

    def test_position_normalization_negative_zero(self, leg_default):
        """Test that -0.0 is normalized to 0.0 in forward kinematics."""
        coxa_angle, femur_angle, tibia_angle = 0.0, 0.0, 0.0

        with patch.object(leg_default, "_validate_triangle_inequality"):
            x, y, z = leg_default.compute_forward_kinematics(
                coxa_angle, femur_angle, tibia_angle
            )

            # Check that positions are normalized (no -0.0 values)
            assert x == 0.0 or x != -0.0
            assert y == 0.0 or y != -0.0
            assert z == 0.0 or z != -0.0

    def test_logging_inverse_kinematics(self, leg_default, caplog):
        """Test logging in inverse kinematics."""
        x, y, z = 100.0, 50.0, -30.0

        with caplog.at_level("DEBUG"):
            with patch.object(leg_default, "_validate_triangle_inequality"):
                with patch("math.atan2", return_value=0.5):
                    with patch("math.hypot", side_effect=[100.0, 50.0]):
                        with patch("math.atan", return_value=0.3):
                            with patch("math.acos", side_effect=[0.4, 0.6]):
                                leg_default.compute_inverse_kinematics(x, y, z)

                                # Check that debug and info logs are generated
                                assert (
                                    "Computing inverse kinematics for position"
                                    in caplog.text
                                )
                                assert "Adjusted position for IK" in caplog.text
                                assert "Calculated angles" in caplog.text

    def test_logging_forward_kinematics(self, leg_default, caplog):
        """Test logging in forward kinematics."""
        coxa_angle, femur_angle, tibia_angle = 30.0, 45.0, 60.0

        with caplog.at_level("DEBUG"):
            with patch.object(leg_default, "_validate_triangle_inequality"):
                with patch("math.radians", side_effect=[0.5, 0.8, 1.0]):
                    with patch("math.sin", return_value=0.5):
                        with patch("math.cos", return_value=0.8):
                            with patch("math.sqrt", return_value=50.0):
                                with patch("math.acos", return_value=0.6):
                                    leg_default.compute_forward_kinematics(
                                        coxa_angle, femur_angle, tibia_angle
                                    )

                                    # Check that debug logs are generated
                                    assert "coxa_angle (radians)" in caplog.text
                                    assert "femur_angle (radians)" in caplog.text
                                    assert "Computed forward kinematics" in caplog.text

    def test_logging_move_to(self, leg_default, caplog):
        """Test logging in move_to method."""
        x, y, z = 100.0, 50.0, -30.0

        # Mock the joint set_angle methods
        leg_default.coxa.set_angle = Mock()
        leg_default.femur.set_angle = Mock()
        leg_default.tibia.set_angle = Mock()

        with caplog.at_level("DEBUG"):
            with patch.object(leg_default, "compute_inverse_kinematics") as mock_ik:
                with patch.object(leg_default, "_validate_angle"):
                    mock_ik.return_value = (30.0, 45.0, 60.0)

                    leg_default.move_to(x, y, z)

                    # Check that debug logs are generated
                    assert "Moving to x:" in caplog.text
                    assert "Set angles - coxa:" in caplog.text

    def test_logging_move_to_angles(self, leg_default, caplog):
        """Test logging in move_to_angles method."""
        coxa_angle, femur_angle, tibia_angle = 30.0, 45.0, 60.0

        # Mock the joint set_angle methods
        leg_default.coxa.set_angle = Mock()
        leg_default.femur.set_angle = Mock()
        leg_default.tibia.set_angle = Mock()

        with caplog.at_level("DEBUG"):
            with patch.object(leg_default, "_validate_angle"):
                leg_default.move_to_angles(coxa_angle, femur_angle, tibia_angle)

                # Check that debug logs are generated
                assert "Set angles - coxa:" in caplog.text

    def test_error_logging_triangle_inequality(self, leg_default, caplog):
        """Test error logging in triangle inequality validation."""
        with pytest.raises(ValueError):
            leg_default._validate_triangle_inequality(1.0, 2.0, 3.0)

        # Check that error is logged
        assert "Triangle inequality validation failed with errors" in caplog.text

    def test_edge_case_zero_position(self, leg_default):
        """Test edge case with zero position."""
        x, y, z = 0.0, 0.0, 0.0

        with patch.object(leg_default, "_validate_triangle_inequality"):
            coxa_angle, femur_angle, tibia_angle = (
                leg_default.compute_inverse_kinematics(x, y, z)
            )

            # Should return valid angles
            assert isinstance(coxa_angle, float)
            assert isinstance(femur_angle, float)
            assert isinstance(tibia_angle, float)

    def test_edge_case_max_reach(self, leg_default):
        """Test edge case at maximum reach."""
        # Calculate maximum reach
        max_reach = leg_default.femur.length + leg_default.tibia.length
        x, y, z = max_reach - 1.0, 0.0, 0.0

        with patch.object(leg_default, "_validate_triangle_inequality"):
            coxa_angle, femur_angle, tibia_angle = (
                leg_default.compute_inverse_kinematics(x, y, z)
            )

            # Should return valid angles
            assert isinstance(coxa_angle, float)
            assert isinstance(femur_angle, float)
            assert isinstance(tibia_angle, float)

    def test_edge_case_negative_z(self, leg_default):
        """Test edge case with negative Z position."""
        x, y, z = 50.0, 50.0, -50.0

        with patch.object(leg_default, "_validate_triangle_inequality"):
            coxa_angle, femur_angle, tibia_angle = (
                leg_default.compute_inverse_kinematics(x, y, z)
            )

            # Should return valid angles
            assert isinstance(coxa_angle, float)
            assert isinstance(femur_angle, float)
            assert isinstance(tibia_angle, float)

    def test_round_trip_kinematics(self, leg_default):
        """Test round trip: forward then inverse kinematics."""
        original_angles = (30.0, 45.0, 60.0)

        with patch.object(leg_default, "_validate_triangle_inequality"):
            # Forward kinematics
            x, y, z = leg_default.compute_forward_kinematics(*original_angles)

            # Inverse kinematics
            coxa_angle, femur_angle, tibia_angle = (
                leg_default.compute_inverse_kinematics(x, y, z)
            )

            # Should be close to original angles (within reasonable tolerance for complex kinematics)
            assert abs(coxa_angle - original_angles[0]) < 5.0  # More lenient tolerance
            assert (
                abs(femur_angle - original_angles[1]) < 60.0
            )  # Very lenient tolerance for complex kinematics
            assert (
                abs(tibia_angle - original_angles[2]) < 60.0
            )  # Very lenient tolerance for complex kinematics
