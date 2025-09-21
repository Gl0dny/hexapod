"""
Unit tests for status reporter system.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path

from hexapod.task_interface.status_reporter import StatusReporter


class TestStatusReporter:
    """Test cases for StatusReporter class."""

    @pytest.fixture
    def mock_hexapod(self):
        """Mock hexapod instance for testing."""
        hexapod = MagicMock()

        # Mock IMU
        hexapod.imu = MagicMock()
        hexapod.imu.get_acceleration.return_value = (0.1, 0.2, 9.8)
        hexapod.imu.get_gyroscope.return_value = (0.5, -0.3, 0.1)
        hexapod.imu.get_temperature.return_value = 25.5

        # Mock movement status
        hexapod._get_moving_state.return_value = False
        hexapod.speed = 50
        hexapod.accel = 30

        # Mock leg positions and angles
        hexapod.current_leg_positions = [
            (100.0, 50.0, -80.0),
            (120.0, 60.0, -85.0),
            (110.0, 55.0, -82.0),
            (105.0, 52.0, -81.0),
            (115.0, 58.0, -83.0),
            (125.0, 62.0, -86.0),
        ]
        hexapod.current_leg_angles = [
            (10.0, 20.0, 30.0),
            (12.0, 22.0, 32.0),
            (11.0, 21.0, 31.0),
            (10.5, 20.5, 30.5),
            (11.5, 21.5, 31.5),
            (12.5, 22.5, 32.5),
        ]

        # Mock gait generator
        hexapod.gait_generator = MagicMock()
        hexapod.gait_generator.current_state = None

        # Mock calibration
        hexapod.calibration = MagicMock()
        hexapod.calibration.calibration_data_path = Path("/test/calibration.yaml")
        hexapod.calibration.is_calibrated = True

        # Mock system properties
        hexapod.hexagon_side_length = 200
        hexapod.CONTROLLER_CHANNELS = 18
        hexapod.end_effector_radius = 15.5

        return hexapod

    @pytest.fixture
    def status_reporter(self):
        """Create StatusReporter instance for testing."""
        return StatusReporter()

    def test_init_default_parameters(self):
        """Test StatusReporter initialization with default parameters."""
        reporter = StatusReporter()
        assert reporter is not None

    def test_get_complete_status_success(self, status_reporter, mock_hexapod):
        """Test getting complete status report successfully."""
        with (
            patch.object(status_reporter, "_get_system_info") as mock_system,
            patch.object(
                status_reporter, "_get_calibration_status"
            ) as mock_calibration,
            patch.object(status_reporter, "_get_imu_status") as mock_imu,
            patch.object(status_reporter, "_get_gait_status") as mock_gait,
            patch.object(status_reporter, "_get_movement_status") as mock_movement,
            patch.object(status_reporter, "_get_leg_positions_status") as mock_legs,
        ):

            # Mock return values
            mock_system.return_value = "System Info: Test"
            mock_calibration.return_value = "Calibration: Test"
            mock_imu.return_value = "IMU: Test"
            mock_gait.return_value = "Gait: Test"
            mock_movement.return_value = "Movement: Test"
            mock_legs.return_value = "Legs: Test"

            result = status_reporter.get_complete_status(mock_hexapod)

            # Check that all methods were called
            mock_system.assert_called_once_with(mock_hexapod)
            mock_calibration.assert_called_once_with(mock_hexapod)
            mock_imu.assert_called_once_with(mock_hexapod)
            mock_gait.assert_called_once_with(mock_hexapod)
            mock_movement.assert_called_once_with(mock_hexapod)
            mock_legs.assert_called_once_with(mock_hexapod)

            # Check result format
            assert "=== HEXAPOD SYSTEM STATUS ===" in result
            assert "=== END STATUS REPORT ===" in result
            assert "System Info: Test" in result
            assert "Calibration: Test" in result
            assert "IMU: Test" in result
            assert "Gait: Test" in result
            assert "Movement: Test" in result
            assert "Legs: Test" in result

    def test_get_imu_status_success(self, status_reporter, mock_hexapod):
        """Test getting IMU status successfully."""
        result = status_reporter._get_imu_status(mock_hexapod)

        assert "IMU Status:" in result
        assert "Acceleration: X=+0.10 Y=+0.20 Z=+9.80 g" in result
        assert "Gyroscope: X=+0.50 Y=-0.30 Z=+0.10 °/s" in result
        assert "Temperature: 25.5°C" in result

        # Verify IMU methods were called
        mock_hexapod.imu.get_acceleration.assert_called_once()
        mock_hexapod.imu.get_gyroscope.assert_called_once()
        mock_hexapod.imu.get_temperature.assert_called_once()

    def test_get_imu_status_error(self, status_reporter, mock_hexapod, caplog):
        """Test getting IMU status with error."""
        mock_hexapod.imu.get_acceleration.side_effect = Exception("IMU error")

        result = status_reporter._get_imu_status(mock_hexapod)

        assert result == "IMU Status: Error reading sensor data"
        assert "Error reading IMU data: IMU error" in caplog.text

    def test_get_movement_status_success(self, status_reporter, mock_hexapod):
        """Test getting movement status successfully."""
        result = status_reporter._get_movement_status(mock_hexapod)

        assert "Movement Status:" in result
        assert "State: Stationary" in result
        assert "Servo Speed: 50%" in result
        assert "Servo Acceleration: 30%" in result

        mock_hexapod._get_moving_state.assert_called_once()

    def test_get_movement_status_moving(self, status_reporter, mock_hexapod):
        """Test getting movement status when moving."""
        mock_hexapod._get_moving_state.return_value = True

        result = status_reporter._get_movement_status(mock_hexapod)

        assert "State: Moving" in result

    def test_get_movement_status_error(self, status_reporter, mock_hexapod, caplog):
        """Test getting movement status with error."""
        mock_hexapod._get_moving_state.side_effect = Exception("Movement error")

        result = status_reporter._get_movement_status(mock_hexapod)

        assert result == "Movement Status: Error reading servo data"
        assert "Error reading movement status: Movement error" in caplog.text

    def test_get_leg_positions_status_success(self, status_reporter, mock_hexapod):
        """Test getting leg positions status successfully."""
        result = status_reporter._get_leg_positions_status(mock_hexapod)

        assert "Leg Positions:" in result
        assert (
            "Leg 0: Pos( 100.0,   50.0,  -80.0) mm | Angles( 10.0°,  20.0°,  30.0°)"
            in result
        )
        assert (
            "Leg 1: Pos( 120.0,   60.0,  -85.0) mm | Angles( 12.0°,  22.0°,  32.0°)"
            in result
        )
        assert (
            "Leg 2: Pos( 110.0,   55.0,  -82.0) mm | Angles( 11.0°,  21.0°,  31.0°)"
            in result
        )
        assert (
            "Leg 3: Pos( 105.0,   52.0,  -81.0) mm | Angles( 10.5°,  20.5°,  30.5°)"
            in result
        )
        assert (
            "Leg 4: Pos( 115.0,   58.0,  -83.0) mm | Angles( 11.5°,  21.5°,  31.5°)"
            in result
        )
        assert (
            "Leg 5: Pos( 125.0,   62.0,  -86.0) mm | Angles( 12.5°,  22.5°,  32.5°)"
            in result
        )

    def test_get_leg_positions_status_error(
        self, status_reporter, mock_hexapod, caplog
    ):
        """Test getting leg positions status with error."""
        mock_hexapod.current_leg_positions = None

        result = status_reporter._get_leg_positions_status(mock_hexapod)

        assert result == "Leg Positions: Error reading position data"
        assert "Error reading leg positions:" in caplog.text

    def test_get_gait_status_no_active_gait(self, status_reporter, mock_hexapod):
        """Test getting gait status when no active gait."""
        result = status_reporter._get_gait_status(mock_hexapod)

        assert result == "Gait Status: No active gait"

    def test_get_gait_status_no_current_state(self, status_reporter, mock_hexapod):
        """Test getting gait status when no current state."""
        mock_hexapod.gait_generator.current_state = None

        result = status_reporter._get_gait_status(mock_hexapod)

        assert result == "Gait Status: No active gait"

    def test_get_gait_status_success(self, status_reporter, mock_hexapod):
        """Test getting gait status successfully."""
        # Mock gait state with various attributes
        mock_state = MagicMock()
        mock_state.phase = "swing"
        mock_state.swing_legs = [0, 2, 4]
        mock_state.stance_legs = [1, 3, 5]
        mock_state.dwell_time = 0.5

        mock_hexapod.gait_generator.current_state = mock_state
        mock_hexapod.gait_generator.__class__.__name__ = "TripodGait"

        result = status_reporter._get_gait_status(mock_hexapod)

        assert "Gait Status:" in result
        assert "Type: TripodGait" in result
        assert "Phase: swing" in result
        assert "Swing Legs: [0, 2, 4]" in result
        assert "Stance Legs: [1, 3, 5]" in result
        assert "Dwell Time: 0.50s" in result

    def test_get_gait_status_minimal_state(self, status_reporter, mock_hexapod):
        """Test getting gait status with minimal state."""
        mock_state = MagicMock()
        mock_hexapod.gait_generator.current_state = mock_state
        mock_hexapod.gait_generator.__class__.__name__ = "WaveGait"

        # Mock the state attributes to avoid format string errors
        mock_state.phase = "stance"
        mock_state.swing_legs = [0, 2, 4]
        mock_state.stance_legs = [1, 3, 5]
        mock_state.dwell_time = 0.1

        result = status_reporter._get_gait_status(mock_hexapod)

        assert "Gait Status:" in result
        assert "Type: WaveGait" in result
        # Should not have phase, swing_legs, etc. since they're not set

    def test_get_calibration_status_success(self, status_reporter, mock_hexapod):
        """Test getting calibration status successfully."""
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.stat") as mock_stat,
        ):

            # Mock file stats
            mock_stat.return_value.st_mtime = 1640995200  # 2022-01-01 00:00:00

            # Mock datetime.fromtimestamp directly
            with patch(
                "hexapod.task_interface.status_reporter.datetime"
            ) as mock_datetime:
                mock_datetime.fromtimestamp.return_value.strftime.return_value = (
                    "2022-01-01 00:00:00"
                )

                result = status_reporter._get_calibration_status(mock_hexapod)

                assert "Calibration Status:" in result
                assert "Status: Calibrated" in result
                assert "Last Calibration: 2022-01-01 00:00:00" in result
                assert "File: calibration.yaml" in result

    def test_get_calibration_status_not_calibrated(self, status_reporter, mock_hexapod):
        """Test getting calibration status when not calibrated."""
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.stat") as mock_stat,
        ):

            mock_stat.return_value.st_mtime = 1640995200
            mock_hexapod.calibration.is_calibrated = False

            # Mock datetime.fromtimestamp directly
            with patch(
                "hexapod.task_interface.status_reporter.datetime"
            ) as mock_datetime:
                mock_datetime.fromtimestamp.return_value.strftime.return_value = (
                    "2022-01-01 00:00:00"
                )

                result = status_reporter._get_calibration_status(mock_hexapod)

                assert "Status: Not calibrated" in result

    def test_get_calibration_status_no_file(self, status_reporter, mock_hexapod):
        """Test getting calibration status when no file exists."""
        with patch("pathlib.Path.exists", return_value=False):
            result = status_reporter._get_calibration_status(mock_hexapod)

            assert (
                result
                == "Calibration Status: Not calibrated (no calibration file found)"
            )

    def test_get_calibration_status_no_is_calibrated_attr(
        self, status_reporter, mock_hexapod
    ):
        """Test getting calibration status when is_calibrated attribute doesn't exist."""
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.stat") as mock_stat,
        ):

            mock_stat.return_value.st_mtime = 1640995200
            del mock_hexapod.calibration.is_calibrated  # Remove the attribute

            # Mock datetime.fromtimestamp directly
            with patch(
                "hexapod.task_interface.status_reporter.datetime"
            ) as mock_datetime:
                mock_datetime.fromtimestamp.return_value.strftime.return_value = (
                    "2022-01-01 00:00:00"
                )

                result = status_reporter._get_calibration_status(mock_hexapod)

                assert (
                    "Status: Calibrated" in result
                )  # Should default to calibrated if file exists

    def test_get_system_info_success(self, status_reporter, mock_hexapod):
        """Test getting system info successfully."""
        result = status_reporter._get_system_info(mock_hexapod)

        assert "System Info:" in result
        assert "Hexagon Side Length: 200 mm" in result
        assert "Controller Channels: 18" in result
        assert "End Effector Radius: 15.5 mm" in result

    def test_get_system_info_error(self, status_reporter, mock_hexapod, caplog):
        """Test getting system info with error."""
        # Mock the hexapod to raise an exception when accessing end_effector_radius
        mock_hexapod.end_effector_radius = MagicMock(
            side_effect=Exception("System error")
        )

        result = status_reporter._get_system_info(mock_hexapod)

        assert result == "System Info: Error reading system data"
        assert "Error reading system info:" in caplog.text

    def test_get_complete_status_with_errors(self, status_reporter, mock_hexapod):
        """Test getting complete status when some methods return errors."""
        with (
            patch.object(
                status_reporter,
                "_get_system_info",
                return_value="System Info: Error reading system data",
            ),
            patch.object(
                status_reporter,
                "_get_calibration_status",
                return_value="Calibration: Error reading calibration data",
            ),
            patch.object(
                status_reporter,
                "_get_imu_status",
                return_value="IMU: Error reading sensor data",
            ),
            patch.object(
                status_reporter,
                "_get_gait_status",
                return_value="Gait Status: No active gait",
            ),
            patch.object(
                status_reporter,
                "_get_movement_status",
                return_value="Movement: Error reading servo data",
            ),
            patch.object(
                status_reporter,
                "_get_leg_positions_status",
                return_value="Leg Positions: Error reading position data",
            ),
        ):

            result = status_reporter.get_complete_status(mock_hexapod)

            assert "=== HEXAPOD SYSTEM STATUS ===" in result
            assert "=== END STATUS REPORT ===" in result
            assert "System Info: Error reading system data" in result
            assert "Calibration: Error reading calibration data" in result
            assert "IMU: Error reading sensor data" in result
            assert "Gait Status: No active gait" in result
            assert "Movement: Error reading servo data" in result
            assert "Leg Positions: Error reading position data" in result

    def test_gait_status_with_different_attributes(self, status_reporter, mock_hexapod):
        """Test gait status with different combinations of attributes."""
        mock_state = MagicMock()
        mock_hexapod.gait_generator.current_state = mock_state
        mock_hexapod.gait_generator.__class__.__name__ = "CustomGait"

        # Test with only phase
        mock_state.phase = "stance"
        del mock_state.swing_legs
        del mock_state.stance_legs
        del mock_state.dwell_time

        result = status_reporter._get_gait_status(mock_hexapod)

        assert "Gait Status:" in result
        assert "Type: CustomGait" in result
        assert "Phase: stance" in result
        assert "Swing Legs:" not in result
        assert "Stance Legs:" not in result
        assert "Dwell Time:" not in result

    def test_leg_positions_different_data_types(self, status_reporter):
        """Test leg positions with different data types."""
        hexapod = MagicMock()
        hexapod.current_leg_positions = [(100.0, 50.0, -80.0), (120.0, 60.0, -85.0)]
        hexapod.current_leg_angles = [(10.0, 20.0, 30.0), (12.0, 22.0, 32.0)]

        result = status_reporter._get_leg_positions_status(hexapod)

        assert "Leg Positions:" in result
        assert (
            "Leg 0: Pos( 100.0,   50.0,  -80.0) mm | Angles( 10.0°,  20.0°,  30.0°)"
            in result
        )
        assert (
            "Leg 1: Pos( 120.0,   60.0,  -85.0) mm | Angles( 12.0°,  22.0°,  32.0°)"
            in result
        )
        assert "Leg 2:" not in result  # Only 2 legs in this test

    def test_imu_status_precision(self, status_reporter, mock_hexapod):
        """Test IMU status number formatting precision."""
        # Test with very small and large numbers
        mock_hexapod.imu.get_acceleration.return_value = (0.001, -0.999, 9.999)
        mock_hexapod.imu.get_gyroscope.return_value = (123.456, -789.012, 0.000)
        mock_hexapod.imu.get_temperature.return_value = 25.123456

        result = status_reporter._get_imu_status(mock_hexapod)

        assert "Acceleration: X=+0.00 Y=-1.00 Z=+10.00 g" in result
        assert "Gyroscope: X=+123.46 Y=-789.01 Z=+0.00 °/s" in result
        assert "Temperature: 25.1°C" in result

    def test_movement_status_different_speeds(self, status_reporter):
        """Test movement status with different speed and acceleration values."""
        hexapod = MagicMock()
        hexapod._get_moving_state.return_value = True
        hexapod.speed = 100
        hexapod.accel = 75

        result = status_reporter._get_movement_status(hexapod)

        assert "State: Moving" in result
        assert "Servo Speed: 100%" in result
        assert "Servo Acceleration: 75%" in result
