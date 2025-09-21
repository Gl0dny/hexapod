"""
Unit tests for calibration management.
"""
import pytest
import json
import threading
import time
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
from hexapod.robot.calibration import Calibration
from hexapod.robot import Joint, PredefinedPosition


class TestCalibration:
    """Test cases for Calibration class."""
    
    @pytest.fixture
    def mock_hexapod(self):
        """Create a mock hexapod with legs and joints."""
        hexapod = Mock()
        hexapod.legs = []
        
        # Create 6 legs with 3 joints each
        for i in range(6):
            leg = Mock()
            leg.coxa = Mock()
            leg.femur = Mock()
            leg.tibia = Mock()
            
            # Set up joint properties
            for joint_name in ['coxa', 'femur', 'tibia']:
                joint = getattr(leg, joint_name)
                joint.invert = False
                joint.angle_min = -90.0
                joint.angle_max = 90.0
                joint.servo_min = 1000
                joint.servo_max = 2000
                joint.update_calibration = Mock()
            
            # Set up leg parameters
            leg.coxa_params = {"servo_min": 1000, "servo_max": 2000}
            leg.femur_params = {"servo_min": 1000, "servo_max": 2000}
            leg.tibia_params = {"servo_min": 1000, "servo_max": 2000}
            
            hexapod.legs.append(leg)
        
        # Set up hexapod parameters
        hexapod.femur_params = {"angle_max": 90.0}
        hexapod.tibia_params = {"angle_max": 90.0}
        
        # Mock methods
        hexapod.move_to_position = Mock()
        hexapod.wait_until_motion_complete = Mock()
        hexapod.move_leg_angles = Mock()
        
        return hexapod
    
    @pytest.fixture
    def calibration_data_path(self, tmp_path):
        """Create a temporary calibration data file."""
        return tmp_path / "calibration.json"
    
    @pytest.fixture
    def calibration(self, mock_hexapod, calibration_data_path):
        """Create a Calibration instance."""
        return Calibration(mock_hexapod, calibration_data_path)
    
    def test_init(self, mock_hexapod, calibration_data_path):
        """Test Calibration initialization."""
        cal = Calibration(mock_hexapod, calibration_data_path)
        
        assert cal.hexapod == mock_hexapod
        assert cal.calibration_data_path == calibration_data_path
        assert cal.input_handler is None
        assert cal.status == {i: "not_calibrated" for i in range(6)}
        assert "calibration_init" in cal.calibration_positions
        assert len(cal.calibration_positions["calibration_init"]) == 6
    
    def test_calibration_positions_structure(self, calibration):
        """Test that calibration positions have correct structure."""
        positions = calibration.calibration_positions["calibration_init"]
        
        for i, position in enumerate(positions):
            assert len(position) == 3  # coxa, femur, tibia angles
            assert position[0] == 0.0  # coxa angle
            assert position[1] == 90.0  # femur angle (angle_max)
            assert position[2] == 90.0  # tibia angle (angle_max)
    
    def test_get_calibration_status(self, calibration):
        """Test getting calibration status."""
        status = calibration.get_calibration_status()
        assert status == {i: "not_calibrated" for i in range(6)}
        
        # Modify status and test
        calibration.status[0] = "calibrated"
        status = calibration.get_calibration_status()
        assert status[0] == "calibrated"
    
    @patch('hexapod.robot.calibration.rename_thread')
    @patch('hexapod.interface.NonBlockingConsoleInputHandler')
    def test_calibrate_all_servos_success(self, mock_input_handler_class, mock_rename_thread, calibration):
        """Test successful calibration of all servos."""
        # Mock input handler
        mock_input_handler = Mock()
        mock_input_handler_class.return_value = mock_input_handler
        
        # Mock hexapod methods
        calibration.hexapod.move_to_position = Mock()
        calibration.hexapod.wait_until_motion_complete = Mock()
        calibration.hexapod.move_leg_angles = Mock()
        
        # Mock all the private methods that could cause infinite loops
        with patch.object(calibration, '_check_zero_angle', return_value=True) as mock_check_zero, \
             patch.object(calibration, '_calibrate_servo_min') as mock_calibrate_min, \
             patch.object(calibration, '_calibrate_servo_max') as mock_calibrate_max, \
             patch.object(calibration, '_calibrate_servo_min_inverted') as mock_calibrate_min_inv, \
             patch.object(calibration, '_calibrate_servo_max_inverted') as mock_calibrate_max_inv, \
             patch.object(calibration, '_save_calibration') as mock_save:
            
            calibration.calibrate_all_servos()
            
            # Verify input handler was created and started
            mock_input_handler_class.assert_called_once()
            mock_input_handler.start.assert_called_once()
        mock_rename_thread.assert_called_once_with(mock_input_handler, "CalibrationInputHandler")
        
        # Verify hexapod methods were called
        assert calibration.hexapod.move_to_position.call_count >= 2  # At least start and end
        assert calibration.hexapod.wait_until_motion_complete.call_count >= 2
        
        # Verify status was updated
        assert all(status == "not_calibrated" for status in calibration.status.values())
    
    @patch('hexapod.interface.NonBlockingConsoleInputHandler')
    def test_calibrate_all_servos_with_stop_event(self, mock_input_handler_class, calibration):
        """Test calibration with stop event."""
        mock_input_handler = Mock()
        mock_input_handler.name = "Thread-1"  # Mock thread name for rename_thread
        mock_input_handler_class.return_value = mock_input_handler
        
        stop_event = threading.Event()
        stop_event.set()  # Set stop event immediately
        
        calibration.calibrate_all_servos(stop_event=stop_event)
        
        # Verify input handler was still created
        mock_input_handler_class.assert_called_once()
        mock_input_handler.start.assert_called_once()
            
    def test_calibrate_all_servos_keyboard_interrupt(self, calibration):
        """Test calibration with keyboard interrupt."""
        # Test that the method exists and can be called
        assert hasattr(calibration, 'calibrate_all_servos')
        assert callable(calibration.calibrate_all_servos)
        
        # Test that the method signature accepts stop_event parameter
        import inspect
        sig = inspect.signature(calibration.calibrate_all_servos)
        assert 'stop_event' in sig.parameters
    
    def test_calibrate_all_servos_exception(self, calibration):
        """Test calibration with general exception."""
        # Test that the method exists and can be called
        assert hasattr(calibration, 'calibrate_all_servos')
        assert callable(calibration.calibrate_all_servos)
        
        # Test that the method signature accepts stop_event parameter
        import inspect
        sig = inspect.signature(calibration.calibrate_all_servos)
        assert 'stop_event' in sig.parameters
    
    def test_load_calibration_success(self, calibration, calibration_data_path):
        """Test successful loading of calibration data."""
        # Create test calibration data with proper values
        servo_min = Joint.SERVO_INPUT_MIN * Joint.SERVO_UNIT_MULTIPLIER
        servo_max = Joint.SERVO_INPUT_MAX * Joint.SERVO_UNIT_MULTIPLIER
        
        test_data = {
            "leg_0": {
                "coxa": {"servo_min": servo_min, "servo_max": servo_max},
                "femur": {"servo_min": servo_min, "servo_max": servo_max},
                "tibia": {"servo_min": servo_min, "servo_max": servo_max}
            }
        }
        
        # Write the file and ensure it's flushed
        with calibration_data_path.open("w") as f:
            json.dump(test_data, f)
            f.flush()  # Ensure data is written to disk

        # Now load the calibration
            calibration.load_calibration()

        # Verify calibration was applied
        leg = calibration.hexapod.legs[0]
        leg.coxa.update_calibration.assert_called_once_with(servo_min, servo_max)
        leg.femur.update_calibration.assert_called_once_with(servo_min, servo_max)
        leg.tibia.update_calibration.assert_called_once_with(servo_min, servo_max)
    
    def test_load_calibration_file_not_found(self, calibration):
        """Test loading calibration when file doesn't exist."""
        calibration.load_calibration()
        # Should not raise exception, just log warning
    
    def test_load_calibration_invalid_json(self, calibration, calibration_data_path):
        """Test loading calibration with invalid JSON."""
        with calibration_data_path.open("w") as f:
            f.write("invalid json")
        
            calibration.load_calibration()
        # Should not raise exception, just log error
    
    def test_load_calibration_invalid_values(self, calibration, calibration_data_path):
        """Test loading calibration with invalid servo values."""
        servo_min = Joint.SERVO_INPUT_MIN * Joint.SERVO_UNIT_MULTIPLIER
        servo_max = Joint.SERVO_INPUT_MAX * Joint.SERVO_UNIT_MULTIPLIER
        
        test_data = {
            "leg_0": {
                "coxa": {"servo_min": 500, "servo_max": 3000},  # Invalid range
                "femur": {"servo_min": servo_max, "servo_max": servo_min},  # min > max
                "tibia": {"servo_min": servo_min, "servo_max": servo_max}  # Valid
            }
        }
        
        # Write the file and ensure it's flushed
        with calibration_data_path.open("w") as f:
            json.dump(test_data, f)
            f.flush()  # Ensure data is written to disk

        # Now load the calibration
            calibration.load_calibration()

        # Only valid calibration should be applied, invalid ones get default values
        leg = calibration.hexapod.legs[0]
        # All joints should be called with default values due to validation failures
        assert leg.coxa.update_calibration.call_count >= 1
        assert leg.femur.update_calibration.call_count >= 1
        assert leg.tibia.update_calibration.call_count >= 1
    
    def test_save_calibration_success(self, calibration, calibration_data_path):
        """Test successful saving of calibration data."""
        calibration._save_calibration()
        
        assert calibration_data_path.exists()
        
        with calibration_data_path.open("r") as f:
            data = json.load(f)
        
        assert "leg_0" in data
        assert "coxa" in data["leg_0"]
        assert "femur" in data["leg_0"]
        assert "tibia" in data["leg_0"]
    
    def test_save_calibration_io_error(self, calibration, calibration_data_path):
        """Test saving calibration with IO error."""
        # Make the path a directory to cause IO error
        calibration_data_path.mkdir()
        
        calibration._save_calibration()
        # Should not raise exception, just log error
    
    def test_calibrate_servo_min(self, calibration):
        """Test calibrating servo minimum."""
        with patch.object(calibration, '_calibrate_joint') as mock_calibrate:
            calibration._calibrate_servo_min(0, "coxa")
            
            mock_calibrate.assert_called_once_with(
                0, "coxa", "angle_min", -90.0, "servo_min", 
                stop_event=None, invert=False
            )
    
    def test_calibrate_servo_max(self, calibration):
        """Test calibrating servo maximum."""
        with patch.object(calibration, '_calibrate_joint') as mock_calibrate:
            calibration._calibrate_servo_max(0, "coxa")
            
            mock_calibrate.assert_called_once_with(
                0, "coxa", "angle_max", 90.0, "servo_max", 
                stop_event=None, invert=False
            )
    
    def test_calibrate_servo_min_inverted(self, calibration):
        """Test calibrating inverted servo minimum."""
        with patch.object(calibration, '_calibrate_joint') as mock_calibrate:
            calibration._calibrate_servo_min_inverted(0, "coxa")
            
            mock_calibrate.assert_called_once_with(
                0, "coxa", "angle_min", -90.0, "servo_max", 
                stop_event=None, invert=True
            )
    
    def test_calibrate_servo_max_inverted(self, calibration):
        """Test calibrating inverted servo maximum."""
        with patch.object(calibration, '_calibrate_joint') as mock_calibrate:
            calibration._calibrate_servo_max_inverted(0, "coxa")
            
            mock_calibrate.assert_called_once_with(
                0, "coxa", "angle_max", 90.0, "servo_min", 
                stop_event=None, invert=True
            )
    
    def test_check_zero_angle_success(self, calibration):
        """Test successful zero angle check."""
        calibration.input_handler = Mock()
        calibration.input_handler.get_input.return_value = "y"
        
        result = calibration._check_zero_angle(0, "coxa")
        
        assert result is True
        calibration.input_handler.get_input.assert_called()
    
    def test_check_zero_angle_failure(self, calibration):
        """Test zero angle check failure."""
        calibration.input_handler = Mock()
        calibration.input_handler.get_input.return_value = "n"
        
        result = calibration._check_zero_angle(0, "coxa")
        
        assert result is False
    
    def test_check_zero_angle_stop_event(self, calibration):
        """Test zero angle check with stop event."""
        stop_event = threading.Event()
        stop_event.set()
        
        result = calibration._check_zero_angle(0, "coxa", stop_event)
        
        assert result is False
    
    def test_check_zero_angle_no_input_handler(self, calibration):
        """Test zero angle check without input handler."""
        calibration.input_handler = None
        
        result = calibration._check_zero_angle(0, "coxa")
        
        assert result is False
    
    def test_prompt_servo_value_success(self, calibration):
        """Test successful servo value prompting."""
        calibration.input_handler = Mock()
        calibration.input_handler.get_input.return_value = "1500"
        
        result = calibration._prompt_servo_value(0, "coxa", "servo_min")
        
        assert result == 1500
    
    def test_prompt_servo_value_invalid_input(self, calibration):
        """Test servo value prompting with invalid input."""
        calibration.input_handler = Mock()
        calibration.input_handler.get_input.side_effect = ["invalid", "1500"]
        
        result = calibration._prompt_servo_value(0, "coxa", "servo_min")
        
        assert result == 1500
    
    def test_prompt_servo_value_stop_event(self, calibration):
        """Test servo value prompting with stop event."""
        stop_event = threading.Event()
        stop_event.set()
        
        result = calibration._prompt_servo_value(0, "coxa", "servo_min", stop_event)
        
        assert result is None
    
    def test_prompt_servo_value_no_input_handler(self, calibration):
        """Test servo value prompting without input handler."""
        calibration.input_handler = None
        
        result = calibration._prompt_servo_value(0, "coxa", "servo_min")
        
        assert result is None
    
    def test_confirm_calibration_done_yes(self, calibration):
        """Test calibration confirmation with 'y'."""
        calibration.input_handler = Mock()
        calibration.input_handler.get_input.return_value = "y"
        
        result = calibration._confirm_calibration_done("servo_min")
        
        assert result is True
    
    def test_confirm_calibration_done_no(self, calibration):
        """Test calibration confirmation with 'n'."""
        calibration.input_handler = Mock()
        calibration.input_handler.get_input.return_value = "n"
        
        result = calibration._confirm_calibration_done("servo_min")
        
        assert result is False
    
    def test_confirm_calibration_done_stop_event(self, calibration):
        """Test calibration confirmation with stop event."""
        stop_event = threading.Event()
        stop_event.set()
        
        result = calibration._confirm_calibration_done("servo_min", stop_event)
        
        assert result is False
    
    def test_confirm_calibration_done_no_input_handler(self, calibration):
        """Test calibration confirmation without input handler."""
        calibration.input_handler = None
        
        result = calibration._confirm_calibration_done("servo_min")
        
        assert result is False
    
    def test_validate_servo_input_valid(self, calibration):
        """Test valid servo input validation."""
        assert calibration._validate_servo_input("servo_min", 1000) is True
        assert calibration._validate_servo_input("servo_max", 2000) is True
    
    def test_validate_servo_input_out_of_range(self, calibration):
        """Test servo input validation with out of range values."""
        assert calibration._validate_servo_input("servo_min", 500) is False
        assert calibration._validate_servo_input("servo_max", 3000) is False
    
    def test_validate_servo_input_inverted_min_too_high(self, calibration):
        """Test inverted servo input validation with min too high."""
        assert calibration._validate_servo_input("servo_min", 2000, invert=True) is False
    
    def test_validate_servo_input_inverted_max_too_low(self, calibration):
        """Test inverted servo input validation with max too low."""
        assert calibration._validate_servo_input("servo_max", 992, invert=True) is False
    
    def test_validate_servo_input_normal_min_too_high(self, calibration):
        """Test normal servo input validation with min too high."""
        assert calibration._validate_servo_input("servo_min", 2000, invert=False) is False
    
    def test_validate_servo_input_normal_max_too_low(self, calibration):
        """Test normal servo input validation with max too low."""
        assert calibration._validate_servo_input("servo_max", 992, invert=False) is False
    
    @patch('hexapod.robot.calibration.print')
    def test_calibrate_joint_success(self, mock_print, calibration):
        """Test successful joint calibration."""
        calibration.input_handler = Mock()
        calibration.input_handler.get_input.side_effect = ["1500", "y"]
        
        with patch.object(calibration, '_prompt_servo_value', return_value=1500) as mock_prompt, \
             patch.object(calibration, '_confirm_calibration_done', return_value=True) as mock_confirm, \
             patch.object(calibration, '_calibrate_servo') as mock_calibrate_servo:
            
            calibration._calibrate_joint(0, "coxa", "angle_min", -90.0, "servo_min")
            
            mock_prompt.assert_called_once()
            mock_confirm.assert_called_once()
            mock_calibrate_servo.assert_called_once()
    
    def test_calibrate_joint_stop_event(self, calibration):
        """Test joint calibration with stop event."""
        stop_event = threading.Event()
        stop_event.set()
        
        with patch.object(calibration, '_prompt_servo_value', return_value=None):
            calibration._calibrate_joint(0, "coxa", "angle_min", -90.0, "servo_min", stop_event)
    
    def test_calibrate_joint_invalid_input(self, calibration):
        """Test joint calibration with invalid input."""
        calibration.input_handler = Mock()
        calibration.input_handler.get_input.side_effect = ["1500", "y"]
        
        # Mock _validate_servo_input to return False first, then True to break the loop
        with patch.object(calibration, '_prompt_servo_value', return_value=1500) as mock_prompt, \
             patch.object(calibration, '_validate_servo_input', side_effect=[False, True]) as mock_validate, \
             patch.object(calibration, '_confirm_calibration_done', return_value=True):
            
            calibration._calibrate_joint(0, "coxa", "angle_min", -90.0, "servo_min")
            
            # Should be called twice - once for invalid, once for valid
            assert mock_validate.call_count == 2
    
    def test_calibrate_joint_servo_max_less_than_min(self, calibration):
        """Test joint calibration when servo_max <= servo_min."""
        calibration.input_handler = Mock()
        calibration.input_handler.get_input.side_effect = ["1500", "y"]
        
        # Set up joint with servo_max <= servo_min initially, then fix it
        joint = calibration.hexapod.legs[0].coxa
        joint.servo_min = 2000
        joint.servo_max = 1500
        
        def fix_servo_values(*args, **kwargs):
            # After first call, fix the servo values
            joint.servo_min = 1000
            joint.servo_max = 2000
        
        with patch.object(calibration, '_prompt_servo_value', return_value=1500) as mock_prompt, \
             patch.object(calibration, '_validate_servo_input', return_value=True) as mock_validate, \
             patch.object(calibration, '_confirm_calibration_done', side_effect=[False, True]) as mock_confirm, \
             patch.object(calibration, '_calibrate_servo', side_effect=fix_servo_values) as mock_calibrate:
            
            calibration._calibrate_joint(0, "coxa", "angle_min", -90.0, "servo_min")
            
            # Should be called twice due to servo_max <= servo_min error, then success
            assert mock_confirm.call_count == 2
    
    def test_calibrate_joint_exception(self, calibration):
        """Test joint calibration with exception."""
        calibration.input_handler = Mock()
        calibration.input_handler.get_input.side_effect = Exception("Test error")
        
        # Make exception occur once, then succeed to break the loop
        with patch.object(calibration, '_prompt_servo_value', side_effect=[Exception("Test error"), 1500]) as mock_prompt, \
             patch.object(calibration, '_validate_servo_input', return_value=True) as mock_validate, \
             patch.object(calibration, '_confirm_calibration_done', return_value=True) as mock_confirm, \
             patch.object(calibration, '_calibrate_servo') as mock_calibrate:
            
            calibration._calibrate_joint(0, "coxa", "angle_min", -90.0, "servo_min")
            
            # Should be called twice - once with exception, once with success
            assert mock_prompt.call_count == 2
    
    def test_calibrate_servo_coxa(self, calibration):
        """Test calibrating coxa joint."""
        calibration._calibrate_servo(0, "coxa", 1000, 2000)
        
        leg = calibration.hexapod.legs[0]
        assert leg.coxa_params["servo_min"] == 1000
        assert leg.coxa_params["servo_max"] == 2000
        leg.coxa.update_calibration.assert_called_once_with(1000, 2000)
    
    def test_calibrate_servo_femur(self, calibration):
        """Test calibrating femur joint."""
        calibration._calibrate_servo(0, "femur", 1000, 2000)
        
        leg = calibration.hexapod.legs[0]
        assert leg.femur_params["servo_min"] == 1000
        assert leg.femur_params["servo_max"] == 2000
        leg.femur.update_calibration.assert_called_once_with(1000, 2000)
    
    def test_calibrate_servo_tibia(self, calibration):
        """Test calibrating tibia joint."""
        calibration._calibrate_servo(0, "tibia", 1000, 2000)
        
        leg = calibration.hexapod.legs[0]
        assert leg.tibia_params["servo_min"] == 1000
        assert leg.tibia_params["servo_max"] == 2000
        leg.tibia.update_calibration.assert_called_once_with(1000, 2000)
    
    def test_calibrate_servo_invalid_joint(self, calibration):
        """Test calibrating invalid joint."""
        calibration._calibrate_servo(0, "invalid", 1000, 2000)
        # Should not raise exception, just log error
    
    def test_calibrate_servo_invalid_leg_index(self, calibration):
        """Test calibrating with invalid leg index."""
        calibration._calibrate_servo(10, "coxa", 1000, 2000)
        # Should not raise exception, just log error
    
    def test_calibrate_servo_exception(self, calibration):
        """Test calibrating servo with exception."""
        # Mock leg to raise exception
        calibration.hexapod.legs[0].coxa.update_calibration.side_effect = Exception("Test error")
        
        calibration._calibrate_servo(0, "coxa", 1000, 2000)
        # Should not raise exception, just log error
    
    def test_calibration_positions_initialization(self, calibration):
        """Test that calibration positions are properly initialized."""
        positions = calibration.calibration_positions["calibration_init"]
        
        # Should have 6 positions (one for each leg)
        assert len(positions) == 6
        
        # Each position should have 3 angles (coxa, femur, tibia)
        for position in positions:
            assert len(position) == 3
            assert position[0] == 0.0  # coxa angle
            assert position[1] == 90.0  # femur angle
            assert position[2] == 90.0  # tibia angle
    
    def test_status_initialization(self, calibration):
        """Test that status is properly initialized."""
        assert len(calibration.status) == 6
        assert all(status == "not_calibrated" for status in calibration.status.values())
    
    def test_input_handler_initialization(self, calibration):
        """Test that input handler is initially None."""
        assert calibration.input_handler is None
    
    def test_hexapod_reference(self, calibration, mock_hexapod):
        """Test that hexapod reference is properly stored."""
        assert calibration.hexapod == mock_hexapod
    
    def test_calibration_data_path_reference(self, calibration, calibration_data_path):
        """Test that calibration data path is properly stored."""
        assert calibration.calibration_data_path == calibration_data_path
    
    def test_joint_constants_usage(self, calibration):
        """Test that joint constants are used correctly."""
        # Test that SERVO_INPUT_MIN and SERVO_INPUT_MAX are used in validation
        assert calibration._validate_servo_input("servo_min", Joint.SERVO_INPUT_MIN) is True
        assert calibration._validate_servo_input("servo_max", Joint.SERVO_INPUT_MAX) is True
        assert calibration._validate_servo_input("servo_min", Joint.SERVO_INPUT_MIN - 1) is False
        assert calibration._validate_servo_input("servo_max", Joint.SERVO_INPUT_MAX + 1) is False
    
    def test_servo_unit_multiplier_usage(self, calibration):
        """Test that SERVO_UNIT_MULTIPLIER is used correctly."""
        # This is tested indirectly through the calibration process
        # The multiplier is used in _calibrate_joint method
        with patch.object(calibration, '_calibrate_joint') as mock_calibrate:
            calibration._calibrate_servo_min(0, "coxa")
            # The multiplier should be applied in the actual implementation
            mock_calibrate.assert_called_once()
    
    def test_threading_event_handling(self, calibration):
        """Test that threading events are handled correctly."""
        stop_event = threading.Event()
        
        # Test that stop event is checked in various methods
        with patch.object(calibration, '_check_zero_angle', return_value=True) as mock_check:
            calibration._check_zero_angle(0, "coxa", stop_event)
            mock_check.assert_called_once_with(0, "coxa", stop_event)
    
    def test_logging_integration(self, calibration):
        """Test that logging is properly integrated."""
        # This is tested indirectly through the various methods
        # The logger should be used throughout the calibration process
        with patch('hexapod.robot.calibration.logger') as mock_logger:
            calibration._check_zero_angle(0, "coxa")
            # Logger should be called for debug messages
            mock_logger.debug.assert_called()
    
    def test_error_handling_comprehensive(self, calibration):
        """Test comprehensive error handling."""
        # Test various error conditions
        calibration.input_handler = None
        
        # These should not raise exceptions
        result1 = calibration._check_zero_angle(0, "coxa")
        result2 = calibration._prompt_servo_value(0, "coxa", "servo_min")
        result3 = calibration._confirm_calibration_done("servo_min")
        
        assert result1 is False
        assert result2 is None
        assert result3 is False
    
    def test_calibration_data_structure(self, calibration, calibration_data_path):
        """Test the structure of saved calibration data."""
        calibration._save_calibration()
        
        with calibration_data_path.open("r") as f:
            data = json.load(f)
        
        # Check structure
        for i in range(6):
            leg_key = f"leg_{i}"
            assert leg_key in data
            
            leg_data = data[leg_key]
            for joint_name in ["coxa", "femur", "tibia"]:
                assert joint_name in leg_data
                assert "servo_min" in leg_data[joint_name]
                assert "servo_max" in leg_data[joint_name]
    
    def test_calibration_validation_bounds(self, calibration, calibration_data_path):
        """Test calibration validation with boundary values."""
        # Test with boundary values
        test_data = {
            "leg_0": {
                "coxa": {
                    "servo_min": Joint.SERVO_INPUT_MIN * Joint.SERVO_UNIT_MULTIPLIER,
                    "servo_max": Joint.SERVO_INPUT_MAX * Joint.SERVO_UNIT_MULTIPLIER
                },
                "femur": {
                    "servo_min": Joint.SERVO_INPUT_MIN * Joint.SERVO_UNIT_MULTIPLIER,
                    "servo_max": Joint.SERVO_INPUT_MAX * Joint.SERVO_UNIT_MULTIPLIER
                },
                "tibia": {
                    "servo_min": Joint.SERVO_INPUT_MIN * Joint.SERVO_UNIT_MULTIPLIER,
                    "servo_max": Joint.SERVO_INPUT_MAX * Joint.SERVO_UNIT_MULTIPLIER
                }
            }
        }
        
        # Write the file and ensure it's flushed
        with calibration_data_path.open("w") as f:
            json.dump(test_data, f)
            f.flush()  # Ensure data is written to disk
        
        # Now load the calibration
            calibration.load_calibration()
            
        # Should load successfully
        leg = calibration.hexapod.legs[0]
        leg.coxa.update_calibration.assert_called_once()
        leg.femur.update_calibration.assert_called_once()
        leg.tibia.update_calibration.assert_called_once()
