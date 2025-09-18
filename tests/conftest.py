"""
Pytest configuration and shared fixtures for the hexapod project.

This file contains shared fixtures and configuration that are automatically
available to all test modules in the tests directory and subdirectories.
"""
import pytest
from unittest.mock import Mock, patch


@pytest.fixture(autouse=True)
def mock_external_dependencies():
    """
    Automatically mock external dependencies for all tests.
    
    This fixture runs automatically for every test and mocks hardware-specific
    and external dependencies that are not available in the test environment.
    """
    mock_modules = {
        # Hardware-specific modules
        'icm20948': Mock(),
        'serial': Mock(),
        'gpiozero': Mock(),
        'gpiozero.pins': Mock(),
        'gpiozero.pins.rpigpio': Mock(),
        'spidev': Mock(),
        
        # Configuration and utilities
        'yaml': Mock(),
        
        # Hexapod internal modules that have external dependencies
        'hexapod.interface': Mock(),
        'hexapod.interface.logging': Mock(),
        'hexapod.interface.logging.logging_utils': Mock(),
        'hexapod.interface.controllers': Mock(),
        'hexapod.interface.controllers.base_manual_controller': Mock(),
        'hexapod.interface.controllers.gamepad_hexapod_controller': Mock(),
        'hexapod.interface.controllers.gamepad_led_controllers': Mock(),
        'hexapod.interface.controllers.gamepad_led_controllers.dual_sense_led_controller': Mock(),
        'hexapod.interface.controllers.gamepad_led_controllers.gamepad_led_controller': Mock(),
        'hexapod.interface.input_mappings': Mock(),
        'hexapod.interface.input_mappings.base_input_mapping': Mock(),
        'hexapod.interface.input_mappings.dual_sense_bluetooth_mapping': Mock(),
        'hexapod.interface.input_mappings.dual_sense_usb_mapping': Mock(),
        'hexapod.interface.console': Mock(),
        'hexapod.interface.console.non_blocking_console_input_handler': Mock(),
        'hexapod.kws': Mock(),
        'hexapod.kws.recorder': Mock(),
        'hexapod.kws.voice_control': Mock(),
        'hexapod.kws.intent_dispatcher': Mock(),
        'hexapod.robot': Mock(),
        'hexapod.robot.sensors': Mock(),
        'hexapod.robot.sensors.imu': Mock(),
        'hexapod.robot.sensors.button_handler': Mock(),
        'hexapod.robot.hexapod': Mock(),
        'hexapod.robot.joint': Mock(),
        'hexapod.robot.leg': Mock(),
        'hexapod.robot.balance_compensator': Mock(),
        'hexapod.robot.calibration': Mock(),
        'hexapod.task_interface': Mock(),
        'hexapod.task_interface.task_interface': Mock(),
        'hexapod.task_interface.status_reporter': Mock(),
        'hexapod.task_interface.tasks': Mock(),
        'hexapod.task_interface.tasks.task': Mock(),
        'hexapod.task_interface.tasks.composite_calibration_task': Mock(),
        'hexapod.task_interface.tasks.follow_task': Mock(),
        'hexapod.task_interface.tasks.helix_task': Mock(),
        'hexapod.task_interface.tasks.march_in_place_task': Mock(),
        'hexapod.task_interface.tasks.move_task': Mock(),
        'hexapod.task_interface.tasks.rotate_task': Mock(),
        'hexapod.task_interface.tasks.say_hello_task': Mock(),
        'hexapod.task_interface.tasks.show_off_task': Mock(),
        'hexapod.task_interface.tasks.sit_up_task': Mock(),
        'hexapod.task_interface.tasks.sound_source_localization': Mock(),
        'hexapod.task_interface.tasks.stream_odas_audio_task': Mock(),
        'hexapod.odas': Mock(),
        'hexapod.odas.odas_audio_processor': Mock(),
        'hexapod.odas.odas_doa_ssl_processor': Mock(),
        'hexapod.odas.odas_to_picovoice_wav': Mock(),
        'hexapod.odas.streaming_odas_audio_player': Mock(),
        'hexapod.gait_generator': Mock(),
        'hexapod.gait_generator.base_gait': Mock(),
        'hexapod.gait_generator.gait_generator': Mock(),
        'hexapod.gait_generator.tripod_gait': Mock(),
        'hexapod.gait_generator.wave_gait': Mock(),
        'hexapod.utils': Mock(),
        'hexapod.utils.utils': Mock(),
        'hexapod.utils.audio': Mock(),
        'hexapod.utils.visualization': Mock(),
        'hexapod.lights': Mock(),
        'hexapod.lights.animations': Mock(),
        'hexapod.maestro': Mock(),
        'hexapod.config': Mock(),
        'hexapod.main': Mock(),
    }
    
    with patch.dict('sys.modules', mock_modules):
        yield


@pytest.fixture
def mock_apa102():
    """Mock APA102 class for lights testing."""
    mock = Mock()
    mock.return_value.num_led = 12
    mock.return_value.set_pixel = Mock()
    mock.return_value.show = Mock()
    mock.return_value.rotate = Mock()
    mock.return_value.global_brightness = 15
    return mock


@pytest.fixture
def mock_led():
    """Mock LED class for lights testing."""
    mock = Mock()
    mock.return_value.on = Mock()
    mock.return_value.off = Mock()
    return mock
