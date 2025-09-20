"""
Shared test configuration and fixtures for the hexapod project.
"""
import sys
import os
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

# Mock ALL external dependencies BEFORE any imports
import unittest.mock as mock

# Mock external dependencies that are not available in test environment
sys.modules['dotenv'] = mock.MagicMock()
sys.modules['serial'] = mock.MagicMock()
sys.modules['icm20948'] = mock.MagicMock()
sys.modules['RPi'] = mock.MagicMock()
sys.modules['RPi.GPIO'] = mock.MagicMock()
sys.modules['smbus2'] = mock.MagicMock()
sys.modules['spidev'] = mock.MagicMock()
sys.modules['gpiozero'] = mock.MagicMock()
sys.modules['gpiozero.pins'] = mock.MagicMock()
sys.modules['gpiozero.pins.rpigpio'] = mock.MagicMock()
sys.modules['gpiozero.pins.rpigpio.RPiGPIOFactory'] = mock.MagicMock()
sys.modules['pyaudio'] = mock.MagicMock()
sys.modules['pygame'] = mock.MagicMock()
sys.modules['pvporcupine'] = mock.MagicMock()
sys.modules['pvrhino'] = mock.MagicMock()
sys.modules['picovoice'] = mock.MagicMock()
sys.modules['paramiko'] = mock.MagicMock()
sys.modules['resampy'] = mock.MagicMock()
sys.modules['sounddevice'] = mock.MagicMock()
sys.modules['dualsense_controller'] = mock.MagicMock()

# Now import pytest and other modules
import pytest

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import hexapod modules
import hexapod
from hexapod.config import Config


@pytest.fixture
def mock_serial():
    """Mock serial connection for hardware testing."""
    mock_serial = Mock()
    mock_serial.is_open = True
    mock_serial.write = Mock()
    mock_serial.read = Mock(return_value=b'')
    mock_serial.readline = Mock(return_value=b'')
    return mock_serial


@pytest.fixture
def mock_gpio():
    """Mock GPIO operations for hardware testing."""
    with patch('RPi.GPIO') as mock_gpio:
        yield mock_gpio


@pytest.fixture
def mock_i2c():
    """Mock I2C operations for sensor testing."""
    with patch('smbus2.SMBus') as mock_i2c:
        yield mock_i2c


@pytest.fixture
def mock_audio():
    """Mock audio operations for voice/ODAS testing."""
    with patch('pyaudio.PyAudio') as mock_audio:
        yield mock_audio


@pytest.fixture
def mock_picovoice():
    """Mock Picovoice operations for voice recognition testing."""
    with patch('pvporcupine.Porcupine') as mock_porcupine, \
         patch('pvrhino.Rhino') as mock_rhino:
        yield {
            'porcupine': mock_porcupine,
            'rhino': mock_rhino
        }


@pytest.fixture
def sample_audio_data():
    """Sample audio data for testing."""
    import numpy as np
    # Generate 1 second of 16kHz audio data
    sample_rate = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    # Generate a simple sine wave
    frequency = 440  # A4 note
    audio_data = np.sin(2 * np.pi * frequency * t)
    return audio_data.astype(np.float32)


@pytest.fixture
def sample_imu_data():
    """Sample IMU data for testing."""
    return {
        'accel': {'x': 0.1, 'y': 0.2, 'z': 9.8},
        'gyro': {'x': 0.01, 'y': 0.02, 'z': 0.03},
        'mag': {'x': 0.1, 'y': 0.2, 'z': 0.3},
        'temperature': 25.0
    }


@pytest.fixture
def sample_odas_data():
    """Sample ODAS data for testing."""
    return {
        'doa': 45.0,  # Direction of arrival in degrees
        'ssl': 0.8,   # Sound source localization confidence
        'audio': b'sample_audio_data',
        'timestamp': 1234567890.0
    }


@pytest.fixture
def hexapod_config():
    """Load hexapod configuration for testing."""
    return Config()


@pytest.fixture
def mock_maestro_commands():
    """Mock Maestro servo commands for testing."""
    return {
        'set_target': 0x84,
        'set_speed': 0x87,
        'set_acceleration': 0x89,
        'get_position': 0x90,
        'get_moving_state': 0x93,
        'get_errors': 0xA1
    }


@pytest.fixture
def sample_leg_positions():
    """Sample leg positions for gait testing."""
    return {
        'leg_1': {'coxa': 0.0, 'femur': 45.0, 'tibia': -90.0},
        'leg_2': {'coxa': 60.0, 'femur': 45.0, 'tibia': -90.0},
        'leg_3': {'coxa': 120.0, 'femur': 45.0, 'tibia': -90.0},
        'leg_4': {'coxa': 180.0, 'femur': 45.0, 'tibia': -90.0},
        'leg_5': {'coxa': 240.0, 'femur': 45.0, 'tibia': -90.0},
        'leg_6': {'coxa': 300.0, 'femur': 45.0, 'tibia': -90.0}
    }


@pytest.fixture
def mock_servo_positions():
    """Mock servo positions for testing."""
    return {
        0: 1500,  # Leg 1 coxa
        1: 1500,  # Leg 1 femur
        2: 1500,  # Leg 1 tibia
        3: 1500,  # Leg 2 coxa
        4: 1500,  # Leg 2 femur
        5: 1500,  # Leg 2 tibia
        # ... continue for all 18 servos
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment before each test."""
    # Set test environment variables
    os.environ['HEXAPOD_TEST_MODE'] = '1'
    os.environ['PYTHONPATH'] = str(project_root)
    
    yield
    
    # Cleanup after test
    if 'HEXAPOD_TEST_MODE' in os.environ:
        del os.environ['HEXAPOD_TEST_MODE']


@pytest.fixture
def mock_file_system():
    """Mock file system operations for testing."""
    with patch('pathlib.Path.exists') as mock_exists, \
         patch('pathlib.Path.read_text') as mock_read_text, \
         patch('pathlib.Path.write_text') as mock_write_text:
        mock_exists.return_value = True
        mock_read_text.return_value = "test content"
        yield {
            'exists': mock_exists,
            'read_text': mock_read_text,
            'write_text': mock_write_text
        }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "hardware: marks tests that require hardware"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on test file location
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        if "slow" in item.name:
            item.add_marker(pytest.mark.slow)