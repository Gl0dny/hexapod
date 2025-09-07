# Hexapod Project Documentation

[← Back to Project Root](../README.md)

## Quick Start

### **Start Here**
- **[System Overview](core/system_overview.md)** - Get the big picture of how everything works together
- **[Movement System](robot/movement_system.md)** - Learn how the hexapod moves and walks
- **[Voice Control System](voice/voice_control_system.md)** - Understand how voice commands work

## Project Structure

The hexapod project is organized into several key directories, each serving a specific purpose:

```
hexapod/
├── assets/                                   # Project assets and resources
├── data/                                     # Data storage and recordings
├── docs/                                     # Comprehensive documentation
├── firmware/                                 # Firmware files and configurations
├── lib/                                      # External submodules
├── logs/                                     # Log files
├── hexapod/                                  # Main Python package directory
│   ├── gait_generator/                       # Walking pattern generation
│   │   ├── gait_generator.py                 # Main gait coordination
│   │   ├── base_gait.py                      # Base gait implementation
│   │   ├── tripod_gait.py                    # Tripod walking pattern
│   │   └── wave_gait.py                      # Wave walking pattern
│   ├── interface/                            # User interface components
│   │   ├── controllers/                      # Control interfaces
│   │   │   ├── base_manual_controller.py     # Base controller
│   │   │   ├── gamepad_hexapod_controller.py # Gamepad control
│   │   │   └── gamepad_led_controllers/      # Controller LED feedback
│   │   ├── input_mappings/                   # Input device mappings
│   │   ├── console/                          # Console interface
│   │   └── logging/                          # Logging system
│   ├── kws/                                  # Voice recognition system
│   │   ├── voice_control.py                  # Keyword spotting integration
│   │   ├── intent_dispatcher.py              # Command processing
│   │   └── recorder.py                       # Audio recording
│   ├── lights/                               # LED control and visual feedback
│   │   ├── lights.py                         # Main LED control
│   │   ├── lights_interaction_handler.py     # Animation management
│   │   ├── apa102.py                         # Hardware driver
│   │   └── animations/                       # LED animation patterns
│   ├── maestro/                              # Pololu Maestro controller interface
│   │   └── maestro_uart.py                   # UART communication
│   ├── odas/                                 # Spatial audio processing
│   │   ├── odas_doa_ssl_processor.py         # Sound source localization
│   │   ├── odas_audio_processor.py           # Audio processing
│   │   └── streaming_odas_audio_player.py    # Remote audio streaming
│   ├── robot/                                # Core movement control and kinematics
│   │   ├── hexapod.py                        # Main hexapod class and movement control
│   │   ├── leg.py                            # Individual leg control and positioning
│   │   ├── joint.py                          # Joint management and servo control
│   │   ├── calibration.py                    # Servo calibration system
│   │   ├── balance_compensator.py            # IMU-based stability control
│   │   └── sensors/                          # Sensor integration
│   │       ├── imu.py                        # IMU data processing
│   │       └── button_handler.py             # GPIO button control
│   ├── task_interface/                       # Central task coordination
│   │   ├── task_interface.py                 # Main task management system
│   │   ├── status_reporter.py                # System status reporting
│   │   └── tasks/                            # Individual task implementations
│   │       ├── task.py                       # Base task class
│   │       ├── move_task.py                  # Movement tasks
│   │       ├── rotate_task.py                # Rotation tasks
│   │       └── ...                           # Other specialized tasks
│   └── utils/                                # Utility functions and helpers
│       ├── utils.py                          # Core utilities
│       ├── audio/                            # Audio utilities
│       └── visualization/                    # Visualization tools
├── tests/                                    # Test suite
├── main.py                                   # Main application entry point
├── pytest.ini                                # Test configuration
├── README.md                                 # Project overview
└── requirements.txt                          # Python dependencies
```

### Key Components

- **`docs/`** - Comprehensive technical documentation
- **`firmware/`** - Hardware drivers and firmware files
- **`lib/`** - External submodules
- **`hexapod/gait_generator/`** - Walking pattern generation and execution
- **`hexapod/interface/`** - User interfaces (gamepad, console, controller LED feedback)
- **`hexapod/kws/`** - Voice recognition and keyword spotting
- **`hexapod/lights/`** - LED strip control and visual feedback animations
- **`hexapod/maestro/`** - Pololu Maestro servo controller communication
- **`hexapod/odas/`** - Spatial audio processing and sound source localization
- **`hexapod/robot/`** - Core movement control, kinematics, and servo management
- **`hexapod/task_interface/`** - Central task coordination and voice control management
- **`hexapod/utils/`** - Shared utilities and helper functions
- **`tests/`** - Comprehensive test suite for all components

## Complete Documentation Index

### **Core System** (`core/`)
- **[System Overview](core/system_overview.md)** - High-level architecture and design principles
- **[Main Application](core/main_application.md)** - Entry point, CLI, and component initialization
- **[Configuration](core/configuration.md)** - Configuration management and logging

### **User Interface** (`interface/`)
- **[Task Interface](interface/task_interface.md)** - Central coordination and voice control management
- **[Voice Control Interface](interface/voice_control_interface.md)** - Voice command interface and controls
- **[Gamepad Controller](interface/gamepad_controller.md)** - Dual-mode gamepad control

### **Robot Movement** (`robot/`)
- **[Movement System](robot/movement_system.md)** - Overview of movement capabilities
- **[Kinematics](robot/kinematics.md)** - Inverse kinematics and leg positioning
- **[Gait System](robot/gait_system.md)** - Walking patterns and stability control
- **[Movement Commands](robot/movement_commands.md)** - High-level movement processing

### **Hardware** (`hardware/`)
- **[Hardware Integration](hardware/hardware_integration.md)** - Servo control and sensor integration
- **[IMU Data Format](hardware/imu_data_format.md)** - IMU sensor data and processing
- **[Lights System](hardware/lights_system.md)** - LED strip control, animations, visual feedback
- **[Servo Control](hardware/servo_control.md)** - Maestro UART, servo management, Pololu protocol

### **Voice Control & Audio** (`voice/`)
- **[Voice Control System](voice/voice_control_system.md)** - Picovoice integration and intent processing
- **[Audio Recording](voice/audio_recording.md)** - Audio recording capabilities

### **ODAS Audio Processing** (`odas/`)
- **[ODAS Audio Processing System](odas/odas_audio_processing.md)** - Multi-channel audio capture and spatial processing
- **[DOA SSL Processor](odas/doa_ssl_processor.md)** - Direction of arrival processing
- **[ODAS Server](odas/odas_server.md)** - ODAS server setup and configuration
- **[ODAS Data Format](odas/odas_data_format.md)** - Data formats and protocols
- **[ODAS Audio Playback](odas/odas_audio_playback.md)** - ODAS audio playback utilities
- **[Streaming ODAS Audio Player](odas/streaming_odas_audio_player.md)** - Remote audio streaming

---
