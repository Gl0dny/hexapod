# Documentation

This directory contains comprehensive documentation for the hexapod project, organized by component categories.

## Directory Structure

```
docs/
├── audio/              # Audio processing documentation
│   ├── audio_recording.md    # Audio recording utilities
│   ├── audio_playback.md     # Audio playback utilities
│   └── audio_ssl.md          # Sound Source Localization
├── sensors/            # Sensor-related documentation
│   └── imu_data_format.md    # IMU data format and processing
└── odas/               # ODAS-specific documentation
    ├── odas_server.md        # ODAS server setup and usage
    └── odas_data_format.md   # ODAS data format specifications
```

## Documentation Categories

### Audio Documentation (`audio/`)
- Audio recording utilities and usage
- Audio playback capabilities
- Sound Source Localization (SSL) implementation
- Microphone array processing

### Sensor Documentation (`sensors/`)
- IMU data format and specifications
- Sensor data processing
- Calibration procedures

### ODAS Documentation (`odas/`)
- ODAS server configuration
- Data format specifications
- Integration with the main system

## Usage

Each subdirectory contains specific documentation for its respective component. The documentation is written in Markdown format and can be viewed using any Markdown viewer or directly on GitHub.

## Contributing

When adding new documentation:
1. Place it in the appropriate subdirectory
2. Follow the existing naming conventions
3. Update this README if adding new categories
4. Include cross-references to related documentation 