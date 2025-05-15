# ODAS Data Format Documentation

## Overview
This document describes the data format and logging system used by the ODAS (Open embeddeD Audition System) server implementation. ODAS provides two separate data streams: one for tracked sources and one for potential sources.

## Log Directory Structure
The ODAS server creates and manages log files in the following directory structure:

```
hexapod/
└── logs/
    └── odas/
        ├── tracked.log    # Logs for tracked sound sources
        ├── potential.log  # Logs for potential sound sources
        └── console.log    # General server console output
```

## Data Format

### Raw Data Format
The ODAS server receives data in the following format:
1. 4-byte size header (unsigned integer)
2. JSON payload of the specified size

### JSON Data Structure
The server processes and logs two types of data streams:

#### Tracked Sources
```json
{
    "id": 2,              # Unique identifier (0 = inactive, >0 = active)
    "tag": "dynamic",     # Source type ("dynamic" = automatically detected)
    "x": 0.865,          # X coordinate (-1.0 to 1.0)
    "y": 0.143,          # Y coordinate (-1.0 to 1.0)
    "z": 0.481,          # Z coordinate (-1.0 to 1.0)
    "activity": 0.998    # Activity level (0.0 to 1.0)
}
```

#### Potential Sources
```json
{
    "id": 0,             # Always 0 for potential sources
    "tag": "",           # Empty for potential sources
    "x": 0.0,           # X coordinate (-1.0 to 1.0)
    "y": 0.0,           # Y coordinate (-1.0 to 1.0)
    "z": 0.0,           # Z coordinate (-1.0 to 1.0)
    "activity": 0.0     # Activity level (0.0 to 1.0)
}
```

### Field Descriptions
- `id`: 
  - 0: Inactive or potential source
  - >0: Active tracked source with unique identifier
- `tag`: 
  - "": Empty for potential sources
  - "dynamic": Automatically detected and tracked source
- `x`, `y`, `z`: 3D coordinates of the sound source (-1.0 to 1.0)
- `activity`: Probability of the source being active (0.0 to 1.0)

## Source Types

### Tracked Sources
- Currently active and tracked sound sources
- Have non-zero IDs
- Represent sources that have been confirmed and are being actively tracked
- Only logged in tracked.log when active (non-zero ID)

### Potential Sources
- New or untracked sound sources being detected
- Always have ID 0
- Represent possible sound sources that haven't been confirmed for tracking
- All potential sources are logged in potential.log
- May transition to tracked sources if they meet tracking criteria

## Logging System

### Log File Management
- Log files are created in the `hexapod/logs/odas/` directory
- Files are overwritten when the server starts
- All logs from the current session are preserved until server restart

### Log Content
Each log entry includes:
- Timestamp
- Data type (tracked/potential)
- JSON payload with source information

### Status Updates
- Server provides status updates every 15 seconds
- Shows number of active tracked sources
- Indicates when monitoring for new potential sources
- Warns if no active sources are detected

### Error Handling
- JSON parsing errors are logged with the raw data for debugging
- Connection errors and timeouts are logged in the console log
- Directory creation errors fall back to the current directory

## Troubleshooting

### Common Issues
1. **No Active Sources**
   - Check if sound is being detected
   - Verify microphone configuration
   - Adjust tracking sensitivity in ODAS config

2. **Source ID Issues**
   - ID 0: Normal for potential sources
   - Non-zero IDs: Indicates active tracking
   - Missing IDs: Check tracking parameters

3. **Activity Levels**
   - 0.0: Source is inactive
   - 0.0-1.0: Probability of source being active
   - 1.0: Source is definitely active

4. **Connection Issues**
   - Verify server IP and port settings
   - Check firewall settings
   - Monitor console.log for connection errors

5. **Log File Access**
   - Ensure the `logs/odas` directory exists and is writable
   - Check file permissions
   - Monitor disk space

## Configuration
The server can be configured with the following parameters:
- Host IP address (default: 192.168.0.171)
- Tracked port (default: 9000)
- Potential port (default: 9001)

## Shutdown Process
The server handles shutdown gracefully by:
1. Closing all client connections
2. Flushing and closing log files
3. Cleaning up server sockets
4. Terminating all threads 