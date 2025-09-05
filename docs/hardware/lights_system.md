# Lights System

The lights system provides visual feedback and animations for the hexapod robot using APA102 LED strips. It includes color management, animation control, and hardware integration.

## Overview

The lights system consists of:
- **Lights Class**: Core LED strip control and color management
- **LightsInteractionHandler**: Animation management and leg-to-LED mapping
- **Animation System**: 10+ predefined animations for visual feedback
- **Hardware Integration**: GPIO control, power management, SPI communication

## Core Components

### Lights Class

The `Lights` class manages the APA102 LED strip hardware:

```python
class Lights:
    DEFAULT_NUM_LED: int = 12
    DEFAULT_POWER_PIN: int = 5
    
    def __init__(self, num_led: int = 12, power_pin: int = 5, 
                 brightness: int = 50, initial_color: ColorRGB = ColorRGB.INDIGO)
```

**Key Features:**
- **LED Count**: Configurable number of LEDs (default: 12)
- **Power Control**: GPIO pin for LED power management
- **Brightness Control**: 0-100% brightness adjustment
- **Color Management**: Predefined color palette with RGB values

### Color Management

The `ColorRGB` enum provides 12 predefined colors:

```python
class ColorRGB(Enum):
    BLACK = (0, 0, 0)
    BLUE = (0, 0, 255)
    TEAL = (0, 128, 128)
    GREEN = (0, 255, 0)
    LIME = (75, 180, 0)
    YELLOW = (255, 215, 0)
    GOLDEN = (255, 50, 0)
    ORANGE = (255, 25, 0)
    RED = (255, 0, 0)
    PINK = (255, 51, 183)
    PURPLE = (128, 0, 128)
    INDIGO = (75, 0, 130)
    GRAY = (139, 69, 19)
```

**Color Operations:**
- **RGB Access**: `color.rgb` returns tuple of RGB values
- **Color Setting**: Individual LED or entire strip color control
- **Brightness Scaling**: Automatic brightness adjustment

## Animation System

### Animation Base Class

All animations inherit from the `Animation` abstract base class:

```python
class Animation(threading.Thread, abc.ABC):
    def __init__(self, lights: Lights)
    def start(self) -> None
    def stop_animation(self) -> None
    @abc.abstractmethod
    def execute_animation(self) -> None
```

**Key Features:**
- **Threading**: Runs in separate thread for non-blocking operation
- **Lifecycle Management**: Start/stop control with proper cleanup
- **Abstract Interface**: Forces implementation of animation logic

### Available Animations

#### 1. Pulse Animation
- **Purpose**: Breathing effect with color transitions
- **Parameters**: Pulse color, speed, intensity
- **Use Case**: System status indication

#### 2. Wheel Animation
- **Purpose**: Rotating color wheel effect
- **Parameters**: Rotation speed, color sequence
- **Use Case**: Processing/loading indication

#### 3. Direction of Arrival Animation
- **Purpose**: Visual indication of sound source direction
- **Parameters**: Direction angle, intensity
- **Use Case**: Audio localization feedback

#### 4. Opposite Rotate Animation
- **Purpose**: Counter-rotating color patterns
- **Parameters**: Rotation speed, color pairs
- **Use Case**: Dynamic visual effects

#### 5. Rainbow Animation
- **Purpose**: Full spectrum color cycling
- **Parameters**: Speed, saturation
- **Use Case**: Celebration/attention-grabbing

#### 6. Police Animation
- **Purpose**: Alternating red/blue flashing
- **Parameters**: Flash speed, intensity
- **Use Case**: Alert/emergency indication

#### 7. March Animation
- **Purpose**: Sequential LED activation
- **Parameters**: Speed, direction
- **Use Case**: Movement indication

#### 8. Dance Animation
- **Purpose**: Complex multi-pattern sequences
- **Parameters**: Dance pattern, speed
- **Use Case**: Entertainment/celebration

#### 9. Show Off Animation
- **Purpose**: Display of all available effects
- **Parameters**: Sequence timing
- **Use Case**: Demonstration mode

#### 10. Sit Up Animation
- **Purpose**: Gradual color transition
- **Parameters**: Transition speed, target color
- **Use Case**: Status change indication

## LightsInteractionHandler

The `LightsInteractionHandler` manages animations and provides a clean interface:

```python
class LightsInteractionHandler:
    def __init__(self, leg_to_led: Dict[int, int])
    def stop_animation(self) -> None
    def animation(method: Callable) -> Callable
```

**Key Features:**
- **Animation Management**: Start/stop control for all animations
- **Leg Mapping**: Maps leg indices to LED indices for coordinated effects
- **Decorator Support**: `@animation` decorator for automatic animation handling
- **State Management**: Tracks current animation and prevents conflicts

### Leg-to-LED Mapping

The system maps each leg to specific LEDs for coordinated visual effects:

