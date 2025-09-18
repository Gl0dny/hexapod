import pytest
from unittest.mock import Mock, patch
import sys


class TestImu:
    """Unit tests for the Imu class - focused on essential functionality."""
    
    @pytest.fixture
    def mock_icm20948(self):
        """Create a mock ICM20948 instance with realistic sensor data."""
        mock_icm = Mock()
        mock_icm.read_accelerometer_gyro_data.return_value = (0.01, 0.01, 1.01, 0.46, 1.14, -0.35)
        mock_icm.read_magnetometer_data.return_value = (-4.95, -6.30, 103.95)
        mock_icm.read_temperature.return_value = 33.11
        return mock_icm
    
    @pytest.fixture
    def imu_class(self):
        """Import the real Imu class with mocked dependencies."""
        with patch.dict('sys.modules', {'icm20948': Mock()}):
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "imu_module", 
                "/Users/gl0dny/workspace/hexapod/hexapod/robot/sensors/imu.py"
            )
            imu_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(imu_module)
            return imu_module.Imu
    
    def test_get_acceleration(self, imu_class, mock_icm20948):
        """Test acceleration data retrieval and tuple unpacking."""
        with patch.object(imu_class, '__init__', return_value=None):
            imu = imu_class()
            imu.imu = mock_icm20948
            
            ax, ay, az = imu.get_acceleration()
            
            assert ax == 0.01
            assert ay == 0.01
            assert az == 1.01
            mock_icm20948.read_accelerometer_gyro_data.assert_called_once()
    
    def test_get_gyroscope(self, imu_class, mock_icm20948):
        """Test gyroscope data retrieval and tuple unpacking."""
        with patch.object(imu_class, '__init__', return_value=None):
            imu = imu_class()
            imu.imu = mock_icm20948
            
            gx, gy, gz = imu.get_gyroscope()
            
            assert gx == 0.46
            assert gy == 1.14
            assert gz == -0.35
            mock_icm20948.read_accelerometer_gyro_data.assert_called_once()
    
    def test_get_magnetometer(self, imu_class, mock_icm20948):
        """Test magnetometer data retrieval."""
        with patch.object(imu_class, '__init__', return_value=None):
            imu = imu_class()
            imu.imu = mock_icm20948
            
            mx, my, mz = imu.get_magnetometer()
            
            assert mx == -4.95
            assert my == -6.30
            assert mz == 103.95
            mock_icm20948.read_magnetometer_data.assert_called_once()
    
    def test_get_temperature(self, imu_class, mock_icm20948):
        """Test temperature data retrieval."""
        with patch.object(imu_class, '__init__', return_value=None):
            imu = imu_class()
            imu.imu = mock_icm20948
            
            temp = imu.get_temperature()
            
            assert temp == 33.11
            mock_icm20948.read_temperature.assert_called_once()
    
    def test_initialization(self, imu_class):
        """Test that Imu initializes with ICM20948 instance."""
        mock_icm = Mock()
        with patch.object(imu_class, '__init__', return_value=None):
            imu = imu_class()
            imu.imu = mock_icm
            
            assert imu.imu == mock_icm
    
    def test_data_extraction_with_different_values(self, imu_class):
        """Test data extraction logic with different sensor values."""
        mock_icm = Mock()
        mock_icm.read_accelerometer_gyro_data.return_value = (1.0, 2.0, 3.0, 4.0, 5.0, 6.0)
        mock_icm.read_magnetometer_data.return_value = (10.0, 20.0, 30.0)
        mock_icm.read_temperature.return_value = 25.0
        
        with patch.object(imu_class, '__init__', return_value=None):
            imu = imu_class()
            imu.imu = mock_icm
            
            # Test acceleration (first 3 values)
            ax, ay, az = imu.get_acceleration()
            assert (ax, ay, az) == (1.0, 2.0, 3.0)
            
            # Test gyroscope (last 3 values)
            gx, gy, gz = imu.get_gyroscope()
            assert (gx, gy, gz) == (4.0, 5.0, 6.0)
            
            # Test magnetometer (direct return)
            mx, my, mz = imu.get_magnetometer()
            assert (mx, my, mz) == (10.0, 20.0, 30.0)
            
            # Test temperature (direct return)
            temp = imu.get_temperature()
            assert temp == 25.0
    
    def test_return_types(self, imu_class, mock_icm20948):
        """Test that methods return correct types."""
        with patch.object(imu_class, '__init__', return_value=None):
            imu = imu_class()
            imu.imu = mock_icm20948
            
            # Test return types
            accel = imu.get_acceleration()
            gyro = imu.get_gyroscope()
            mag = imu.get_magnetometer()
            temp = imu.get_temperature()
            
            assert isinstance(accel, tuple) and len(accel) == 3
            assert isinstance(gyro, tuple) and len(gyro) == 3
            assert isinstance(mag, tuple) and len(mag) == 3
            assert isinstance(temp, float)
            
            # Test all values are floats
            assert all(isinstance(x, float) for x in accel)
            assert all(isinstance(x, float) for x in gyro)
            assert all(isinstance(x, float) for x in mag)