import pytest
import sys
import os
import serial
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/')))
from maestro import MaestroUART
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/')))  # ...existing code...

def test_init(mocker):
    mock_serial = mocker.patch('serial.Serial')
    device = '/dev/ttyS0'
    baudrate = 9600
    maestro = MaestroUART(device, baudrate)
    mock_serial.assert_called_with(device)
    instance = mock_serial.return_value
    assert instance.baudrate == baudrate
    assert instance.bytesize == serial.EIGHTBITS
    assert instance.parity == serial.PARITY_NONE
    assert instance.stopbits == serial.STOPBITS_ONE
    assert instance.xonxoff == False
    assert instance.timeout == 0

def test_get_error(mocker):
    mock_serial = mocker.patch('serial.Serial')
    maestro = MaestroUART()
    error_codes = {
        1: b'\x01',   # Error bit 0
        2: b'\x02',   # Error bit 1
        4: b'\x04',   # Error bit 2
        8: b'\x08',   # Error bit 3
        16: b'\x10',  # Error bit 4
        32: b'\x20',  # Error bit 5
        64: b'\x40',  # Error bit 6
        128: b'\x80', # Error bit 7
    }

    for code, byte in error_codes.items():
        maestro.ser.read.side_effect = [byte, b'\x00']
        error_code = maestro.get_error()
        maestro.ser.write.assert_called_with(bytes([0xAA, 0x0C, 0xA1 & 0x7F]))
        assert error_code == code

    # Test no error
    maestro.ser.read.side_effect = [b'\x00', b'\x00']
    error_code = maestro.get_error()
    maestro.ser.write.assert_called_with(bytes([0xAA, 0x0C, 0xA1 & 0x7F]))
    assert error_code == 0

def test_get_position(mocker):
    mock_serial = mocker.patch('serial.Serial')
    maestro = MaestroUART()
    channel = 0
    maestro.ser.read.side_effect = [b'\x10', b'\x27']  # Mock position bytes
    position = maestro.get_position(channel)
    maestro.ser.write.assert_called_with(bytes([0xAA, 0x0C, 0x90 & 0x7F, channel]))
    expected_position = int.from_bytes(b'\x10', byteorder='big') + (int.from_bytes(b'\x27', byteorder='big') << 8)
    assert position == expected_position

def test_set_speed(mocker):
    mock_serial = mocker.patch('serial.Serial')
    maestro = MaestroUART()
    channel = 0
    speed = 32
    maestro.set_speed(channel, speed)
    command = bytes([
        0xAA, 0x0C, 0x87 & 0x7F, channel,
        speed & 0x7F, (speed >> 7) & 0x7F
    ])
    maestro.ser.write.assert_called_with(command)

def test_set_acceleration(mocker):
    mock_serial = mocker.patch('serial.Serial')
    maestro = MaestroUART()
    channel = 0
    accel = 5
    maestro.set_acceleration(channel, accel)
    command = bytes([
        0xAA, 0x0C, 0x89 & 0x7F, channel,
        accel & 0x7F, (accel >> 7) & 0x7F
    ])
    maestro.ser.write.assert_called_with(command)

def test_set_target(mocker):
    mock_serial = mocker.patch('serial.Serial')
    maestro = MaestroUART()
    channel = 0
    target = 6000
    maestro.set_target(channel, target)
    command = bytes([
        0xAA, 0x0C, 0x84 & 0x7F, channel,
        target & 0x7F, (target >> 7) & 0x7F
    ])
    maestro.ser.write.assert_called_with(command)

def test_go_home(mocker):
    mock_serial = mocker.patch('serial.Serial')
    maestro = MaestroUART()
    maestro.go_home()
    command = bytes([0xAA, 0x0C, 0x22 & 0x7F])
    maestro.ser.write.assert_called_with(command)

def test_get_moving_state(mocker):
    mock_serial = mocker.patch('serial.Serial')
    maestro = MaestroUART()
    maestro.ser.read.return_value = b'\x00'  # Mock moving state as 0
    moving_state = maestro.get_moving_state()
    command = bytes([0xAA, 0x0C, 0x93 & 0x7F])
    maestro.ser.write.assert_called_with(command)
    assert moving_state == 0

def test_close(mocker):
    mock_serial = mocker.patch('serial.Serial')
    maestro = MaestroUART()
    maestro.close()
    maestro.ser.close.assert_called_once()