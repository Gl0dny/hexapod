# ODAS DoA/SSL Processor

[← Previous: ODAS Audio Processing System](odas_audio_processing.md) | [Next: ODAS Server →](odas_server.md)

[← Back to Documentation](../README.md)

## Overview
The ODAS DoA/SSL Processor is a Python implementation that processes and relays sound source data from the ODAS (Open embeddeD Audition System). It handles both Direction of Arrival (DoA) and Sound Source Localization (SSL) data, providing real-time processing, visualization, and logging capabilities.

## Features
- Real-time sound source tracking and processing
- Direction of Arrival (DoA) calculation and processing
- Sound Source Localization (SSL) coordinate handling
- LED visualization of sound sources
- Optional GUI data forwarding
- Comprehensive logging system
- Debug mode with real-time source tracking display

## Components

### Core Functionality
- **Sound Source Processing**: Tracks up to 4 active sound sources simultaneously
- **Direction Calculation**: Converts x,y,z coordinates into directional information
- **Data Relay**: Forwards processed data to various outputs (LEDs, GUI, logs)
- **Visualization**: Real-time LED feedback of sound source positions

### Network Handling
- **Tracked Sources Port**: Default 9000
- **Potential Sources Port**: Default 9001
- **GUI Forwarding**: Optional connection to GUI station (default: 192.168.0.102)

### Operating Modes
1. **Local Mode**
   - Runs on 127.0.0.1
   - Starts ODAS process automatically
   - Suitable for development and testing

2. **Remote Mode**
   - Connects to specified host IP
   - Requires running ODAS instance
   - Suitable for production deployment

## Usage

### Command Line Arguments
```bash
--mode: 'local' or 'remote' (default: local)
--host: IP address for remote mode (default: 192.168.0.171)
--tracked-port: Port for tracked sources (default: 9000)
--potential-port: Port for potential sources (default: 9001)
--forward-to-gui: Enable GUI forwarding
--debug: Enable debug mode with real-time display
```

### Example Commands
```bash
# Local mode with debug output
python src/odas/odas_doa_ssl_processor.py --debug

# Remote mode with GUI forwarding
python src/odas/odas_doa_ssl_processor.py --mode remote --forward-to-gui
```

## Data Processing

### Sound Source Data
- Position coordinates (x, y, z)
- Activity level
- Direction (calculated from coordinates)
- Source ID tracking

### Output Formats
1. **LED Visualization**
   - Real-time position display
   - Activity level indication
   - Direction visualization

2. **Log Files**
   - Tracked sources log
   - Potential sources log
   - Timestamped entries

3. **GUI Data**
   - JSON-formatted source data
   - Real-time updates
   - Position and activity information

## Error Handling
- Graceful GUI disconnection handling
- Automatic reconnection attempts
- Proper resource cleanup
- Comprehensive error logging

## Notes
- The processor automatically handles GUI disconnections
- Debug mode provides real-time source tracking display
- Logs are stored in `logs/odas/ssl/` directory
- Maximum of 4 active sources are tracked simultaneously

---

[← Previous: ODAS Audio Processing System](odas_audio_processing.md) | [Next: ODAS Server →](odas_server.md)

[← Back to Documentation](../README.md)