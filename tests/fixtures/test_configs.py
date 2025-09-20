"""
Test configuration data for the hexapod project.
"""
from typing import Dict, Any, List


def get_test_hexapod_config() -> Dict[str, Any]:
    """Get test hexapod configuration."""
    return {
        'robot': {
            'legs': 6,
            'servos_per_leg': 3,
            'total_servos': 18,
            'leg_lengths': {
                'coxa': 50.0,
                'femur': 80.0,
                'tibia': 100.0
            }
        },
        'servos': {
            'min_position': 1000,
            'max_position': 2000,
            'center_position': 1500,
            'speed_limit': 100,
            'acceleration_limit': 50
        },
        'gait': {
            'default_gait': 'tripod',
            'step_height': 20.0,
            'step_length': 30.0,
            'cycle_time': 2.0
        }
    }


def get_test_maestro_config() -> Dict[str, Any]:
    """Get test Maestro configuration."""
    return {
        'port': '/dev/ttyUSB0',
        'baudrate': 9600,
        'timeout': 1.0,
        'channels': 18,
        'min_position': 1000,
        'max_position': 2000,
        'center_position': 1500
    }


def get_test_voice_config() -> Dict[str, Any]:
    """Get test voice control configuration."""
    return {
        'keyword_model': 'porcupine',
        'intent_model': 'rhino',
        'audio_sample_rate': 16000,
        'audio_channels': 1,
        'audio_chunk_size': 1024,
        'confidence_threshold': 0.7
    }


def get_test_odas_config() -> Dict[str, Any]:
    """Get test ODAS configuration."""
    return {
        'config_file': 'odas/config/odas.cfg',
        'doa_enabled': True,
        'ssl_enabled': True,
        'beamforming_enabled': True,
        'noise_reduction_enabled': True,
        'confidence_threshold': 0.7,
        'angle_resolution': 1.0
    }


def get_test_lights_config() -> Dict[str, Any]:
    """Get test lights configuration."""
    return {
        'led_count': 60,
        'spi_port': 0,
        'spi_device': 0,
        'brightness': 128,
        'default_color': [255, 0, 0],  # Red
        'animations_enabled': True
    }


def get_test_imu_config() -> Dict[str, Any]:
    """Get test IMU configuration."""
    return {
        'i2c_bus': 1,
        'i2c_address': 0x68,
        'sample_rate': 100,
        'accel_range': 2,
        'gyro_range': 250,
        'mag_range': 4
    }


def get_sample_leg_positions() -> List[Dict[str, float]]:
    """Get sample leg positions for testing."""
    return [
        {'coxa': 0.0, 'femur': 45.0, 'tibia': -90.0},      # Leg 1
        {'coxa': 60.0, 'femur': 45.0, 'tibia': -90.0},     # Leg 2
        {'coxa': 120.0, 'femur': 45.0, 'tibia': -90.0},    # Leg 3
        {'coxa': 180.0, 'femur': 45.0, 'tibia': -90.0},    # Leg 4
        {'coxa': 240.0, 'femur': 45.0, 'tibia': -90.0},    # Leg 5
        {'coxa': 300.0, 'femur': 45.0, 'tibia': -90.0}     # Leg 6
    ]


def get_sample_servo_positions() -> List[int]:
    """Get sample servo positions for testing."""
    return [1500] * 18  # All servos at center position


def get_sample_voice_commands() -> List[str]:
    """Get sample voice commands for testing."""
    return [
        "move forward",
        "turn left",
        "turn right",
        "stop",
        "stand up",
        "sit down",
        "dance",
        "emergency stop"
    ]


def get_sample_odas_data() -> List[Dict[str, Any]]:
    """Get sample ODAS data for testing."""
    return [
        {
            'doa': 0.0,
            'ssl': 0.8,
            'timestamp': 1234567890.0,
            'confidence': 0.9
        },
        {
            'doa': 45.0,
            'ssl': 0.7,
            'timestamp': 1234567891.0,
            'confidence': 0.8
        },
        {
            'doa': 90.0,
            'ssl': 0.9,
            'timestamp': 1234567892.0,
            'confidence': 0.95
        }
    ]
