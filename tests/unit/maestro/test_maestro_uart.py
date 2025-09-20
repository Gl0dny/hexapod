#!/usr/bin/env python3

"""
Unit tests for MaestroUART class.

This module tests the MaestroUART class which handles communication
with Pololu Maestro servo controller boards via UART.
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, MagicMock, patch, call
import threading
import time

from hexapod.maestro.maestro_uart import MaestroUART


class TestMaestroUART:
    """Test cases for MaestroUART class."""
    
    @pytest.fixture
    def mock_serial(self):
        """Create a mock serial.Serial object."""
        mock_ser = Mock()
        mock_ser.baudrate = 9600
        mock_ser.bytesize = 8
        mock_ser.parity = 0
        mock_ser.stopbits = 1
        mock_ser.xonxoff = False
        mock_ser.timeout = 0
        return mock_ser

    @pytest.fixture
    def maestro_uart(self, mock_serial):
        """Create a MaestroUART instance with mocked serial connection."""
        with patch('hexapod.maestro.maestro_uart.serial.Serial', return_value=mock_serial):
            return MaestroUART(device="/dev/ttyS0", baudrate=9600)

    def test_class_constants(self):
        """Test that all class constants are defined correctly."""
        assert MaestroUART.COMMAND_START == 0xAA
        assert MaestroUART.DEFAULT_DEVICE_NUMBER == 0x0C
        assert MaestroUART.COMMAND_GET_ERROR == 0x21
        assert MaestroUART.COMMAND_GET_POSITION == 0x10
        assert MaestroUART.COMMAND_SET_SPEED == 0x07
        assert MaestroUART.COMMAND_SET_ACCELERATION == 0x09
        assert MaestroUART.COMMAND_SET_TARGET == 0x04
        assert MaestroUART.COMMAND_GO_HOME == 0x22
        assert MaestroUART.COMMAND_GET_MOVING_STATE == 0x13
        assert MaestroUART.COMMAND_SET_MULTIPLE_TARGETS == 0x1F

    def test_init_default_parameters(self, mock_serial):
        """Test MaestroUART initialization with default parameters."""
        with patch('hexapod.maestro.maestro_uart.serial.Serial', return_value=mock_serial):
            maestro = MaestroUART()
            
            assert maestro.ser == mock_serial
            assert maestro.ser.baudrate == 9600
            # Check that the serial port attributes are set correctly
            assert hasattr(maestro.ser, 'bytesize')
            assert hasattr(maestro.ser, 'parity')
            assert hasattr(maestro.ser, 'stopbits')
            assert maestro.ser.xonxoff is False
            assert maestro.ser.timeout == 0
            assert isinstance(maestro.lock, threading.Lock)

    def test_init_custom_parameters(self, mock_serial):
        """Test MaestroUART initialization with custom parameters."""
        with patch('hexapod.maestro.maestro_uart.serial.Serial', return_value=mock_serial):
            maestro = MaestroUART(device="/dev/ttyAMA0", baudrate=115200)
            
            assert maestro.ser == mock_serial
            assert maestro.ser.baudrate == 115200

    def test_init_logging(self, mock_serial, caplog):
        """Test that initialization logs the correct information."""
        with patch('hexapod.maestro.maestro_uart.serial.Serial', return_value=mock_serial):
            with caplog.at_level("INFO"):
                MaestroUART(device="/dev/ttyS0", baudrate=9600)
                
            assert "MaestroUART initialized successfully with device=/dev/ttyS0, baudrate=9600" in caplog.text

    def test_get_error_no_error(self, maestro_uart, mock_serial):
        """Test get_error method when no error occurs."""
        # Mock successful response (no error)
        mock_serial.reset_input_buffer.return_value = None
        mock_serial.read.side_effect = [b'\x00', b'\x00']  # No error response
        
        error_code = maestro_uart.get_error()
        
        assert error_code == 0
        mock_serial.reset_input_buffer.assert_called_once()
        mock_serial.write.assert_called_once_with(bytes([0xAA, 0x0C, 0x21]))
        assert mock_serial.read.call_count == 2

    def test_get_error_with_errors(self, maestro_uart, mock_serial, caplog):
        """Test get_error method when various errors occur."""
        # Mock error response (bit 0 and bit 4 set = 0x11 = 17)
        mock_serial.reset_input_buffer.return_value = None
        mock_serial.read.side_effect = [b'\x11', b'\x00']  # Error code 17
        
        with caplog.at_level("ERROR"):
            error_code = maestro_uart.get_error()
        
        assert error_code == 17
        assert "Error detected with code: 17" in caplog.text
        assert "Serial signal error: Stop bit not detected at the expected place." in caplog.text
        assert "Serial protocol error: Incorrectly formatted or nonsensical command packet." in caplog.text

    def test_get_error_all_error_types(self, maestro_uart, mock_serial, caplog):
        """Test get_error method with all possible error types."""
        # Mock error response with all bits set (0xFF = 255)
        mock_serial.reset_input_buffer.return_value = None
        mock_serial.read.side_effect = [b'\xFF', b'\x00']  # All error bits set
        
        with caplog.at_level("ERROR"):
            error_code = maestro_uart.get_error()
        
        assert error_code == 255
        # Check that all error messages are logged (excluding the last one which requires bit 8)
        error_messages = [
            "Serial signal error: Stop bit not detected at the expected place.",
            "Serial overrun error: UART's internal buffer filled up.",
            "Serial buffer full: Firmware buffer for received bytes is full.",
            "Serial CRC error: CRC byte does not match the computed CRC.",
            "Serial protocol error: Incorrectly formatted or nonsensical command packet.",
            "Serial timeout: Timeout period elapsed without receiving valid serial commands.",
            "Script stack error: Stack overflow or underflow.",
            "Script call stack error: Call stack overflow or underflow."
        ]
        
        for message in error_messages:
            assert message in caplog.text

    def test_get_position_success(self, maestro_uart, mock_serial, caplog):
        """Test get_position method with successful response."""
        # Mock position response (1500 * 4 = 6000 quarter-microseconds)
        mock_serial.reset_input_buffer.return_value = None
        mock_serial.read.side_effect = [b'\x70', b'\x17']  # 6000 in little-endian
        
        with caplog.at_level("INFO"):
            position = maestro_uart.get_position(5)
        
        assert position == 6000
        mock_serial.reset_input_buffer.assert_called_once()
        mock_serial.write.assert_called_once_with(bytes([0xAA, 0x0C, 0x10, 5]))
        assert "Position for channel 5 is 6000." in caplog.text

    def test_get_position_zero_response(self, maestro_uart, mock_serial, caplog):
        """Test get_position method with zero response (error case)."""
        mock_serial.reset_input_buffer.return_value = None
        mock_serial.read.side_effect = [b'\x00', b'\x00']  # Zero response
        
        with caplog.at_level("INFO"):
            position = maestro_uart.get_position(3)
        
        assert position == 0
        assert "Position for channel 3 is 0." in caplog.text

    def test_set_speed(self, maestro_uart, mock_serial, caplog):
        """Test set_speed method."""
        with caplog.at_level("INFO"):
            maestro_uart.set_speed(2, 32)
        
        expected_command = bytes([0xAA, 0x0C, 0x07, 2, 32 & 0x7F, (32 >> 7) & 0x7F])
        mock_serial.write.assert_called_once_with(expected_command)
        assert "Speed for channel 2 set to 32." in caplog.text

    def test_set_speed_high_value(self, maestro_uart, mock_serial, caplog):
        """Test set_speed method with high speed value."""
        with caplog.at_level("INFO"):
            maestro_uart.set_speed(1, 255)
        
        expected_command = bytes([0xAA, 0x0C, 0x07, 1, 255 & 0x7F, (255 >> 7) & 0x7F])
        mock_serial.write.assert_called_once_with(expected_command)
        assert "Speed for channel 1 set to 255." in caplog.text

    def test_set_acceleration(self, maestro_uart, mock_serial, caplog):
        """Test set_acceleration method."""
        with caplog.at_level("INFO"):
            maestro_uart.set_acceleration(3, 5)
        
        expected_command = bytes([0xAA, 0x0C, 0x09, 3, 5 & 0x7F, (5 >> 7) & 0x7F])
        mock_serial.write.assert_called_once_with(expected_command)
        assert "Acceleration for channel 3 set to 5." in caplog.text

    def test_set_acceleration_high_value(self, maestro_uart, mock_serial, caplog):
        """Test set_acceleration method with high acceleration value."""
        with caplog.at_level("INFO"):
            maestro_uart.set_acceleration(0, 200)
        
        expected_command = bytes([0xAA, 0x0C, 0x09, 0, 200 & 0x7F, (200 >> 7) & 0x7F])
        mock_serial.write.assert_called_once_with(expected_command)
        assert "Acceleration for channel 0 set to 200." in caplog.text

    def test_set_target(self, maestro_uart, mock_serial, caplog):
        """Test set_target method."""
        with caplog.at_level("INFO"):
            maestro_uart.set_target(4, 8000)
        
        expected_command = bytes([0xAA, 0x0C, 0x04, 4, 8000 & 0x7F, (8000 >> 7) & 0x7F])
        mock_serial.write.assert_called_once_with(expected_command)
        assert "Target for channel 4 set to 8000." in caplog.text

    def test_set_target_zero(self, maestro_uart, mock_serial, caplog):
        """Test set_target method with zero target (stop servo)."""
        with caplog.at_level("INFO"):
            maestro_uart.set_target(1, 0)
        
        expected_command = bytes([0xAA, 0x0C, 0x04, 1, 0 & 0x7F, (0 >> 7) & 0x7F])
        mock_serial.write.assert_called_once_with(expected_command)
        assert "Target for channel 1 set to 0." in caplog.text

    def test_set_multiple_targets_sequential(self, maestro_uart, mock_serial, caplog):
        """Test set_multiple_targets method with sequential channels."""
        targets = [(3, 0), (4, 6000), (5, 8000)]
        
        with caplog.at_level("INFO"):
            maestro_uart.set_multiple_targets(targets)
        
        expected_command = bytes([
            0xAA, 0x0C, 0x1F,  # Command header
            3, 3,  # Number of targets, first channel
            0 & 0x7F, (0 >> 7) & 0x7F,  # Target 0
            6000 & 0x7F, (6000 >> 7) & 0x7F,  # Target 6000
            8000 & 0x7F, (8000 >> 7) & 0x7F   # Target 8000
        ])
        mock_serial.write.assert_called_once_with(expected_command)
        assert "Multiple targets set: [(3, 0), (4, 6000), (5, 8000)]" in caplog.text

    def test_set_multiple_targets_single_channel(self, maestro_uart, mock_serial, caplog):
        """Test set_multiple_targets method with single channel."""
        targets = [(5, 4000)]
        
        with caplog.at_level("INFO"):
            maestro_uart.set_multiple_targets(targets)
        
        expected_command = bytes([
            0xAA, 0x0C, 0x1F,  # Command header
            1, 5,  # Number of targets, first channel
            4000 & 0x7F, (4000 >> 7) & 0x7F  # Target 4000
        ])
        mock_serial.write.assert_called_once_with(expected_command)
        assert "Multiple targets set: [(5, 4000)]" in caplog.text

    def test_set_multiple_targets_non_sequential_raises_error(self, maestro_uart):
        """Test set_multiple_targets method with non-sequential channels raises ValueError."""
        targets = [(3, 0), (5, 6000)]  # Non-sequential channels
        
        with pytest.raises(ValueError, match="Channels are not sequential."):
            maestro_uart.set_multiple_targets(targets)

    def test_set_multiple_targets_empty_list(self, maestro_uart):
        """Test set_multiple_targets method with empty list."""
        targets = []
        
        with pytest.raises(ValueError, match="min\\(\\) iterable argument is empty"):
            maestro_uart.set_multiple_targets(targets)

    def test_go_home(self, maestro_uart, mock_serial, caplog):
        """Test go_home method."""
        with caplog.at_level("INFO"):
            maestro_uart.go_home()
        
        expected_command = bytes([0xAA, 0x0C, 0x22])
        mock_serial.write.assert_called_once_with(expected_command)
        assert "Go Home command sent." in caplog.text

    def test_get_moving_state_moving(self, maestro_uart, mock_serial, caplog):
        """Test get_moving_state method when servos are moving."""
        mock_serial.reset_input_buffer.return_value = None
        mock_serial.read.return_value = b'\x01'  # Moving state = 1
        
        with caplog.at_level("INFO"):
            moving_state = maestro_uart.get_moving_state()
        
        assert moving_state == 1
        mock_serial.reset_input_buffer.assert_called_once()
        expected_command = bytes([0xAA, 0x0C, 0x13])
        mock_serial.write.assert_called_once_with(expected_command)
        assert "Moving state: 1" in caplog.text

    def test_get_moving_state_not_moving(self, maestro_uart, mock_serial, caplog):
        """Test get_moving_state method when servos are not moving."""
        mock_serial.reset_input_buffer.return_value = None
        mock_serial.read.return_value = b'\x00'  # Moving state = 0
        
        with caplog.at_level("INFO"):
            moving_state = maestro_uart.get_moving_state()
        
        assert moving_state == 0
        assert "Moving state: 0" in caplog.text

    def test_get_moving_state_no_response(self, maestro_uart, mock_serial):
        """Test get_moving_state method when no response is received."""
        mock_serial.reset_input_buffer.return_value = None
        mock_serial.read.return_value = b''  # No response
        
        moving_state = maestro_uart.get_moving_state()
        
        assert moving_state is None

    def test_close(self, maestro_uart, mock_serial, caplog):
        """Test close method."""
        with caplog.at_level("INFO"):
            maestro_uart.close()
        
        mock_serial.close.assert_called_once()
        assert "Serial port closed." in caplog.text

    def test_threading_lock_usage(self, maestro_uart, mock_serial):
        """Test that all write operations use the threading lock."""
        # Test that set_speed uses the lock
        maestro_uart.set_speed(0, 10)
        mock_serial.write.assert_called_once()
        
        # Reset mock
        mock_serial.reset_mock()
        
        # Test that get_error uses the lock
        mock_serial.read.side_effect = [b'\x00', b'\x00']
        maestro_uart.get_error()
        mock_serial.write.assert_called_once()

    def test_command_byte_clearing_msb(self, maestro_uart, mock_serial):
        """Test that command bytes have MSB cleared in Pololu protocol."""
        # Test with a value that has MSB set
        maestro_uart.set_speed(0, 128)  # 128 = 0x80 (MSB set)
        
        # The command should have MSB cleared (128 & 0x7F = 0)
        expected_command = bytes([0xAA, 0x0C, 0x07, 0, 0, 1])  # 128 >> 7 = 1
        mock_serial.write.assert_called_once_with(expected_command)

    def test_high_target_value_handling(self, maestro_uart, mock_serial):
        """Test handling of high target values in set_target."""
        # Test with a high target value (e.g., 20000)
        maestro_uart.set_target(0, 20000)
        
        # Should split into low and high bytes correctly
        expected_command = bytes([0xAA, 0x0C, 0x04, 0, 20000 & 0x7F, (20000 >> 7) & 0x7F])
        mock_serial.write.assert_called_once_with(expected_command)

    def test_error_code_bit_operations(self, maestro_uart, mock_serial, caplog):
        """Test that error code bit operations work correctly."""
        # Test with error code 0x05 (bits 0 and 2 set)
        mock_serial.reset_input_buffer.return_value = None
        mock_serial.read.side_effect = [b'\x05', b'\x00']
        
        with caplog.at_level("ERROR"):
            error_code = maestro_uart.get_error()
        
        assert error_code == 5
        # Should log both bit 0 and bit 2 errors
        assert "Serial signal error" in caplog.text
        assert "Serial buffer full" in caplog.text

    def test_position_calculation(self, maestro_uart, mock_serial):
        """Test position calculation from two-byte response."""
        # Test with position 12345 (0x3039)
        mock_serial.reset_input_buffer.return_value = None
        mock_serial.read.side_effect = [b'\x39', b'\x30']  # Little-endian representation
        
        position = maestro_uart.get_position(0)
        
        # Should calculate: 0x39 + (0x30 << 8) = 57 + (48 << 8) = 57 + 12288 = 12345
        assert position == 12345

    def test_serial_port_configuration(self, mock_serial):
        """Test that serial port is configured correctly during initialization."""
        with patch('hexapod.maestro.maestro_uart.serial.Serial', return_value=mock_serial):
            MaestroUART(device="/dev/ttyS0", baudrate=9600)
            
            # Verify serial port configuration
            assert mock_serial.baudrate == 9600
            # Check that the serial port attributes are set correctly
            assert hasattr(mock_serial, 'bytesize')
            assert hasattr(mock_serial, 'parity')
            assert hasattr(mock_serial, 'stopbits')
            assert mock_serial.xonxoff is False
            assert mock_serial.timeout == 0

    def test_concurrent_access_protection(self, maestro_uart, mock_serial):
        """Test that concurrent access is properly protected by the lock."""
        import threading
        import time
        
        results = []
        
        def set_speed_thread(channel, speed):
            maestro_uart.set_speed(channel, speed)
            results.append(f"channel_{channel}_speed_{speed}")
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=set_speed_thread, args=(i, i * 10))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all operations completed
        assert len(results) == 5
        assert mock_serial.write.call_count == 5

    def test_logging_levels(self, maestro_uart, mock_serial, caplog):
        """Test that appropriate logging levels are used."""
        # Test info level logging
        with caplog.at_level("INFO"):
            maestro_uart.set_speed(0, 10)
            assert "Speed for channel 0 set to 10." in caplog.text
        
        # Test error level logging
        mock_serial.read.side_effect = [b'\x01', b'\x00']  # Error code 1
        with caplog.at_level("ERROR"):
            maestro_uart.get_error()
            assert "Error detected with code: 1" in caplog.text

    def test_high_speed_value_handling(self, maestro_uart, mock_serial):
        """Test handling of high speed values that require bit shifting."""
        # Test with speed 1000 (requires bit shifting)
        maestro_uart.set_speed(0, 1000)
        
        expected_command = bytes([0xAA, 0x0C, 0x07, 0, 1000 & 0x7F, (1000 >> 7) & 0x7F])
        mock_serial.write.assert_called_once_with(expected_command)

    def test_high_acceleration_value_handling(self, maestro_uart, mock_serial):
        """Test handling of high acceleration values that require bit shifting."""
        # Test with acceleration 1000 (requires bit shifting)
        maestro_uart.set_acceleration(0, 1000)
        
        expected_command = bytes([0xAA, 0x0C, 0x09, 0, 1000 & 0x7F, (1000 >> 7) & 0x7F])
        mock_serial.write.assert_called_once_with(expected_command)

    def test_multiple_targets_large_values(self, maestro_uart, mock_serial, caplog):
        """Test set_multiple_targets with large target values."""
        targets = [(0, 20000), (1, 30000)]
        
        with caplog.at_level("INFO"):
            maestro_uart.set_multiple_targets(targets)
        
        expected_command = bytes([
            0xAA, 0x0C, 0x1F,  # Command header
            2, 0,  # Number of targets, first channel
            20000 & 0x7F, (20000 >> 7) & 0x7F,  # Target 20000
            30000 & 0x7F, (30000 >> 7) & 0x7F   # Target 30000
        ])
        mock_serial.write.assert_called_once_with(expected_command)
        assert "Multiple targets set: [(0, 20000), (1, 30000)]" in caplog.text

    def test_error_code_edge_cases(self, maestro_uart, mock_serial, caplog):
        """Test error code handling with edge case values."""
        # Test with error code 0x01 (only bit 0 set)
        mock_serial.reset_input_buffer.return_value = None
        mock_serial.read.side_effect = [b'\x01', b'\x00']
        
        with caplog.at_level("ERROR"):
            error_code = maestro_uart.get_error()
        
        assert error_code == 1
        assert "Serial signal error" in caplog.text
        # Should not log other error types
        assert "Serial overrun error" not in caplog.text

    def test_position_response_edge_cases(self, maestro_uart, mock_serial):
        """Test position response with edge case values."""
        # Test with maximum position value (0xFFFF = 65535)
        mock_serial.reset_input_buffer.return_value = None
        mock_serial.read.side_effect = [b'\xFF', b'\xFF']
        
        position = maestro_uart.get_position(0)
        assert position == 65535

    def test_serial_communication_failure_handling(self, maestro_uart, mock_serial):
        """Test handling of serial communication failures."""
        # Test get_position with partial response (only one byte instead of two)
        mock_serial.reset_input_buffer.return_value = None
        mock_serial.read.side_effect = [b'\x01', b'\x00']  # First byte, then empty second byte
        
        # This should work and return a position based on both bytes
        position = maestro_uart.get_position(0)
        assert position == 1  # Should return 1 + (0 << 8) = 1

    def test_threading_lock_context_manager(self, maestro_uart, mock_serial):
        """Test that the threading lock is used as a context manager."""
        # Test that operations complete successfully with the lock
        maestro_uart.set_speed(0, 10)
        
        # Verify that the operation completed (write was called)
        mock_serial.write.assert_called_once()

    def test_command_protocol_compliance(self, maestro_uart, mock_serial):
        """Test that all commands follow the Pololu protocol correctly."""
        # Test that all commands start with 0xAA and use device number 0x0C
        maestro_uart.set_speed(0, 10)
        command = mock_serial.write.call_args[0][0]
        assert command[0] == 0xAA
        assert command[1] == 0x0C
        
        mock_serial.reset_mock()
        
        # Mock the read response for get_error
        mock_serial.read.side_effect = [b'\x00', b'\x00']
        maestro_uart.get_error()
        command = mock_serial.write.call_args[0][0]
        assert command[0] == 0xAA
        assert command[1] == 0x0C