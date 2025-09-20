"""
Unit tests for calibration system.
"""
import pytest
import json
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from hexapod.robot.calibration import Calibration


class TestCalibration:
    """Test cases for Calibration class."""
    
    @pytest.fixture
    def mock_hexapod(self):
        """Create a mock Hexapod instance."""
        hexapod = Mock()
        hexapod.legs = []
        
        # Create 6 mock legs with joints
        for i in range(6):
            leg = Mock()
            leg.coxa = Mock()
            leg.femur = Mock()
            leg.tibia = Mock()
            leg.coxa_params = {"servo_min": 3968, "servo_max": 8000}
            leg.femur_params = {"servo_min": 3968, "servo_max": 8000}
            leg.tibia_params = {"servo_min": 3968, "servo_max": 8000}
            
            # Set up joint properties
            leg.coxa.servo_min = 3968
            leg.coxa.servo_max = 8000
            leg.coxa.angle_min = -90.0
            leg.coxa.angle_max = 90.0
            leg.coxa.invert = False
            
            leg.femur.servo_min = 3968
            leg.femur.servo_max = 8000
            leg.femur.angle_min = -90.0
            leg.femur.angle_max = 90.0
            leg.femur.invert = False
            
            leg.tibia.servo_min = 3968
            leg.tibia.servo_max = 8000
            leg.tibia.angle_min = -90.0
            leg.tibia.angle_max = 90.0
            leg.tibia.invert = False
            
            hexapod.legs.append(leg)
        
        # Set up hexapod parameters
        hexapod.femur_params = {"angle_max": 90.0}
        hexapod.tibia_params = {"angle_max": 90.0}
        
        # Mock hexapod methods
        hexapod.move_to_position = Mock()
        hexapod.wait_until_motion_complete = Mock()
        hexapod.move_leg_angles = Mock()
        
        return hexapod
    
    @pytest.fixture
    def calibration_data_path(self, tmp_path):
        """Create a temporary calibration data path."""
        return tmp_path / "calibration.json"
    
    @pytest.fixture
    def calibration(self, mock_hexapod, calibration_data_path):
        """Create a Calibration instance."""
        return Calibration(mock_hexapod, calibration_data_path)
    
    def test_init_default_parameters(self, mock_hexapod, calibration_data_path):
        """Test Calibration initialization with default parameters."""
        cal = Calibration(mock_hexapod, calibration_data_path)
        
        assert cal.hexapod == mock_hexapod
        assert cal.calibration_data_path == calibration_data_path
        assert cal.input_handler is None
        assert cal.status == {i: "not_calibrated" for i in range(6)}
        assert "calibration_init" in cal.calibration_positions
        assert len(cal.calibration_positions["calibration_init"]) == 6
    
    def test_init_custom_parameters(self, mock_hexapod, calibration_data_path):
        """Test Calibration initialization with custom parameters."""
        cal = Calibration(mock_hexapod, calibration_data_path)
        
        # Check calibration positions are set correctly
        for i, position in enumerate(cal.calibration_positions["calibration_init"]):
            assert position == (0.0, 90.0, 90.0)
    
    def test_get_calibration_status(self, calibration):
        """Test getting calibration status."""
        status = calibration.get_calibration_status()
        
        assert status == {i: "not_calibrated" for i in range(6)}
        assert len(status) == 6
    
    def test_calibrate_servo_valid(self, calibration):
        """Test calibrating valid servo."""
        leg_index = 0
        joint_name = "coxa"
        servo_min = 4000
        servo_max = 8000
        
        calibration._calibrate_servo(leg_index, joint_name, servo_min, servo_max)
        
        # Check that joint parameters were updated
        leg = calibration.hexapod.legs[leg_index]
        assert leg.coxa_params["servo_min"] == servo_min
        assert leg.coxa_params["servo_max"] == servo_max
        leg.coxa.update_calibration.assert_called_once_with(servo_min, servo_max)
    
    def test_calibrate_servo_invalid_leg_index(self, calibration, caplog):
        """Test calibrating servo with invalid leg index."""
        calibration._calibrate_servo(10, "coxa", 4000, 8000)
        
        assert "Invalid leg index. Must be between 0 and 5" in caplog.text
    
    def test_calibrate_servo_invalid_joint(self, calibration, caplog):
        """Test calibrating servo with invalid joint name."""
        calibration._calibrate_servo(0, "invalid_joint", 4000, 8000)
        
        assert "Invalid joint name. Choose 'coxa', 'femur', or 'tibia'" in caplog.text
    
    def test_load_calibration_valid_data(self, calibration):
        """Test loading valid calibration data."""
        calibration_data = {
            "leg_0": {
                "coxa": {"servo_min": 4000, "servo_max": 8000},
                "femur": {"servo_min": 4000, "servo_max": 8000},
                "tibia": {"servo_min": 4000, "servo_max": 8000}
            }
        }
        
        with patch('pathlib.Path.open', mock_open(read_data=json.dumps(calibration_data))):
            with patch.object(calibration, '_calibrate_servo') as mock_calibrate:
                calibration.load_calibration()
                
                # Check that calibration was called for each joint
                assert mock_calibrate.call_count == 3
    
    def test_load_calibration_invalid_data(self, calibration, caplog):
        """Test loading invalid calibration data."""
        calibration_data = {
            "leg_0": {
                "coxa": {"servo_min": 100, "servo_max": 200},  # Invalid range
                "femur": {"servo_min": 4000, "servo_max": 8000},
                "tibia": {"servo_min": 4000, "servo_max": 8000}
            }
        }
        
        with patch('pathlib.Path.open', mock_open(read_data=json.dumps(calibration_data))):
            with patch.object(calibration, '_calibrate_servo') as mock_calibrate:
                calibration.load_calibration()
                
                # Check that warning was logged for invalid data
                assert "Calibration values for leg 0 coxa are invalid" in caplog.text
                # Check that default values were used
                assert mock_calibrate.call_count == 3
    
    def test_load_calibration_file_not_found(self, calibration, caplog):
        """Test loading calibration when file doesn't exist."""
        with patch('pathlib.Path.open', side_effect=FileNotFoundError):
            calibration.load_calibration()
            
            assert "not found. Using default calibration values" in caplog.text
    
    def test_load_calibration_json_decode_error(self, calibration, caplog):
        """Test loading calibration with invalid JSON."""
        with patch('pathlib.Path.open', mock_open(read_data="invalid json")):
            calibration.load_calibration()
            
            assert "Error decoding" in caplog.text
    
    def test_save_calibration_data(self, calibration):
        """Test saving calibration data."""
        with patch('pathlib.Path.open', mock_open()) as mock_file:
            calibration._save_calibration()
            
            # Check that file was opened for writing
            mock_file.assert_called_once_with('w')
            # Check that JSON was written
            mock_file().write.assert_called()
    
    def test_save_calibration_io_error(self, calibration, caplog):
        """Test saving calibration with IO error."""
        with patch('pathlib.Path.open', side_effect=IOError("Permission denied")):
            calibration._save_calibration()
            
            assert "Failed to save calibration data" in caplog.text
    
    def test_validate_servo_input_valid(self, calibration):
        """Test validating valid servo input."""
        assert calibration._validate_servo_input("servo_min", 1000) == True
        assert calibration._validate_servo_input("servo_max", 1500) == True
    
    def test_validate_servo_input_invalid_min(self, calibration):
        """Test validating invalid servo min input."""
        assert calibration._validate_servo_input("servo_min", 100) == False
        assert calibration._validate_servo_input("servo_min", 3000) == False
    
    def test_validate_servo_input_invalid_max(self, calibration):
        """Test validating invalid servo max input."""
        assert calibration._validate_servo_input("servo_max", 100) == False
        assert calibration._validate_servo_input("servo_max", 3000) == False
    
    def test_validate_servo_input_inverted(self, calibration):
        """Test validating servo input with inverted logic."""
        # The validation logic is the same for inverted and non-inverted servos
        assert calibration._validate_servo_input("servo_min", 1500, invert=True) == True
        assert calibration._validate_servo_input("servo_max", 1500, invert=True) == True
        assert calibration._validate_servo_input("servo_min", 100, invert=True) == False
        assert calibration._validate_servo_input("servo_max", 3000, invert=True) == False
    
    
    def test_error_handling_calibration_failure(self, calibration, caplog):
        """Test error handling for calibration failures."""
        # Test with invalid leg index
        calibration._calibrate_servo(10, "coxa", 1000, 1500)
        assert "Invalid leg index" in caplog.text
        
        # Test with invalid joint name
        calibration._calibrate_servo(0, "invalid", 1000, 1500)
        assert "Invalid joint name" in caplog.text
    
    def test_error_handling_file_io_failure(self, calibration, caplog):
        """Test error handling for file I/O failures."""
        # Test loading with file not found
        with patch('pathlib.Path.open', side_effect=FileNotFoundError):
            calibration.load_calibration()
            assert "not found" in caplog.text
        
        # Test saving with IO error
        with patch('pathlib.Path.open', side_effect=IOError("Permission denied")):
            calibration._save_calibration()
            assert "Failed to save" in caplog.text
