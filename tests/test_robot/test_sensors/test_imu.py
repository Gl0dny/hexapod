import pytest
from unittest.mock import Mock, patch
import importlib.util


@pytest.fixture
def imu_module():
    """Import the real imu module with mocked dependencies."""
    spec = importlib.util.spec_from_file_location(
        "imu_module", 
        "/Users/gl0dny/workspace/hexapod/hexapod/robot/sensors/imu.py"
    )
    imu_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(imu_module)
    return imu_module


class TestImu:
    """Test the Imu class from sensors/imu.py"""

    def test_imu_class_exists(self, imu_module):
        """Test that Imu class exists."""
        assert hasattr(imu_module, 'Imu')
        assert callable(imu_module.Imu)

    def test_imu_initialization(self, imu_module):
        """Test Imu initialization."""
        with patch('hexapod.robot.sensors.imu.icm20948') as mock_icm20948:
            imu = imu_module.Imu()
            
            # Verify initialization - check that the object was created successfully
            assert imu is not None

    def test_imu_methods_exist(self, imu_module):
        """Test that Imu has required methods."""
        Imu = imu_module.Imu
        
        # Test that required methods exist
        required_methods = ['get_acceleration', 'get_gyroscope', 'get_magnetometer', 'get_temperature']
        
        for method_name in required_methods:
            assert hasattr(Imu, method_name), f"Imu should have {method_name} method"

    def test_get_acceleration_method(self, imu_module):
        """Test get_acceleration method."""
        with patch('hexapod.robot.sensors.imu.icm20948') as mock_icm20948:
            imu = imu_module.Imu()
            
            # Test get_acceleration method exists and can be called
            assert hasattr(imu, 'get_acceleration')
            assert callable(imu.get_acceleration)

    def test_get_gyroscope_method(self, imu_module):
        """Test get_gyroscope method."""
        with patch('hexapod.robot.sensors.imu.icm20948') as mock_icm20948:
            imu = imu_module.Imu()
            
            # Test get_gyroscope method exists and can be called
            assert hasattr(imu, 'get_gyroscope')
            assert callable(imu.get_gyroscope)

    def test_get_magnetometer_method(self, imu_module):
        """Test get_magnetometer method."""
        with patch('hexapod.robot.sensors.imu.icm20948') as mock_icm20948:
            imu = imu_module.Imu()
            
            # Test get_magnetometer method exists and can be called
            assert hasattr(imu, 'get_magnetometer')
            assert callable(imu.get_magnetometer)

    def test_get_temperature_method(self, imu_module):
        """Test get_temperature method."""
        with patch('hexapod.robot.sensors.imu.icm20948') as mock_icm20948:
            imu = imu_module.Imu()
            
            # Test get_temperature method exists and can be called
            assert hasattr(imu, 'get_temperature')
            assert callable(imu.get_temperature)