```python
leg_to_led = {
    0: 0,   # Right leg -> LED 0
    1: 2,   # Right Front leg -> LED 2
    2: 4,   # Left Front leg -> LED 4
    3: 6,   # Left leg -> LED 6
    4: 8,   # Left Back leg -> LED 8
    5: 10   # Right Back leg -> LED 10
}
```

## Hardware Integration

### APA102 LED Strip

**Specifications:**
- **Protocol**: SPI communication
- **LED Count**: 12 LEDs (configurable)
- **Power**: 5V supply with GPIO control
- **Control Pin**: GPIO pin 5 (configurable)
- **Data Pin**: SPI MOSI
- **Clock Pin**: SPI SCLK

### GPIO Configuration

```python
# Force GPIOZero to use RPi.GPIO backend
from gpiozero.pins.rpigpio import RPiGPIOFactory
gpiozero.Device.pin_factory = RPiGPIOFactory()

# Power control
power = LED(power_pin)
power.on()
```

**Key Features:**
- **Backend Selection**: Uses RPi.GPIO for compatibility
- **Power Management**: GPIO-controlled power supply
- **SPI Communication**: Hardware-accelerated data transfer

### Power Management

The system includes intelligent power management:

- **Automatic Power On**: LEDs powered on during initialization
- **Brightness Control**: Software-controlled brightness (0-100%)
- **Power Efficiency**: Automatic brightness scaling for power conservation
- **Safe Shutdown**: Proper power-off sequence

## Usage Examples

### Basic Color Control

```python
from lights import Lights, ColorRGB

# Initialize lights
lights = Lights(num_led=12, brightness=75)

# Set entire strip to blue
lights.set_color(ColorRGB.BLUE)

# Set individual LED
lights.set_color(ColorRGB.RED, led_index=5)

# Adjust brightness
lights.set_brightness(50)
```

### Animation Control

```python
from lights import LightsInteractionHandler
from lights.animations import PulseAnimation

# Initialize handler
handler = LightsInteractionHandler(leg_to_led)

# Start pulse animation
pulse = PulseAnimation(handler.lights, ColorRGB.GREEN)
pulse.start()

# Stop current animation
handler.stop_animation()
```

### Task Integration

```python
from lights import LightsInteractionHandler

class MyTask(Task):
    def __init__(self, lights_handler: LightsInteractionHandler):
        self.lights_handler = lights_handler
    
    @lights_handler.animation
    def execute_task(self):
        # Animation automatically managed
        # Task logic here
        pass
```

## Configuration

### Default Settings

```python
DEFAULT_NUM_LED = 12
DEFAULT_POWER_PIN = 5
DEFAULT_BRIGHTNESS = 50
DEFAULT_INITIAL_COLOR = ColorRGB.INDIGO
```

### Customization

The lights system supports extensive customization:

- **LED Count**: Any number of LEDs (limited by hardware)
- **Power Pin**: Any available GPIO pin
- **Brightness**: 0-100% range
- **Initial Color**: Any predefined or custom color
- **Animation Parameters**: Speed, intensity, patterns

## Performance Considerations

### Threading

- **Non-blocking**: All animations run in separate threads
- **Resource Management**: Proper thread cleanup on stop
- **Concurrency**: Safe animation switching

### Memory Usage

- **Efficient Storage**: Minimal memory footprint for color data
- **Animation Caching**: Pre-calculated animation patterns
- **State Management**: Lightweight state tracking

### Power Consumption

- **Brightness Scaling**: Automatic power optimization
- **Animation Efficiency**: Optimized update patterns
- **Sleep Modes**: Automatic power reduction when idle

## Troubleshooting

### Common Issues

1. **LEDs Not Lighting**
   - Check power pin configuration
   - Verify SPI communication
   - Confirm LED strip connections

2. **Animation Not Starting**
   - Check thread initialization
   - Verify animation parameters
   - Confirm lights object state

3. **Color Inconsistencies**
   - Check RGB value ranges
   - Verify brightness settings
   - Confirm LED strip type

### Debug Information

The system provides comprehensive logging:

```python
logger = logging.getLogger("lights_logger")
logger.debug("Lights initialized successfully")
logger.info("Brightness set to 75%")
logger.warning("Animation stop requested")
```

## Integration Points

### Task System

The lights system integrates with the task system through:

- **Animation Decorators**: Automatic animation management
- **Status Indication**: Visual feedback for task states
- **Error Handling**: Visual error indication

### Voice Control

Voice commands can control lights:

- **Color Changes**: "Change color to blue"
- **Brightness Control**: "Set brightness to 50%"
- **Animation Control**: "Start pulse animation"

### Hardware Status

Lights provide visual feedback for:

- **System Status**: Power, calibration, errors
- **Movement State**: Walking, standing, rotating
- **Audio Processing**: Sound source direction
- **Task Execution**: Progress indication

---

[← Previous: IMU Data Format](imu_data_format.md) | [Next: Servo Control →](servo_control.md)

[← Back to Documentation](../README.md)
