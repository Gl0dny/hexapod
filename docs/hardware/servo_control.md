# Servo Control System

The servo control system manages the 18 MG996R servos through the Pololu Maestro servo controller board using UART communication.

## Overview

The servo control system consists of:
- **MaestroUART Class**: Pololu protocol implementation and serial communication
- **Servo Management**: Position control, speed/acceleration settings, error handling
- **Protocol Implementation**: Command structure, device addressing, timing requirements
- **Hardware Integration**: UART communication, servo calibration, position feedback

## Core Components

### MaestroUART Class

The `MaestroUART` class handles communication with the Pololu Maestro controller:

```python
class MaestroUART:
    COMMAND_START: int = 0xAA
    DEFAULT_DEVICE_NUMBER: int = 0x0C
    COMMAND_GET_ERROR: int = 0x21
    COMMAND_GET_POSITION: int = 0x10
    COMMAND_SET_SPEED: int = 0x07
    COMMAND_SET_ACCELERATION: int = 0x09
    COMMAND_SET_TARGET: int = 0x04
    COMMAND_GO_HOME: int = 0x22
    COMMAND_GET_MOVING_STATE: int = 0x13
    COMMAND_SET_MULTIPLE_TARGETS: int = 0x1F
```

**Key Features:**
- **Serial Communication**: UART interface with configurable baud rate
- **Command Protocol**: Pololu protocol implementation
- **Error Handling**: Comprehensive error detection and reporting
- **Thread Safety**: Thread-safe operations with locking

### Initialization

```python
def __init__(self, device: str = '/dev/ttyS0', baudrate: int = 9600):
    self.ser: serial.Serial = serial.Serial(device)
    self.ser.baudrate = baudrate
    self.ser.bytesize = serial.EIGHTBITS
    self.ser.parity = serial.PARITY_NONE
    self.ser.stopbits = serial.STOPBITS_ONE
    self.ser.xonxoff = False
    self.ser.timeout = 0
    self.lock = threading.Lock()
```

**Configuration:**
- **Device**: Serial port (default: `/dev/ttyS0`)
- **Baud Rate**: 9600 bps (default)
- **Data Format**: 8 data bits, no parity, 1 stop bit
- **Timeout**: Non-blocking reads
- **Threading**: Thread-safe with lock

## Pololu Protocol

### Command Structure

The Pololu protocol uses a specific command format:

```
0xAA, device_number, command_byte, data_bytes...
```

**Protocol Details:**
- **Start Byte**: `0xAA` (170 decimal)
- **Device Number**: `0x0C` (12 decimal) - default Maestro device
- **Command Byte**: Command with MSB cleared (bit 7 = 0)
- **Data Bytes**: Command-specific parameters

### Command Examples

#### Set Servo Target
```
Command: 0x04 (Set Target)
Data: channel (1 byte), target (2 bytes, little-endian)
Example: 0xAA, 0x0C, 0x04, 0x00, 0x70, 0x2E
```

#### Get Servo Position
```
Command: 0x10 (Get Position)
Data: channel (1 byte)
Response: position (2 bytes, little-endian)
```

#### Set Servo Speed
```
Command: 0x07 (Set Speed)
Data: channel (1 byte), speed (1 byte)
```

## Servo Management

### Position Control

```python
def set_target(self, channel: int, target: int) -> bool:
    """Set target position for a servo channel."""
    
def get_position(self, channel: int) -> Optional[int]:
    """Get current position of a servo channel."""
```

**Position Units:**
- **Quarter-Microseconds**: 4x microsecond values for precision
- **Range**: 992-2000 microseconds (3968-8000 quarter-microseconds)
- **Resolution**: 0.25 microsecond steps

### Speed and Acceleration

```python
def set_speed(self, channel: int, speed: int) -> bool:
    """Set speed for servo movement."""
    
def set_acceleration(self, channel: int, accel: int) -> bool:
    """Set acceleration for servo movement."""
```

**Speed Units:**
- **Speed**: 0.25 microseconds per 10ms
- **Acceleration**: 0.25 microseconds per 10ms per 80ms
- **Range**: 0-255 for both parameters

### Multiple Servo Control

```python
def set_multiple_targets(self, channels: List[int], targets: List[int]) -> bool:
    """Set targets for multiple servos simultaneously."""
```

**Benefits:**
- **Synchronization**: All servos move together
- **Efficiency**: Single command for multiple servos
- **Precision**: Coordinated movement timing

## Error Handling

### Error Detection

```python
def get_error(self) -> int:
    """Get error status from Maestro controller."""
```

**Error Codes:**
- **0x00**: No error
- **0x01**: Serial signal error
- **0x02**: Serial overrun error
- **0x04**: Serial buffer full
- **0x08**: Serial CRC error
- **0x10**: Serial protocol error
- **0x20**: Serial timeout error

### Error Recovery

The system includes automatic error recovery:

- **Error Detection**: Continuous error monitoring
- **Automatic Retry**: Failed commands are retried
- **Logging**: Comprehensive error logging
- **Graceful Degradation**: System continues with reduced functionality

