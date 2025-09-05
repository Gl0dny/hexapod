# ODAS Server Documentation

[← Previous: Audio SSL](audio_ssl.md) | [Next: ODAS Data Format →](odas_data_format.md)

## Overview

The ODAS (Open embeddeD Audition System) Server is a Python-based server that receives and processes sound source data from ODAS. It handles two separate data streams:
1. Tracked sources: Currently active and tracked sound sources
2. Potential sources: New or untracked sound sources being detected

The server creates and manages log files for both types of sources, providing real-time monitoring and status updates. It can also forward data to a remote GUI station if configured to do so.

## Features

- Real-time sound source tracking and logging
- Support for both tracked and potential sound sources
- Optional GUI data forwarding
- Automatic log file management
- Graceful shutdown handling
- Process monitoring and error reporting

## Usage

### Basic Usage

To start the server in local mode (default):

```bash
python src/odas/odas_server.py --mode local
```

This will:
- Start ODAS with the local configuration
- Listen on localhost (127.0.0.1) for data
- Create log files in the `logs/odas/ssl` directory

### GUI Forwarding

To enable data forwarding to a GUI station:

```bash
python src/odas/odas_server.py --mode local --forward-to-gui
```

This will:
- Start ODAS with the local configuration
- Listen on localhost (127.0.0.1) for data
- Forward data to the GUI station at 192.168.0.102
- Create log files in the `logs/odas/ssl` directory

### Command Line Arguments

The server supports the following command line arguments:

- `--mode`: Operation mode (default: 'local')
  - `local`: Run in local mode, listening on localhost
  - `remote`: Run in remote mode, listening on specified host
- `--host`: Host IP address for remote mode (default: '192.168.0.171')
- `--tracked-port`: Port for tracked sources (default: 9000)
- `--potential-port`: Port for potential sources (default: 9001)
- `--forward-to-gui`: Enable data forwarding to GUI station (default: False)

## Log Files

The server creates two log files in the `logs/odas/ssl` directory:

1. `tracked.log`: Contains data about currently active and tracked sound sources
   - Only logs sources with non-zero IDs
   - Includes source position, activity, and tracking information

2. `potential.log`: Contains data about new or untracked sound sources
   - Logs all potential source detections
   - Includes position and activity information

## Data Format

The server processes JSON data from ODAS. For detailed information about the data format, see [ODAS Data Format](odas_data_format.md).

## Architecture

### Components

1. **ODAS Process Manager**
   - Manages the ODAS process lifecycle
   - Monitors process output and errors
   - Handles process termination

2. **Socket Server**
   - Listens for connections on specified ports
   - Handles client connections and data reception
   - Manages socket lifecycle

3. **Data Processor**
   - Parses incoming JSON data
   - Validates and processes sound source information
   - Updates active source tracking

4. **Log Manager**
   - Creates and manages log files
   - Handles log file rotation and cleanup
   - Provides logging interface

5. **GUI Forwarder** (Optional)
   - Manages connections to GUI station
   - Forwards processed data to GUI
   - Handles connection errors and reconnection

### Data Flow

1. ODAS process generates sound source data
2. Data is sent to local server via TCP sockets
3. Server processes and logs the data
4. If enabled, data is forwarded to GUI station
5. Log files are updated with processed data

## Error Handling

The server implements comprehensive error handling:

- Socket connection errors
- Process monitoring and recovery
- Log file management
- GUI connection management
- Graceful shutdown

## Best Practices

1. **Resource Management**
   - Monitor log file sizes
   - Clean up old log files periodically
   - Monitor system resources

2. **Network Configuration**
   - Ensure proper firewall settings
   - Configure network interfaces correctly
   - Monitor network bandwidth

3. **Process Management**
   - Monitor ODAS process health
   - Handle process crashes gracefully
   - Implement proper shutdown procedures



## Contributing

When contributing to the ODAS server:

1. Follow the existing code style
2. Add appropriate documentation
3. Include error handling
4. Add unit tests
5. Update this documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

[← Previous: Audio SSL](audio_ssl.md) | [Next: ODAS Data Format →](odas_data_format.md) 