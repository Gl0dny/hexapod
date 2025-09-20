"""
Unit tests for IMU sensor system.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from hexapod.robot.sensors.imu import Imu


class TestImu:
    """Test cases for Imu class."""
    
    @pytest.fixture
    def mock_icm20948(self):
        """Create a mock ICM20948 instance."""
        mock_imu = Mock()
        mock_imu.read_accelerometer_gyro_data.return_value = (0.01, 0.01, 1.01, 0.46, 1.14, -0.35)
        mock_imu.read_magnetometer_data.return_value = (-4.95, -6.30, 103.95)
        mock_imu.read_temperature.return_value = 33.11
        return mock_imu
    
    @pytest.fixture
    def imu(self, mock_icm20948):
        """Create an Imu instance with mocked ICM20948."""
        with patch('hexapod.robot.sensors.imu.ICM20948', return_value=mock_icm20948):
            return Imu()
    
    def test_init_default_parameters(self, mock_icm20948):
        """Test Imu initialization with default parameters."""
        with patch('hexapod.robot.sensors.imu.ICM20948', return_value=mock_icm20948) as mock_icm:
            imu = Imu()
            
            # Check that ICM20948 was instantiated
            mock_icm.assert_called_once()
            assert imu.imu == mock_icm20948
    
    def test_get_acceleration(self, imu, mock_icm20948):
        """Test reading accelerometer data."""
        # Test with default mock data
        ax, ay, az = imu.get_acceleration()
        
        # Check that the correct method was called
        mock_icm20948.read_accelerometer_gyro_data.assert_called_once()
        
        # Check that the correct values are returned
        assert ax == 0.01
        assert ay == 0.01
        assert az == 1.01
    
    def test_get_acceleration_custom_data(self, mock_icm20948):
        """Test reading accelerometer data with custom values."""
        # Set custom return values
        mock_icm20948.read_accelerometer_gyro_data.return_value = (1.5, -2.3, 9.8, 0.0, 0.0, 0.0)
        
        with patch('hexapod.robot.sensors.imu.ICM20948', return_value=mock_icm20948):
            imu = Imu()
            ax, ay, az = imu.get_acceleration()
            
            assert ax == 1.5
            assert ay == -2.3
            assert az == 9.8
    
    def test_get_gyroscope(self, imu, mock_icm20948):
        """Test reading gyroscope data."""
        # Test with default mock data
        gx, gy, gz = imu.get_gyroscope()
        
        # Check that the correct method was called
        mock_icm20948.read_accelerometer_gyro_data.assert_called_once()
        
        # Check that the correct values are returned
        assert gx == 0.46
        assert gy == 1.14
        assert gz == -0.35
    
    def test_get_gyroscope_custom_data(self, mock_icm20948):
        """Test reading gyroscope data with custom values."""
        # Set custom return values
        mock_icm20948.read_accelerometer_gyro_data.return_value = (0.0, 0.0, 0.0, 10.5, -15.2, 3.7)
        
        with patch('hexapod.robot.sensors.imu.ICM20948', return_value=mock_icm20948):
            imu = Imu()
            gx, gy, gz = imu.get_gyroscope()
            
            assert gx == 10.5
            assert gy == -15.2
            assert gz == 3.7
    
    def test_get_magnetometer(self, imu, mock_icm20948):
        """Test reading magnetometer data."""
        # Test with default mock data
        mx, my, mz = imu.get_magnetometer()
        
        # Check that the correct method was called
        mock_icm20948.read_magnetometer_data.assert_called_once()
        
        # Check that the correct values are returned
        assert mx == -4.95
        assert my == -6.30
        assert mz == 103.95
    
    def test_get_magnetometer_custom_data(self, mock_icm20948):
        """Test reading magnetometer data with custom values."""
        # Set custom return values
        mock_icm20948.read_magnetometer_data.return_value = (25.3, -18.7, 45.2)
        
        with patch('hexapod.robot.sensors.imu.ICM20948', return_value=mock_icm20948):
            imu = Imu()
            mx, my, mz = imu.get_magnetometer()
            
            assert mx == 25.3
            assert my == -18.7
            assert mz == 45.2
    
    def test_get_temperature(self, imu, mock_icm20948):
        """Test reading temperature data."""
        # Test with default mock data
        temp = imu.get_temperature()
        
        # Check that the correct method was called
        mock_icm20948.read_temperature.assert_called_once()
        
        # Check that the correct value is returned
        assert temp == 33.11
    
    def test_get_temperature_custom_data(self, mock_icm20948):
        """Test reading temperature data with custom values."""
        # Set custom return value
        mock_icm20948.read_temperature.return_value = 25.5
        
        with patch('hexapod.robot.sensors.imu.ICM20948', return_value=mock_icm20948):
            imu = Imu()
            temp = imu.get_temperature()
            
            assert temp == 25.5
    
    def test_read_all_sensor_data(self, imu, mock_icm20948):
        """Test reading all sensor data in sequence."""
        # Read all sensor data
        accel = imu.get_acceleration()
        gyro = imu.get_gyroscope()
        mag = imu.get_magnetometer()
        temp = imu.get_temperature()
        
        # Check that all methods were called
        assert mock_icm20948.read_accelerometer_gyro_data.call_count == 2  # Called for accel and gyro
        assert mock_icm20948.read_magnetometer_data.call_count == 1
        assert mock_icm20948.read_temperature.call_count == 1
        
        # Check that all data is returned correctly
        assert accel == (0.01, 0.01, 1.01)
        assert gyro == (0.46, 1.14, -0.35)
        assert mag == (-4.95, -6.30, 103.95)
        assert temp == 33.11
    
    def test_data_types(self, imu):
        """Test that all data methods return correct types."""
        # Test acceleration data types
        accel = imu.get_acceleration()
        assert isinstance(accel, tuple)
        assert len(accel) == 3
        assert all(isinstance(x, float) for x in accel)
        
        # Test gyroscope data types
        gyro = imu.get_gyroscope()
        assert isinstance(gyro, tuple)
        assert len(gyro) == 3
        assert all(isinstance(x, float) for x in gyro)
        
        # Test magnetometer data types
        mag = imu.get_magnetometer()
        assert isinstance(mag, tuple)
        assert len(mag) == 3
        assert all(isinstance(x, float) for x in mag)
        
        # Test temperature data type
        temp = imu.get_temperature()
        assert isinstance(temp, float)
    
    def test_error_handling_i2c_failure(self, mock_icm20948):
        """Test error handling for I2C failures."""
        # Mock I2C failure
        mock_icm20948.read_accelerometer_gyro_data.side_effect = Exception("I2C communication error")
        
        with patch('hexapod.robot.sensors.imu.ICM20948', return_value=mock_icm20948):
            imu = Imu()
            
            # Test that exceptions are propagated
            with pytest.raises(Exception, match="I2C communication error"):
                imu.get_acceleration()
    
    def test_error_handling_sensor_failure(self, mock_icm20948):
        """Test error handling for sensor failures."""
        # Mock sensor failure
        mock_icm20948.read_magnetometer_data.side_effect = Exception("Sensor read error")
        
        with patch('hexapod.robot.sensors.imu.ICM20948', return_value=mock_icm20948):
            imu = Imu()
            
            # Test that exceptions are propagated
            with pytest.raises(Exception, match="Sensor read error"):
                imu.get_magnetometer()
    
    def test_error_handling_temperature_failure(self, mock_icm20948):
        """Test error handling for temperature sensor failures."""
        # Mock temperature sensor failure
        mock_icm20948.read_temperature.side_effect = Exception("Temperature sensor error")
        
        with patch('hexapod.robot.sensors.imu.ICM20948', return_value=mock_icm20948):
            imu = Imu()
            
            # Test that exceptions are propagated
            with pytest.raises(Exception, match="Temperature sensor error"):
                imu.get_temperature()
    
    def test_multiple_reads_consistency(self, imu, mock_icm20948):
        """Test that multiple reads return consistent data."""
        # Read data multiple times
        accel1 = imu.get_acceleration()
        accel2 = imu.get_acceleration()
        
        # Check that the same data is returned
        assert accel1 == accel2
        
        # Check that the method was called the expected number of times
        assert mock_icm20948.read_accelerometer_gyro_data.call_count == 2
    
    def test_zero_values(self, mock_icm20948):
        """Test handling of zero values."""
        # Set zero values
        mock_icm20948.read_accelerometer_gyro_data.return_value = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        mock_icm20948.read_magnetometer_data.return_value = (0.0, 0.0, 0.0)
        mock_icm20948.read_temperature.return_value = 0.0
        
        with patch('hexapod.robot.sensors.imu.ICM20948', return_value=mock_icm20948):
            imu = Imu()
            
            accel = imu.get_acceleration()
            gyro = imu.get_gyroscope()
            mag = imu.get_magnetometer()
            temp = imu.get_temperature()
            
            assert accel == (0.0, 0.0, 0.0)
            assert gyro == (0.0, 0.0, 0.0)
            assert mag == (0.0, 0.0, 0.0)
            assert temp == 0.0
    
    def test_negative_values(self, mock_icm20948):
        """Test handling of negative values."""
        # Set negative values
        mock_icm20948.read_accelerometer_gyro_data.return_value = (-1.5, -2.3, -9.8, -10.5, -15.2, -3.7)
        mock_icm20948.read_magnetometer_data.return_value = (-25.3, -18.7, -45.2)
        mock_icm20948.read_temperature.return_value = -10.5
        
        with patch('hexapod.robot.sensors.imu.ICM20948', return_value=mock_icm20948):
            imu = Imu()
            
            accel = imu.get_acceleration()
            gyro = imu.get_gyroscope()
            mag = imu.get_magnetometer()
            temp = imu.get_temperature()
            
            assert accel == (-1.5, -2.3, -9.8)
            assert gyro == (-10.5, -15.2, -3.7)
            assert mag == (-25.3, -18.7, -45.2)
            assert temp == -10.5
    
    def test_large_values(self, mock_icm20948):
        """Test handling of large values."""
        # Set large values
        mock_icm20948.read_accelerometer_gyro_data.return_value = (100.0, 200.0, 300.0, 1000.0, 2000.0, 3000.0)
        mock_icm20948.read_magnetometer_data.return_value = (1000.0, 2000.0, 3000.0)
        mock_icm20948.read_temperature.return_value = 150.0
        
        with patch('hexapod.robot.sensors.imu.ICM20948', return_value=mock_icm20948):
            imu = Imu()
            
            accel = imu.get_acceleration()
            gyro = imu.get_gyroscope()
            mag = imu.get_magnetometer()
            temp = imu.get_temperature()
            
            assert accel == (100.0, 200.0, 300.0)
            assert gyro == (1000.0, 2000.0, 3000.0)
            assert mag == (1000.0, 2000.0, 3000.0)
            assert temp == 150.0
    
    def test_float_precision(self, mock_icm20948):
        """Test handling of high precision float values."""
        # Set high precision values
        mock_icm20948.read_accelerometer_gyro_data.return_value = (0.123456789, 0.987654321, 1.000000001, 0.000000001, 0.000000002, 0.000000003)
        mock_icm20948.read_magnetometer_data.return_value = (0.000000001, 0.000000002, 0.000000003)
        mock_icm20948.read_temperature.return_value = 25.123456789
        
        with patch('hexapod.robot.sensors.imu.ICM20948', return_value=mock_icm20948):
            imu = Imu()
            
            accel = imu.get_acceleration()
            gyro = imu.get_gyroscope()
            mag = imu.get_magnetometer()
            temp = imu.get_temperature()
            
            assert accel == (0.123456789, 0.987654321, 1.000000001)
            assert gyro == (0.000000001, 0.000000002, 0.000000003)
            assert mag == (0.000000001, 0.000000002, 0.000000003)
            assert temp == 25.123456789
