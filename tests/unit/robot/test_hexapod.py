"""
Unit tests for hexapod robot logic.
"""

import pytest
import yaml
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from enum import Enum
from hexapod.robot.hexapod import Hexapod, PredefinedPosition, PredefinedAnglePosition


class TestHexapod:
    """Test cases for Hexapod class."""

    @pytest.fixture
    def mock_config_data(self):
        """Mock configuration data for testing."""
        return {
            "hexagon_side_length": 100.0,
            "controller": {"port": "/dev/ttyUSB0", "baudrate": 9600},
            "speed": 25,
            "accel": 10,
            "coxa_params": {
                "length": 50.0,
                "angle_min": -90.0,
                "angle_max": 90.0,
                "invert": False,
            },
            "femur_params": {
                "length": 80.0,
                "angle_min": -90.0,
                "angle_max": 90.0,
                "invert": False,
            },
            "tibia_params": {
                "length": 100.0,
                "angle_min": -90.0,
                "angle_max": 90.0,
                "invert": False,
            },
            "coxa_channel_map": [0, 3, 6, 9, 12, 15],
            "femur_channel_map": [1, 4, 7, 10, 13, 16],
            "tibia_channel_map": [2, 5, 8, 11, 14, 17],
            "end_effector_offset": [0.0, 0.0, 0.0],
            "leg_to_led": {0: 0, 1: 10, 2: 20, 3: 30, 4: 40, 5: 50},
            "predefined_positions": {
                "zero": [
                    [100, 0, -100],
                    [50, 87, -100],
                    [-50, 87, -100],
                    [-100, 0, -100],
                    [-50, -87, -100],
                    [50, -87, -100],
                ],
                "low_profile": [
                    [120, 0, -80],
                    [60, 104, -80],
                    [-60, 104, -80],
                    [-120, 0, -80],
                    [-60, -104, -80],
                    [60, -104, -80],
                ],
                "high_profile": [
                    [140, 0, -60],
                    [70, 121, -60],
                    [-70, 121, -60],
                    [-140, 0, -60],
                    [-70, -121, -60],
                    [70, -121, -60],
                ],
            },
            "predefined_angle_positions": {
                "zero": [
                    [0, 0, 0],
                    [0, 0, 0],
                    [0, 0, 0],
                    [0, 0, 0],
                    [0, 0, 0],
                    [0, 0, 0],
                ],
                "low_profile": [
                    [0, -30, 30],
                    [0, -30, 30],
                    [0, -30, 30],
                    [0, -30, 30],
                    [0, -30, 30],
                    [0, -30, 30],
                ],
                "high_profile": [
                    [0, -45, 45],
                    [0, -45, 45],
                    [0, -45, 45],
                    [0, -45, 45],
                    [0, -45, 45],
                    [0, -45, 45],
                ],
            },
            "gait": {"default_gait": "tripod", "step_height": 20.0},
        }

    @pytest.fixture
    def mock_calibration_data(self):
        """Mock calibration data for testing."""
        return {
            "coxa_offsets": [0, 0, 0, 0, 0, 0],
            "femur_offsets": [0, 0, 0, 0, 0, 0],
            "tibia_offsets": [0, 0, 0, 0, 0, 0],
        }

    @pytest.fixture
    def mock_hexapod(self, mock_config_data, mock_calibration_data, tmp_path):
        """Create a mock hexapod instance for testing."""
        # Create temporary config file
        config_file = tmp_path / "hexapod_config.yaml"
        with config_file.open("w") as f:
            yaml.dump(mock_config_data, f)

        # Create temporary calibration file
        calib_file = tmp_path / "calibration.json"
        with calib_file.open("w") as f:
            import json

            json.dump(mock_calibration_data, f)

        with (
            patch("hexapod.robot.hexapod.MaestroUART") as mock_maestro,
            patch("hexapod.robot.hexapod.Imu") as mock_imu,
            patch("hexapod.robot.hexapod.Calibration") as mock_calibration,
            patch("hexapod.robot.hexapod.GaitGenerator") as mock_gait,
        ):

            # Setup mock controller
            mock_maestro.return_value = Mock()
            mock_maestro.return_value.set_speed = Mock()
            mock_maestro.return_value.set_acceleration = Mock()
            mock_maestro.return_value.set_multiple_targets = Mock()
            mock_maestro.return_value.get_moving_state = Mock(return_value=0x00)

            # Setup mock IMU
            mock_imu.return_value = Mock()

            # Setup mock calibration
            mock_calibration.return_value = Mock()
            mock_calibration.return_value.load_calibration = Mock()

            # Setup mock gait generator
            mock_gait.return_value = Mock()

            hexapod = Hexapod(config_path=config_file, calibration_data_path=calib_file)
            return hexapod

    def test_init_default_config(self, mock_hexapod):
        """Test Hexapod initialization with default configuration."""
        assert mock_hexapod.hexagon_side_length == 100.0
        assert mock_hexapod.speed == 25
        assert mock_hexapod.accel == 10
        assert len(mock_hexapod.legs) == 6
        assert len(mock_hexapod.current_leg_angles) == 6
        assert len(mock_hexapod.current_leg_positions) == 6
        assert mock_hexapod.controller is not None
        assert mock_hexapod.imu is not None
        assert mock_hexapod.calibration is not None
        assert mock_hexapod.gait_generator is not None

    def test_init_custom_config(
        self, mock_config_data, mock_calibration_data, tmp_path
    ):
        """Test Hexapod initialization with custom configuration."""
        # Modify config for custom test
        mock_config_data["speed"] = 50
        mock_config_data["accel"] = 20

        config_file = tmp_path / "custom_config.yaml"
        with config_file.open("w") as f:
            yaml.dump(mock_config_data, f)

        calib_file = tmp_path / "calibration.json"
        with calib_file.open("w") as f:
            import json

            json.dump(mock_calibration_data, f)

        with (
            patch("hexapod.robot.hexapod.MaestroUART") as mock_maestro,
            patch("hexapod.robot.hexapod.Imu") as mock_imu,
            patch("hexapod.robot.hexapod.Calibration") as mock_calibration,
            patch("hexapod.robot.hexapod.GaitGenerator") as mock_gait,
        ):

            mock_maestro.return_value = Mock()
            mock_maestro.return_value.set_speed = Mock()
            mock_maestro.return_value.set_acceleration = Mock()
            mock_imu.return_value = Mock()
            mock_calibration.return_value = Mock()
            mock_calibration.return_value.load_calibration = Mock()
            mock_gait.return_value = Mock()

            hexapod = Hexapod(config_path=config_file, calibration_data_path=calib_file)
            assert hexapod.speed == 50
            assert hexapod.accel == 20

    def test_init_missing_config_file(self, tmp_path):
        """Test Hexapod initialization with missing config file."""
        with pytest.raises(
            FileNotFoundError, match="Hexapod configuration file not found"
        ):
            Hexapod(config_path=tmp_path / "nonexistent.yaml")

    def test_init_missing_calibration_file(self, mock_config_data, tmp_path):
        """Test Hexapod initialization with missing calibration file."""
        config_file = tmp_path / "config.yaml"
        with config_file.open("w") as f:
            yaml.dump(mock_config_data, f)

        with pytest.raises(FileNotFoundError, match="Calibration data file not found"):
            Hexapod(
                config_path=config_file,
                calibration_data_path=tmp_path / "nonexistent.json",
            )

    def test_hexagon_angles_computation(self, mock_hexapod):
        """Test hexagon angles computation."""
        expected_angles = [0, 60, 120, 180, 240, 300]  # degrees
        computed_angles = mock_hexapod._compute_hexagon_angles()
        assert computed_angles == expected_angles

        # Test that leg_angles are in radians
        expected_radians = np.radians(expected_angles)
        np.testing.assert_array_almost_equal(mock_hexapod.leg_angles, expected_radians)

    def test_end_effector_radius_calculation(self, mock_hexapod):
        """Test end effector radius calculation."""
        expected_radius = (
            100.0 + 50.0 + 80.0
        )  # hexagon_side_length + coxa_length + femur_length
        assert mock_hexapod.end_effector_radius == expected_radius

    def test_calibrate_all_servos(self, mock_hexapod):
        """Test servo calibration."""
        mock_hexapod.calibrate_all_servos()
        mock_hexapod.calibration.calibrate_all_servos.assert_called_once()

    def test_calibrate_all_servos_with_stop_event(self, mock_hexapod):
        """Test servo calibration with stop event."""
        import threading

        stop_event = threading.Event()
        mock_hexapod.calibrate_all_servos(stop_event=stop_event)
        mock_hexapod.calibration.calibrate_all_servos.assert_called_once_with(
            stop_event=stop_event
        )

    def test_set_all_servos_speed_percentage(self, mock_hexapod):
        """Test setting all servos speed with percentage."""
        # Reset call count to ignore initialization calls
        mock_hexapod.controller.set_speed.reset_mock()

        mock_hexapod.set_all_servos_speed(50)

        # Verify controller.set_speed was called for all channels
        expected_calls = 18  # 6 legs * 3 joints each
        assert mock_hexapod.controller.set_speed.call_count == expected_calls

        # Verify speed was mapped correctly (50% -> 126)
        for call in mock_hexapod.controller.set_speed.call_args_list:
            args, kwargs = call
            channel, speed = args
            assert speed == 126  # map_range(50, 1, 100, 1, 255) = 126

    def test_set_all_servos_speed_unlimited(self, mock_hexapod):
        """Test setting all servos speed to unlimited."""
        # Reset call count to ignore initialization calls
        mock_hexapod.controller.set_speed.reset_mock()

        mock_hexapod.set_all_servos_speed(0)

        # Verify controller.set_speed was called for all channels with 0
        expected_calls = 18
        assert mock_hexapod.controller.set_speed.call_count == expected_calls

        for call in mock_hexapod.controller.set_speed.call_args_list:
            args, kwargs = call
            channel, speed = args
            assert speed == 0

    def test_set_all_servos_accel_percentage(self, mock_hexapod):
        """Test setting all servos acceleration with percentage."""
        # Reset call count to ignore initialization calls
        mock_hexapod.controller.set_acceleration.reset_mock()

        mock_hexapod.set_all_servos_accel(30)

        # Verify controller.set_acceleration was called for all channels
        expected_calls = 18
        assert mock_hexapod.controller.set_acceleration.call_count == expected_calls

        # Verify acceleration was mapped correctly (30% -> 75)
        for call in mock_hexapod.controller.set_acceleration.call_args_list:
            args, kwargs = call
            channel, accel = args
            assert accel == 75  # map_range(30, 1, 100, 1, 255) = 75

    def test_set_all_servos_accel_unlimited(self, mock_hexapod):
        """Test setting all servos acceleration to unlimited."""
        # Reset call count to ignore initialization calls
        mock_hexapod.controller.set_acceleration.reset_mock()

        mock_hexapod.set_all_servos_accel(0)

        # Verify controller.set_acceleration was called for all channels with 0
        expected_calls = 18
        assert mock_hexapod.controller.set_acceleration.call_count == expected_calls

        for call in mock_hexapod.controller.set_acceleration.call_args_list:
            args, kwargs = call
            channel, accel = args
            assert accel == 0

    def test_move_leg_valid(self, mock_hexapod):
        """Test moving leg to valid position."""
        # Mock the leg's move_to method
        mock_hexapod.legs[0].move_to = Mock()
        mock_hexapod.legs[0].compute_inverse_kinematics = Mock(
            return_value=(0.0, -30.0, 30.0)
        )

        mock_hexapod.move_leg(0, 100.0, 0.0, -80.0)

        # Verify leg's move_to was called
        mock_hexapod.legs[0].move_to.assert_called_once_with(100.0, 0.0, -80.0)

        # Verify current position was updated
        assert mock_hexapod.current_leg_positions[0] == (100.0, 0.0, -80.0)

        # Verify inverse kinematics was called
        mock_hexapod.legs[0].compute_inverse_kinematics.assert_called_once_with(
            100.0, 0.0, -80.0
        )

        # Verify current angles were updated
        assert mock_hexapod.current_leg_angles[0] == (0.0, -30.0, 30.0)

    def test_move_leg_invalid_index(self, mock_hexapod):
        """Test moving leg with invalid index."""
        with pytest.raises(IndexError):
            mock_hexapod.move_leg(6, 100.0, 0.0, -80.0)  # Index 6 is out of range

    def test_move_leg_angles_valid(self, mock_hexapod):
        """Test moving leg to valid angles."""
        # Mock the leg's move_to_angles method
        mock_hexapod.legs[0].move_to_angles = Mock()
        mock_hexapod.legs[0].compute_forward_kinematics = Mock(
            return_value=(100.0, 0.0, -80.0)
        )

        mock_hexapod.move_leg_angles(0, 0.0, -30.0, 30.0)

        # Verify leg's move_to_angles was called
        mock_hexapod.legs[0].move_to_angles.assert_called_once_with(0.0, -30.0, 30.0)

        # Verify current angles were updated
        assert mock_hexapod.current_leg_angles[0] == (0.0, -30.0, 30.0)

        # Verify forward kinematics was called
        mock_hexapod.legs[0].compute_forward_kinematics.assert_called_once_with(
            0.0, -30.0, 30.0
        )

        # Verify current position was updated
        assert mock_hexapod.current_leg_positions[0] == (100.0, 0.0, -80.0)

    def test_move_leg_angles_invalid_index(self, mock_hexapod):
        """Test moving leg angles with invalid index."""
        with pytest.raises(IndexError):
            mock_hexapod.move_leg_angles(6, 0.0, -30.0, 30.0)  # Index 6 is out of range

    def test_move_body_valid(self, mock_hexapod):
        """Test moving body with valid parameters."""
        # Mock the internal methods
        mock_hexapod._compute_body_inverse_kinematics = Mock(
            return_value=np.array([[1, 2, 3]] * 6)
        )
        mock_hexapod._transform_body_to_leg_frames = Mock(
            return_value=np.array([[0.5, 1, 1.5]] * 6)
        )
        mock_hexapod.move_all_legs = Mock()
        mock_hexapod._sync_angles_from_positions = Mock()

        mock_hexapod.move_body(tx=10.0, ty=5.0, tz=-2.0, roll=5.0, pitch=10.0, yaw=15.0)

        # Verify body IK was called
        mock_hexapod._compute_body_inverse_kinematics.assert_called_once_with(
            10.0, 5.0, -2.0, 5.0, 10.0, 15.0
        )

        # Verify transform was called
        mock_hexapod._transform_body_to_leg_frames.assert_called_once()

        # Verify move_all_legs was called
        mock_hexapod.move_all_legs.assert_called_once()

        # Verify sync was called
        mock_hexapod._sync_angles_from_positions.assert_called_once()

    def test_move_body_with_angle_validation_error(self, mock_hexapod):
        """Test move_body with angle validation error."""
        # Mock the internal methods
        mock_hexapod._compute_body_inverse_kinematics = Mock(
            return_value=np.array([[1, 2, 3]] * 6)
        )
        mock_hexapod._transform_body_to_leg_frames = Mock(
            return_value=np.array([[0.5, 1, 1.5]] * 6)
        )
        mock_hexapod.move_all_legs = Mock(side_effect=ValueError("Angle out of limits"))
        mock_hexapod._sync_angles_from_positions = Mock()

        with pytest.raises(ValueError, match="Angle out of limits.*move_body"):
            mock_hexapod.move_body(tx=10.0, ty=5.0, tz=-2.0)

    def test_move_to_position_valid(self, mock_hexapod):
        """Test moving to valid predefined position."""
        mock_hexapod.move_all_legs = Mock()

        mock_hexapod.move_to_position(PredefinedPosition.LOW_PROFILE)

        # Verify move_all_legs was called with correct positions
        mock_hexapod.move_all_legs.assert_called_once()
        call_args = mock_hexapod.move_all_legs.call_args[0][0]
        assert len(call_args) == 6
        assert all(isinstance(pos, tuple) for pos in call_args)

    def test_move_to_position_invalid(self, mock_hexapod):
        """Test moving to invalid predefined position."""

        # Create a mock enum that doesn't exist in predefined_positions
        class InvalidPosition(Enum):
            INVALID = "invalid_position"

        # Mock move_all_legs to track calls
        mock_hexapod.move_all_legs = Mock()

        # The method should not raise an exception, just log an error
        mock_hexapod.move_to_position(InvalidPosition.INVALID)

        # Verify that move_all_legs was not called for invalid position
        mock_hexapod.move_all_legs.assert_not_called()

    def test_move_to_angles_position_valid(self, mock_hexapod):
        """Test moving to valid predefined angle position."""
        mock_hexapod.move_all_legs_angles = Mock()

        mock_hexapod.move_to_angles_position(PredefinedAnglePosition.LOW_PROFILE)

        # Verify move_all_legs_angles was called
        mock_hexapod.move_all_legs_angles.assert_called_once()
        call_args = mock_hexapod.move_all_legs_angles.call_args[0][0]
        assert len(call_args) == 6
        assert all(isinstance(angles, tuple) for angles in call_args)

    def test_move_to_angles_position_with_validation_error(self, mock_hexapod):
        """Test move_to_angles_position with angle validation error."""
        mock_hexapod.move_all_legs_angles = Mock(
            side_effect=ValueError("Angle out of limits")
        )

        with pytest.raises(
            ValueError, match="Angle out of limits.*move_to_angles_position"
        ):
            mock_hexapod.move_to_angles_position(PredefinedAnglePosition.LOW_PROFILE)

    def test_deactivate_all_servos(self, mock_hexapod):
        """Test deactivating all servos."""
        with patch("time.sleep") as mock_sleep:
            mock_hexapod.deactivate_all_servos()

            # Verify sleep was called
            mock_sleep.assert_called_once_with(2.0)

            # Verify set_multiple_targets was called
            mock_hexapod.controller.set_multiple_targets.assert_called_once()

            # Verify all targets are set to 0
            call_args = mock_hexapod.controller.set_multiple_targets.call_args[0][0]
            assert all(target[1] == 0 for target in call_args)
            assert len(call_args) == 24  # All 24 channels

    def test_move_all_legs_valid(self, mock_hexapod):
        """Test moving all legs with valid positions."""
        positions = [
            (100, 0, -80),
            (50, 87, -80),
            (-50, 87, -80),
            (-100, 0, -80),
            (-50, -87, -80),
            (50, -87, -80),
        ]

        # Mock leg methods
        for i, leg in enumerate(mock_hexapod.legs):
            leg.compute_inverse_kinematics = Mock(return_value=(0.0, -30.0, 30.0))
            leg.coxa.invert = False
            leg.femur.invert = False
            leg.tibia.invert = False
            leg.coxa.angle_to_servo_target = Mock(return_value=1500)
            leg.femur.angle_to_servo_target = Mock(return_value=1500)
            leg.tibia.angle_to_servo_target = Mock(return_value=1500)
            leg.coxa.channel = i * 3
            leg.femur.channel = i * 3 + 1
            leg.tibia.channel = i * 3 + 2

        mock_hexapod.move_all_legs(positions)

        # Verify controller.set_multiple_targets was called
        mock_hexapod.controller.set_multiple_targets.assert_called_once()

        # Verify current positions were updated
        assert mock_hexapod.current_leg_positions == [
            (100.0, 0.0, -80.0),
            (50.0, 87.0, -80.0),
            (-50.0, 87.0, -80.0),
            (-100.0, 0.0, -80.0),
            (-50.0, -87.0, -80.0),
            (50.0, -87.0, -80.0),
        ]

    def test_move_all_legs_angles_valid(self, mock_hexapod):
        """Test moving all legs with valid angles."""
        angles = [
            (0, -30, 30),
            (0, -30, 30),
            (0, -30, 30),
            (0, -30, 30),
            (0, -30, 30),
            (0, -30, 30),
        ]

        # Mock leg methods
        for i, leg in enumerate(mock_hexapod.legs):
            leg.coxa.invert = False
            leg.femur.invert = False
            leg.tibia.invert = False
            leg.coxa.angle_to_servo_target = Mock(return_value=1500)
            leg.femur.angle_to_servo_target = Mock(return_value=1500)
            leg.tibia.angle_to_servo_target = Mock(return_value=1500)
            leg.coxa.channel = i * 3
            leg.femur.channel = i * 3 + 1
            leg.tibia.channel = i * 3 + 2

        mock_hexapod.move_all_legs_angles(angles)

        # Verify controller.set_multiple_targets was called
        mock_hexapod.controller.set_multiple_targets.assert_called_once()

        # Verify current angles were updated
        assert mock_hexapod.current_leg_angles == angles

    def test_move_all_legs_angles_with_validation_error(self, mock_hexapod):
        """Test move_all_legs_angles with angle validation error."""
        # Create angles that are out of range
        invalid_angles = [
            (200, -30, 30),
            (0, -30, 30),
            (0, -30, 30),
            (0, -30, 30),
            (0, -30, 30),
            (0, -30, 30),
        ]  # coxa angle 200 is out of range

        with pytest.raises(ValueError, match="Coxa angle 200.*out of limits"):
            mock_hexapod.move_all_legs_angles(invalid_angles)

    def test_validate_angles_valid(self, mock_hexapod):
        """Test angle validation with valid angles."""
        valid_angles = [
            (0, -30, 30),
            (0, -30, 30),
            (0, -30, 30),
            (0, -30, 30),
            (0, -30, 30),
            (0, -30, 30),
        ]

        # Should not raise any exception
        mock_hexapod._validate_angles(valid_angles, "test_method")

    def test_validate_angles_invalid_coxa(self, mock_hexapod):
        """Test angle validation with invalid coxa angle."""
        invalid_angles = [
            (200, -30, 30),
            (0, -30, 30),
            (0, -30, 30),
            (0, -30, 30),
            (0, -30, 30),
            (0, -30, 30),
        ]

        with pytest.raises(
            ValueError, match="Coxa angle 200.*out of limits.*test_method"
        ):
            mock_hexapod._validate_angles(invalid_angles, "test_method")

    def test_validate_angles_invalid_femur(self, mock_hexapod):
        """Test angle validation with invalid femur angle."""
        invalid_angles = [
            (0, 200, 30),
            (0, -30, 30),
            (0, -30, 30),
            (0, -30, 30),
            (0, -30, 30),
            (0, -30, 30),
        ]

        with pytest.raises(
            ValueError, match="Femur angle 200.*out of limits.*test_method"
        ):
            mock_hexapod._validate_angles(invalid_angles, "test_method")

    def test_validate_angles_invalid_tibia(self, mock_hexapod):
        """Test angle validation with invalid tibia angle."""
        invalid_angles = [
            (0, -30, 200),
            (0, -30, 30),
            (0, -30, 30),
            (0, -30, 30),
            (0, -30, 30),
            (0, -30, 30),
        ]

        with pytest.raises(
            ValueError, match="Tibia angle 200.*out of limits.*test_method"
        ):
            mock_hexapod._validate_angles(invalid_angles, "test_method")

    def test_wait_until_motion_complete(self, mock_hexapod):
        """Test waiting until motion is complete."""
        import threading

        # Mock the moving state to return True then False
        mock_hexapod._get_moving_state = Mock(side_effect=[True, False])

        with patch("time.time", side_effect=[0, 0.5, 1.0, 1.5]):
            mock_hexapod.wait_until_motion_complete()

        # Verify _get_moving_state was called
        assert mock_hexapod._get_moving_state.call_count >= 1

    def test_wait_until_motion_complete_with_stop_event(self, mock_hexapod):
        """Test waiting until motion is complete with stop event."""
        import threading

        stop_event = threading.Event()
        stop_event.set()  # Set the event immediately

        mock_hexapod._get_moving_state = Mock(return_value=True)

        with patch("time.time", side_effect=[0, 0.5, 1.0]):
            mock_hexapod.wait_until_motion_complete(stop_event=stop_event)

        # Should return early due to stop event
        assert mock_hexapod._get_moving_state.call_count == 0

    def test_get_moving_state(self, mock_hexapod):
        """Test getting moving state from controller."""
        mock_hexapod.controller.get_moving_state.return_value = 0x01

        result = mock_hexapod._get_moving_state()
        assert result is True

        mock_hexapod.controller.get_moving_state.return_value = 0x00
        result = mock_hexapod._get_moving_state()
        assert result is False

    def test_sync_positions_from_angles(self, mock_hexapod):
        """Test syncing positions from angles."""
        # Set up mock angles
        mock_hexapod.current_leg_angles = [(0, -30, 30)] * 6

        # Mock leg forward kinematics
        for leg in mock_hexapod.legs:
            leg.compute_forward_kinematics = Mock(return_value=(100.0, 0.0, -80.0))

        mock_hexapod._sync_positions_from_angles()

        # Verify all positions were updated
        expected_positions = [(100.0, 0.0, -80.0)] * 6
        assert mock_hexapod.current_leg_positions == expected_positions

    def test_sync_angles_from_positions(self, mock_hexapod):
        """Test syncing angles from positions."""
        # Set up mock positions
        mock_hexapod.current_leg_positions = [(100.0, 0.0, -80.0)] * 6

        # Mock leg inverse kinematics
        for leg in mock_hexapod.legs:
            leg.compute_inverse_kinematics = Mock(return_value=(0.0, -30.0, 30.0))

        mock_hexapod._sync_angles_from_positions()

        # Verify all angles were updated
        expected_angles = [(0.0, -30.0, 30.0)] * 6
        assert mock_hexapod.current_leg_angles == expected_angles

    def test_compute_body_inverse_kinematics(self, mock_hexapod):
        """Test body inverse kinematics computation."""
        deltas = mock_hexapod._compute_body_inverse_kinematics(
            tx=10.0, ty=5.0, tz=-2.0, roll=5.0, pitch=10.0, yaw=15.0
        )

        # Verify deltas shape
        assert deltas.shape == (6, 3)

        # Verify deltas are rounded to 2 decimal places
        assert np.all(np.round(deltas, 2) == deltas)

    def test_transform_body_to_leg_frames(self, mock_hexapod):
        """Test transformation from body to leg frames."""
        body_deltas = np.array([[1.0, 2.0, 3.0]] * 6)

        leg_deltas = mock_hexapod._transform_body_to_leg_frames(body_deltas)

        # Verify output shape
        assert leg_deltas.shape == (6, 3)

        # Verify deltas are rounded to 2 decimal places (allow for small floating point differences)
        expected_leg_deltas = np.array(
            [
                [-2.0, 1.0, 3.0],
                [-0.1339746, 2.23205081, 3.0],
                [1.8660254, 1.23205081, 3.0],
                [2.0, -1.0, 3.0],
                [0.1339746, -2.23205081, 3.0],
                [-1.8660254, -1.23205081, 3.0],
            ]
        )
        np.testing.assert_allclose(leg_deltas, expected_leg_deltas, rtol=1e-6)

    def test_controller_channels_constant(self, mock_hexapod):
        """Test CONTROLLER_CHANNELS constant."""
        assert mock_hexapod.CONTROLLER_CHANNELS == 24

    def test_predefined_positions_enum(self):
        """Test PredefinedPosition enum values."""
        assert PredefinedPosition.ZERO.value == "zero"
        assert PredefinedPosition.LOW_PROFILE.value == "low_profile"
        assert PredefinedPosition.HIGH_PROFILE.value == "high_profile"

    def test_predefined_angle_positions_enum(self):
        """Test PredefinedAnglePosition enum values."""
        assert PredefinedAnglePosition.ZERO.value == "zero"
        assert PredefinedAnglePosition.LOW_PROFILE.value == "low_profile"
        assert PredefinedAnglePosition.HIGH_PROFILE.value == "high_profile"
