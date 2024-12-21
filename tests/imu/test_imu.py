# from unittest.mock import patch
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/')))

from imu import Imu

def test_get_acceleration(mocker):
    mock_icm = mocker.patch('imu.imu.ICM20948')
    mock_instance = mock_icm.return_value
    mock_instance.read_accelerometer_gyro_data.return_value = (0.01, 0.01, 1.01, 0.46, 1.14, -0.35)
    
    imu = Imu()
    ax, ay, az = imu.get_acceleration()
    assert ax == 0.01
    assert ay == 0.01
    assert az == 1.01

def test_get_gyroscope(mocker):
    mock_icm = mocker.patch('imu.imu.ICM20948')
    mock_instance = mock_icm.return_value
    mock_instance.read_accelerometer_gyro_data.return_value = (0.01, 0.01, 1.01, 0.46, 1.14, -0.35)
    
    imu = Imu()
    gx, gy, gz = imu.get_gyroscope()
    assert gx == 0.46
    assert gy == 1.14
    assert gz == -0.35

def test_get_magnetometer(mocker):
    mock_icm = mocker.patch('imu.imu.ICM20948')
    mock_instance = mock_icm.return_value
    mock_instance.read_magnetometer_data.return_value = (-4.95, -6.30, 103.95)
    
    imu = Imu()
    mx, my, mz = imu.get_magnetometer()
    assert mx == -4.95
    assert my == -6.30
    assert mz == 103.95

def test_get_temperature(mocker):
    mock_icm = mocker.patch('imu.imu.ICM20948')
    mock_instance = mock_icm.return_value
    mock_instance.read_temperature.return_value = 33.11
    
    imu = Imu()
    temp = imu.get_temperature()
    assert temp == 33.11