## Hardware Integration

### Servo Specifications

**MG996R Servo Motors:**
- **Voltage**: 4.8V - 7.2V
- **Current**: 1.0A - 2.5A (stall)
- **Torque**: 9.4 kg-cm (4.8V), 11 kg-cm (6.0V)
- **Speed**: 0.20 sec/60° (4.8V), 0.18 sec/60° (6.0V)
- **Weight**: 55g
- **Dimensions**: 40.7 x 19.7 x 42.9 mm

### Channel Mapping

The hexapod uses 18 servos (3 per leg):

```
Leg 0 (Right):        Channels 0, 1, 2
Leg 1 (Right Front):  Channels 3, 4, 5
Leg 2 (Left Front):   Channels 6, 7, 8
Leg 3 (Left):         Channels 9, 10, 11
Leg 4 (Left Back):    Channels 12, 13, 14
Leg 5 (Right Back):   Channels 15, 16, 17
```

**Joint Mapping:**
- **Coxa**: Channels 0, 3, 6, 9, 12, 15
- **Femur**: Channels 1, 4, 7, 10, 13, 16
- **Tibia**: Channels 2, 5, 8, 11, 14, 17

### Power Management

**Power Requirements:**
- **Total Current**: Up to 45A (18 servos × 2.5A)
- **Voltage**: 6V recommended
- **Power Supply**: External switching power supply
- **Protection**: Fuses and current limiting

## Usage Examples

### Basic Servo Control

```python
from maestro import MaestroUART

# Initialize controller
maestro = MaestroUART('/dev/ttyS0', 9600)

# Set servo position
maestro.set_target(0, 1500 * 4)  # 1500 microseconds

# Get current position
position = maestro.get_position(0)

# Set speed and acceleration
maestro.set_speed(0, 32)
maestro.set_acceleration(0, 5)
```

### Multiple Servo Control

```python
# Move multiple servos simultaneously
channels = [0, 1, 2]  # First leg
targets = [1500 * 4, 1500 * 4, 1500 * 4]
maestro.set_multiple_targets(channels, targets)
```

### Error Handling

```python
# Check for errors
error = maestro.get_error()
if error:
    print(f"Maestro error: {error}")

# Wait for movement completion
while maestro.get_moving_state() != 0:
    time.sleep(0.1)
```

## Configuration

### Serial Port Settings

```python
# Raspberry Pi 3/4
device = '/dev/ttyS0'
baudrate = 9600

# Raspberry Pi 2
device = '/dev/ttyAMA0'
baudrate = 9600
```

### Servo Limits

```python
# Default servo limits
SERVO_INPUT_MIN = 992 * 4   # 3968 quarter-microseconds
SERVO_INPUT_MAX = 2000 * 4  # 8000 quarter-microseconds

# Custom limits per servo
maestro.set_target(0, 1200 * 4)  # Custom position
```

### Timing Parameters

```python
# Default timing
DEFAULT_SPEED = 32      # 0.8064us/ms
DEFAULT_ACCEL = 5       # 0.0016128us/ms/ms

# Custom timing
maestro.set_speed(0, 16)      # Slower movement
maestro.set_acceleration(0, 10)  # Faster acceleration
```

## Performance Considerations

### Communication Efficiency

- **Batched Commands**: Use `set_multiple_targets` for efficiency
- **Error Checking**: Balance error detection with performance
- **Threading**: Thread-safe operations for concurrent access

### Timing Precision

- **Quarter-Microsecond Resolution**: High precision positioning
- **Synchronized Movement**: Multiple servos move together
- **Timing Control**: Precise speed and acceleration control

### Resource Management

- **Serial Port**: Single UART connection
- **Memory Usage**: Minimal buffer requirements
- **CPU Usage**: Low overhead communication

## Troubleshooting

### Common Issues

1. **Servo Not Moving**
   - Check power supply
   - Verify channel mapping
   - Confirm target range

2. **Communication Errors**
   - Check serial port configuration
   - Verify baud rate settings
   - Confirm device number

3. **Position Inaccuracy**
   - Check servo calibration
   - Verify target units
   - Confirm servo limits

### Debug Information

```python
logger = logging.getLogger("maestro_logger")
logger.debug("MaestroUART initialized successfully")
logger.info("Servo 0 moved to position 6000")
logger.warning("Communication error detected")
```

## Integration Points

### Robot System

The servo control integrates with:

- **Hexapod Class**: Main robot control
- **Leg System**: Individual leg control
- **Joint System**: Servo abstraction layer
- **Calibration**: Servo position calibration

### Task System

Tasks use servo control through:

- **Movement Tasks**: Coordinated servo movement
- **Calibration Tasks**: Servo position calibration
- **Status Tasks**: Servo position monitoring

---

[← Previous: Lights System](lights_system.md) | [Next: Task Interface →](../interface/task_interface.md)

[← Back to Documentation](../README.md)
