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

class TestMaestroUART:
    def test_init(self, maestro_fixture):
        # Test initialization of MaestroUART
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
    def test_get_error(self, maestro_fixture, code, byte):
        # Test get_error method with different error codes
        _, maestro = maestro_fixture
        maestro.ser.read.side_effect = [byte, b'\x00']
        error_code = maestro.get_error()
        maestro.ser.write.assert_called_with(bytes([
            0xAA, 0x0C, 0xA1 & 0x7F  # COMMAND_START, device number, COMMAND_GET_ERROR
        ]))
        assert error_code == code

    def test_get_error_no_error(self, maestro_fixture):
        # Test get_error method with no error
        _, maestro = maestro_fixture
        maestro.ser.read.side_effect = [b'\x00', b'\x00']
        error_code = maestro.get_error()
        maestro.ser.write.assert_called_with(bytes([
            0xAA, 0x0C, 0xA1 & 0x7F  # COMMAND_START, device number, COMMAND_GET_ERROR
        ]))
        assert error_code == 0

    def test_get_position(self, maestro_fixture):
        # Test get_position method
        _, maestro = maestro_fixture
        channel = 0
        maestro.ser.read.side_effect = [b'\x10', b'\x27']  # Mock position bytes
        position = maestro.get_position(channel)
        maestro.ser.write.assert_called_with(bytes([
            0xAA, 0x0C, 0x90 & 0x7F, channel  # COMMAND_START, device number, COMMAND_GET_POSITION, channel
        ]))
        expected_position = int.from_bytes(b'\x10', byteorder='big') + (int.from_bytes(b'\x27', byteorder='big') << 8)
        assert position == expected_position

    def test_set_speed(self, maestro_fixture):
        # Test set_speed method
        _, maestro = maestro_fixture
        channel = 0
        speed = 32
        maestro.set_speed(channel, speed)
        expected_command = bytes([
            0xAA, 0x0C, 0x87 & 0x7F, channel,  # COMMAND_START, device number, COMMAND_SET_SPEED, channel
            speed & 0x7F, (speed >> 7) & 0x7F   # speed low byte, speed high byte
        ])
        maestro.ser.write.assert_called_with(expected_command)

    def test_set_acceleration(self, maestro_fixture):
        # Test set_acceleration method
        _, maestro = maestro_fixture
        channel = 0
        accel = 5
        maestro.set_acceleration(channel, accel)
        expected_command = bytes([
            0xAA, 0x0C, 0x89 & 0x7F, channel,  # COMMAND_START, device number, COMMAND_SET_ACCELERATION, channel
            accel & 0x7F, (accel >> 7) & 0x7F # accel low byte, accel high byte
        ])
        maestro.ser.write.assert_called_with(expected_command)

    def test_set_target(self, maestro_fixture):
        # Test set_target method
        _, maestro = maestro_fixture
        channel = 0
        target = 6000
        maestro.set_target(channel, target)
        expected_command = bytes([
            0xAA, 0x0C, 0x84 & 0x7F, channel,  # COMMAND_START, device number, COMMAND_SET_TARGET, channel
            target & 0x7F, (target >> 7) & 0x7F # target low byte, target high byte
        ])
        maestro.ser.write.assert_called_with(expected_command)

    def test_go_home(self, maestro_fixture):
        # Test go_home method
        _, maestro = maestro_fixture
        maestro.go_home()
        command = bytes([
            0xAA, 0x0C, 0x22 & 0x7F  # COMMAND_START, device number, COMMAND_GO_HOME
        ])
        maestro.ser.write.assert_called_with(command)

    def test_get_moving_state(self, maestro_fixture):
        # Test get_moving_state method
        _, maestro = maestro_fixture
        maestro.ser.read.return_value = b'\x00'  # Mock moving state as 0
        moving_state = maestro.get_moving_state()
        command = bytes([
            0xAA, 0x0C, 0x93 & 0x7F  # COMMAND_START, device number, COMMAND_GET_MOVING_STATE
        ])
        maestro.ser.write.assert_called_with(command)
        assert moving_state == 0

    def test_get_moving_state_empty_response(self, maestro_fixture, mocker):
        # Test get_moving_state method with empty response
        _, maestro = maestro_fixture
        maestro.ser.read.return_value = b''
        maestro.ser.write.return_value = None
        result = maestro.get_moving_state()
        assert result is None

    def test_close(self, maestro_fixture):
        # Test close method
        _, maestro = maestro_fixture
        maestro.close()
        maestro.ser.close.assert_called_once()

    def test_set_multiple_targets(self, maestro_fixture):
        # Test set_multiple_targets method
        _, maestro = maestro_fixture
        targets = [(3, 0), (4, 6000)]
        maestro.set_multiple_targets(targets)
        expected_command = bytes([
            0xAA, 0x0C, 0x1F,  # COMMAND_START, device number, COMMAND_SET_MULTIPLE_TARGETS
            2, 3,              # Number of targets and first channel
            0 & 0x7F, (0 >> 7) & 0x7F,      # Target for channel 3
            6000 & 0x7F, (6000 >> 7) & 0x7F  # Target for channel 4
        ])
        maestro.ser.write.assert_called_with(expected_command)

    def test_set_multiple_targets_non_sequential(self, maestro_fixture):
        # Test set_multiple_targets method with non-sequential channels
        _, maestro = maestro_fixture
        targets = [(3, 6000), (5, 7000)]  # Non-sequential channels
        with pytest.raises(ValueError) as exc_info:
            maestro.set_multiple_targets(targets)
        assert "Channels are not sequential." in str(exc_info.value)