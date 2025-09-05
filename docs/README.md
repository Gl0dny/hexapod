# Hexapod Project Documentation

[← Back to Project Root](../README.md)

## Quick Start

### **Start Here**
- **[System Overview](core/system_overview.md)** - Get the big picture of how everything works together
- **[Movement System](robot/movement_system.md)** - Learn how the hexapod moves and walks
- **[Voice Control System](voice/voice_control_system.md)** - Understand how voice commands work

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
- **[Audio Processing](voice/audio_processing.md)** - Multi-channel audio capture and spatial processing
- **[Audio Playback](voice/audio_playback.md)** - Audio playback utilities
- **[Audio Recording](voice/audio_recording.md)** - Audio recording capabilities
- **[Audio SSL](voice/audio_ssl.md)** - Sound source localization
- **[ODAS Server](voice/odas_server.md)** - ODAS server setup and configuration
- **[ODAS Data Format](voice/odas_data_format.md)** - Data formats and protocols
- **[DOA SSL Processor](voice/doa_ssl_processor.md)** - Direction of arrival processing
- **[ODAS KWS Testing](voice/odas_kws_testing.md)** - Keyword spotting testing
- **[Streaming Audio Player](voice/streaming_odas_audio_player.md)** - Remote audio streaming

---

[← Back to Project Root](../README.md)