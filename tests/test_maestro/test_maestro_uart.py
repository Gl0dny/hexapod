import pytest
from unittest.mock import Mock, patch
import sys
from typing import List, Tuple

class TestMaestroUART:
    """Unit tests for the real MaestroUART class from hexapod.maestro.maestro_uart."""
    
    @pytest.fixture
    def mock_serial(self):
        """Create a mock Serial instance."""
        mock_ser = Mock()
        mock_ser.reset_input_buffer.return_value = None
        mock_ser.write.return_value = None
        mock_ser.read.return_value = b'\x00'
        mock_ser.close.return_value = None
        return mock_ser
    
    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        mock_logger = Mock()
        mock_logger.info.return_value = None
        mock_logger.error.return_value = None
        return mock_logger
    
    def _create_maestro_instance(self, maestro_class, mock_serial):
        """Helper method to create a properly configured maestro instance."""
        with patch.object(maestro_class, '__init__', return_value=None):
            maestro = maestro_class()
            maestro.ser = mock_serial
            # Create a mock lock that supports context manager protocol
            mock_lock = Mock()
            mock_lock.__enter__ = Mock(return_value=None)
            mock_lock.__exit__ = Mock(return_value=None)
            maestro.lock = mock_lock
            return maestro
    
    @pytest.fixture
    def maestro_class(self):
        """Import the real MaestroUART class with mocked dependencies."""
        # Mock all external dependencies
        with patch.dict('sys.modules', {
            'serial': Mock(),
            'yaml': Mock(),
            'hexapod.interface': Mock(),
            'hexapod.interface.logging': Mock(),
            'hexapod.interface.logging.logging_utils': Mock(),
            'hexapod.interface.logging.logger': Mock(),
            'hexapod.interface.console': Mock(),
            'hexapod.interface.console.non_blocking_console_input_handler': Mock(),
            'hexapod.interface.controllers': Mock(),
            'hexapod.interface.input_mappings': Mock(),
            'hexapod.kws': Mock(),
            'hexapod.kws.recorder': Mock(),
            'hexapod.kws.voice_control': Mock(),
            'hexapod.kws.intent_dispatcher': Mock(),
            'hexapod.main': Mock(),
            'hexapod.odas': Mock(),
            'hexapod.robot': Mock(),
            'hexapod.task_interface': Mock(),
            'hexapod.utils': Mock(),
            'hexapod.lights': Mock(),
            'hexapod.gait_generator': Mock(),
            'hexapod.config': Mock(),
            'hexapod.maestro': Mock()
        }):
            # Import the real module
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "maestro_module", 
                "/Users/gl0dny/workspace/hexapod/hexapod/maestro/maestro_uart.py"
            )
            maestro_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(maestro_module)
            return maestro_module.MaestroUART

    def test_initialization(self, maestro_class, mock_serial):
        """Test MaestroUART initialization with proper serial configuration."""
        with patch.object(maestro_class, '__init__', return_value=None) as mock_init:
            maestro = maestro_class()
            maestro.ser = mock_serial
            maestro.lock = Mock()  # Add the missing lock attribute
            
            # Test that the instance was created
            assert maestro is not None
            assert hasattr(maestro, 'ser')
            assert hasattr(maestro, 'lock')

    def test_get_error_no_error(self, maestro_class, mock_serial):
        """Test get_error method with no error response."""
        maestro = self._create_maestro_instance(maestro_class, mock_serial)
        maestro.ser.read.side_effect = [b'\x00', b'\x00']
        
        error_code = maestro.get_error()
        
        # Verify the command was sent correctly
        expected_command = bytes([0xAA, 0x0C, 0x21])  # COMMAND_START, device number, COMMAND_GET_ERROR
        maestro.ser.write.assert_called_with(expected_command)
        assert error_code == 0

    def test_get_error_with_error(self, maestro_class, mock_serial):
        """Test get_error method with error response."""
        maestro = self._create_maestro_instance(maestro_class, mock_serial)
        maestro.ser.read.side_effect = [b'\x01', b'\x00']  # Error code 1
        
        error_code = maestro.get_error()
        
        expected_command = bytes([0xAA, 0x0C, 0x21])
        maestro.ser.write.assert_called_with(expected_command)
        assert error_code == 1

    def test_get_position(self, maestro_class, mock_serial):
        """Test get_position method."""
        maestro = self._create_maestro_instance(maestro_class, mock_serial)
        maestro.ser.read.side_effect = [b'\x10', b'\x27']  # Position bytes
        
        position = maestro.get_position(0)
        
        expected_command = bytes([0xAA, 0x0C, 0x10, 0])  # COMMAND_GET_POSITION, channel
        maestro.ser.write.assert_called_with(expected_command)
        # Position = 0x10 + (0x27 << 8) = 16 + (39 << 8) = 16 + 9984 = 10000
        expected_position = 16 + (39 << 8)
        assert position == expected_position

    def test_set_speed(self, maestro_class, mock_serial):
        """Test set_speed method."""
        maestro = self._create_maestro_instance(maestro_class, mock_serial)
        
        maestro.set_speed(0, 32)
        
        expected_command = bytes([0xAA, 0x0C, 0x07, 0, 32 & 0x7F, (32 >> 7) & 0x7F])
        maestro.ser.write.assert_called_with(expected_command)

    def test_set_acceleration(self, maestro_class, mock_serial):
        """Test set_acceleration method."""
        maestro = self._create_maestro_instance(maestro_class, mock_serial)
        
        maestro.set_acceleration(0, 5)
        
        expected_command = bytes([0xAA, 0x0C, 0x09, 0, 5 & 0x7F, (5 >> 7) & 0x7F])
        maestro.ser.write.assert_called_with(expected_command)

    def test_set_target(self, maestro_class, mock_serial):
        """Test set_target method."""
        maestro = self._create_maestro_instance(maestro_class, mock_serial)
        
        maestro.set_target(0, 6000)
        
        expected_command = bytes([0xAA, 0x0C, 0x04, 0, 6000 & 0x7F, (6000 >> 7) & 0x7F])
        maestro.ser.write.assert_called_with(expected_command)

    def test_go_home(self, maestro_class, mock_serial):
        """Test go_home method."""
        maestro = self._create_maestro_instance(maestro_class, mock_serial)
        
        maestro.go_home()
        
        expected_command = bytes([0xAA, 0x0C, 0x22])
        maestro.ser.write.assert_called_with(expected_command)

    def test_get_moving_state(self, maestro_class, mock_serial):
        """Test get_moving_state method."""
        maestro = self._create_maestro_instance(maestro_class, mock_serial)
        maestro.ser.read.return_value = b'\x00'
        
        moving_state = maestro.get_moving_state()
        
        expected_command = bytes([0xAA, 0x0C, 0x13])
        maestro.ser.write.assert_called_with(expected_command)
        assert moving_state == 0

    def test_get_moving_state_empty_response(self, maestro_class, mock_serial):
        """Test get_moving_state method with empty response."""
        maestro = self._create_maestro_instance(maestro_class, mock_serial)
        maestro.ser.read.return_value = b''
        
        moving_state = maestro.get_moving_state()
        
        assert moving_state is None

    def test_close(self, maestro_class, mock_serial):
        """Test close method."""
        maestro = self._create_maestro_instance(maestro_class, mock_serial)
        
        maestro.close()
        
        maestro.ser.close.assert_called_once()

    def test_set_multiple_targets(self, maestro_class, mock_serial):
        """Test set_multiple_targets method with sequential channels."""
        maestro = self._create_maestro_instance(maestro_class, mock_serial)
        targets = [(3, 0), (4, 6000)]
        
        maestro.set_multiple_targets(targets)
        
        expected_command = bytes([
            0xAA, 0x0C, 0x1F,  # COMMAND_START, device number, COMMAND_SET_MULTIPLE_TARGETS
            2, 3,              # Number of targets and first channel
            0 & 0x7F, (0 >> 7) & 0x7F,      # Target for channel 3
            6000 & 0x7F, (6000 >> 7) & 0x7F  # Target for channel 4
        ])
        maestro.ser.write.assert_called_with(expected_command)

    def test_set_multiple_targets_non_sequential(self, maestro_class, mock_serial):
        """Test set_multiple_targets method with non-sequential channels raises ValueError."""
        maestro = self._create_maestro_instance(maestro_class, mock_serial)
        targets = [(3, 6000), (5, 7000)]  # Non-sequential channels
        
        with pytest.raises(ValueError) as exc_info:
            maestro.set_multiple_targets(targets)
        
        assert "Channels are not sequential." in str(exc_info.value)
        