import pytest
import sys
import os
import serial
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/')))
from maestro import MaestroUART

@pytest.fixture
def maestro_fixture(mocker):
    mock_serial = mocker.patch('serial.Serial')
    device = '/dev/ttyS0'
    baudrate = 9600
    maestro = MaestroUART(device, baudrate)
    return mock_serial, maestro

def test_init(maestro_fixture):
    mock_serial, maestro = maestro_fixture
    mock_serial.assert_called_with('/dev/ttyS0')
    instance = mock_serial.return_value
    assert instance.baudrate == 9600
    assert instance.bytesize == serial.EIGHTBITS
    assert instance.parity == serial.PARITY_NONE
    assert instance.stopbits == serial.STOPBITS_ONE
    assert instance.xonxoff == False
    assert instance.timeout == 0

@pytest.mark.parametrize("code, byte", [
    (1, b'\x01'),
    (2, b'\x02'),
    (4, b'\x04'),
    (8, b'\x08'),
    (16, b'\x10'),
    (32, b'\x20'),
    (64, b'\x40'),
    (128, b'\x80'),
])
def test_get_error(maestro_fixture, code, byte):
    _, maestro = maestro_fixture
    maestro.ser.read.side_effect = [byte, b'\x00']
    error_code = maestro.get_error()
    maestro.ser.write.assert_called_with(bytes([0xAA, 0x0C, 0xA1 & 0x7F]))
    assert error_code == code

def test_get_error_no_error(maestro_fixture):
    _, maestro = maestro_fixture
    maestro.ser.read.side_effect = [b'\x00', b'\x00']
    error_code = maestro.get_error()
    maestro.ser.write.assert_called_with(bytes([0xAA, 0x0C, 0xA1 & 0x7F]))
    assert error_code == 0

def test_get_position(maestro_fixture):
    _, maestro = maestro_fixture
    channel = 0
    maestro.ser.read.side_effect = [b'\x10', b'\x27']  # Mock position bytes
    position = maestro.get_position(channel)
    maestro.ser.write.assert_called_with(bytes([0xAA, 0x0C, 0x90 & 0x7F, channel]))
    expected_position = int.from_bytes(b'\x10', byteorder='big') + (int.from_bytes(b'\x27', byteorder='big') << 8)
    assert position == expected_position

def test_set_speed(maestro_fixture):
    _, maestro = maestro_fixture
    channel = 0
    speed = 32
    maestro.set_speed(channel, speed)
    command = bytes([
        0xAA, 0x0C, 0x87 & 0x7F, channel,
        speed & 0x7F, (speed >> 7) & 0x7F
    ])
    maestro.ser.write.assert_called_with(command)

def test_set_acceleration(maestro_fixture):
    _, maestro = maestro_fixture
    channel = 0
    accel = 5
    maestro.set_acceleration(channel, accel)
    command = bytes([
        0xAA, 0x0C, 0x89 & 0x7F, channel,
        accel & 0x7F, (accel >> 7) & 0x7F
    ])
    maestro.ser.write.assert_called_with(command)

def test_set_target(maestro_fixture):
    _, maestro = maestro_fixture
    channel = 0
    target = 6000
    maestro.set_target(channel, target)
    command = bytes([
        0xAA, 0x0C, 0x84 & 0x7F, channel,
        target & 0x7F, (target >> 7) & 0x7F
    ])
    maestro.ser.write.assert_called_with(command)

def test_go_home(maestro_fixture):
    _, maestro = maestro_fixture
    maestro.go_home()
    command = bytes([0xAA, 0x0C, 0x22 & 0x7F])
    maestro.ser.write.assert_called_with(command)

def test_get_moving_state(maestro_fixture):
    _, maestro = maestro_fixture
    maestro.ser.read.return_value = b'\x00'  # Mock moving state as 0
    moving_state = maestro.get_moving_state()
    command = bytes([0xAA, 0x0C, 0x93 & 0x7F])
    maestro.ser.write.assert_called_with(command)
    assert moving_state == 0

def test_close(maestro_fixture):
    _, maestro = maestro_fixture
    maestro.close()
    maestro.ser.close.assert_called_once()