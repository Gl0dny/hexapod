## Thesis : "Hexapod autonomous control system based on auditory scene analysis: real-time sound source localization and keyword spotting for voice command recognition"

Diploma project completed at Warsaw University of Science and Technology as a part of Master of Science in Engineering - Computer Science.

This project aims to develop an autonomous control system for a hexapod walking robot, using auditory scene analysis as the primary modality for navigation and environmental interaction. The system integrates sound source localization (Direction of Arrival estimation - DOA) and beamforming techniques via the ODAS framework, employing a circular microphone array for enhanced spatial precision. This enables the robot to accurately detect and characterize sound sources, allowing real-time responses to acoustic stimuli for dynamic, context-aware behavior.

A Keyword Spotting (KWS) module, powered by machine learning, is incorporated to recognize predefined voice commands, enabling effective human-robot interaction. The research focuses on developing the hardware and software infrastructure to seamlessly integrate acoustic processing with the robot's control system.

The project includes designing and building the robot's platform, encompassing both the mechanical structure and embedded systems. The hexapod's platform is engineered to support advanced auditory processing, ensuring optimal performance in real-world scenarios. This involves creating a robust mechanical framework for stable, agile locomotion and an embedded system architecture for real-time processing and decision-making.

The hardware is designed to accommodate the circular microphone array, ensuring precise sound capture, while the software facilitates seamless communication between auditory processing modules, the control system, and actuators. This comprehensive approach ensures the robot can perform complex tasks, such as navigating dynamic environments and responding accurately to auditory cues.

![](./assets/hexapod.jpg)

![](./assets/hexapod2.jpg)

### Real-Time Sound Source Localization: Hexapod Robot with ODAS Audio Processing
[Click the image below to watch the full demonstration video]

[![Real-Time Sound Source Localization: Hexapod Robot with ODAS Audio Processing](./assets/odas_thumbnail.png)](https://www.youtube.com/watch?v=d-cn0CHzEGE)

This video demonstrates an autonomous hexapod robot performing advanced auditory scene analysis in real-time. The complete ODAS (Open embeddeD Audition System) pipeline with beamforming is showcased, featuring:

- Real-time Direction of Arrival (DoA) estimation using a 6-microphone circular array
- Live GUI visualization showing sound source tracking and spatial mapping
- Terminal debug output displaying active sound sources with coordinates and activity levels
- Elevation and azimuth time charts showing temporal tracking of sound source positions
- System monitoring panel showing CPU usage, temperature, memory usage, and IP address
- Robot view - top-down view of the hexapod responding to acoustic stimuli
- LED feedback system indicating detected sound sources through visual cues
- Multi-source tracking - demonstrating the system's ability to track up to 4 simultaneous sound sources
- Automatic audio stream separation and recording of individual source audio files

This represents a complete autonomous control system where the hexapod can navigate and interact based purely on auditory cues, enabling sophisticated human-robot interaction through voice commands and environmental sound awareness.

## Voice Control System

The hexapod operates through a sophisticated voice control system that processes commands through distinct phases, each with specific functionality and visual feedback:

### System Phases

#### 1. **Wake Word Detection Mode**
![Wake Word Mode](assets/gifs/wake_word_mode.gif)
*"Listening for 'Hexapod'..."* - System continuously monitors audio input for the wake word using Picovoice Porcupine engine. LEDs show pulsing animation (blue base with green pulse) during passive listening state.

#### 2. **Intent Recognition Mode**
![Intent Mode](assets/gifs/intent_mode.gif)
*"What would you like me to do?"* - After wake word detection, system switches to active command listening using Picovoice Rhino engine. LEDs show alternating light rotating pattern while waiting for voice command.

#### 3. **Command Processing Mode**
![Processing Mode](assets/gifs/processing_mode.gif)
*"Processing your request..."* - System analyzes the recognized intent, extracts parameters, and determines the appropriate action. LED animation shows lime green opposite rotation pattern during processing.

#### 4. **Task Execution Mode**
![Execution Mode](assets/gifs/execution_mode.gif)
*"Executing command..."* - System dispatches the command to the appropriate subsystem (movement, lights, audio, or system control). LED feedback varies by command type and execution progress.

#### 5. **Error Handling Mode**
![Error Mode](assets/gifs/error_mode.gif)
*"Command not recognized"* - System handles unrecognized commands, invalid parameters, or execution failures. LED indicators show pulsing animation (red base with orange pulse) for error states.

### System Features
- **Multi-intent processing** - Handles complex commands with multiple parameters
- **Task interruption** - Wake word detection automatically interrupts current tasks (gait tasks are gracefully stopped after completing a cycle)
- **Real-time feedback** - Visual and audio confirmation of system state
- **Error recovery** - Graceful handling of command failures and system errors

## Usage Examples

### Movement Commands

#### Walk
![Walk](assets/gifs/walk.gif)
*"Hexapod, walk [direction] [for X seconds/minutes/cycles]" - Omnidirectional movement in 8 directions: forward, backward, left, right, forward left, forward right, backward left, backward right. Supports time-based (seconds/minutes) or cycle-based movement*

#### Turn
![Turn](assets/gifs/turn.gif)
*"Hexapod, turn [clockwise/counterclockwise] [for X seconds/minutes/cycles]" - Smooth rotation in both directions using inverse kinematics. Supports time-based (seconds/minutes) or cycle-based rotation*

#### March in Place
![March in Place](assets/gifs/march_in_place.gif)
*"Hexapod, march in place [for X seconds/minutes]" - In-place marching demonstration with optional duration control*

#### Idle Stance
*"Hexapod, go to idle stance" - Return to neutral default position*

### Entertainment Commands

#### Sit Up
![Sit Up](assets/gifs/sit_up.gif)
*"Hexapod, make some sit ups" - Dynamic sit-up exercise routine*

#### Say Hello
![Say Hello](assets/gifs/say_hello.gif)
*"Hexapod, say hello" - Friendly greeting gesture with leg movement*

#### Show Off
![Show Off](assets/gifs/show_off.gif)
*"Hexapod, show off" - Demonstration routine showcasing capabilities*

#### Helix
![Helix](assets/gifs/helix.gif)
*"Hexapod, helix" - Complex helical movement pattern*

### Light Commands

#### Police Lights
![Police Lights](assets/gifs/police_lights.gif)
*"Hexapod, activate police mode" - Police-style flashing lights*

#### Rainbow Lights
![Rainbow Lights](assets/gifs/rainbow_lights.gif)
*"Hexapod, activate rainbow" - Rainbow color sequence*

#### Change Color
![Change Color](assets/gifs/change_color.gif)
*"Hexapod, change color to [blue/red/green/etc.]" - Change LED color to specified color from 13 available colors*

#### Turn Lights On/Off
![Turn Lights](assets/gifs/turn_lights.gif)
*"Hexapod, turn lights [on/off]" - Control LED power state*

#### Set Brightness
![Set Brightness](assets/gifs/set_brightness.gif)
*"Hexapod, set brightness to X%" - Adjust LED brightness from 0-100%*

### Audio Commands

#### Sound Source Following
![Sound Following](assets/gifs/sound_following.gif)
*"Hexapod, follow me" - Audio-based target following using ODAS*

#### Sound Source Localization
![Sound Localization](assets/gifs/sound_localization.gif)
*"Hexapod, run sound source localization" - Analyze environment for sound sources*

#### Stream ODAS Audio
*"Hexapod, stream ODAS audio" - Stream processed audio from ODAS system to remote host*

#### Start/Stop Recording
*"Hexapod, start recording [for X seconds/minutes]" / "Hexapod, stop recording" - Begin/end audio recording with optional duration control*

### System Commands

#### Calibrate
![Calibrate](assets/gifs/calibrate.gif)
*"Hexapod, calibrate servos" - Servo calibration and position setup*

#### System Status
*"Hexapod, what's your status?" - System health and status reporting*

#### Help
*"Hexapod, show commands" - Display list of available commands*

#### Wake Up
![Wake Up](assets/gifs/wake_up.gif)
*"Hexapod, wake up" - Activate the system from sleep mode*

#### Sleep
![Sleep](assets/gifs/sleep.gif)
*"Hexapod, go to sleep" - Put system into sleep mode*

#### Stop
*"Hexapod, stop" - Immediately stop current task or movement*

#### Repeat Last Command
*"Hexapod, repeat last command" - Execute the previous command again*

#### Set Speed
*"Hexapod, set speed to X%" - Adjust movement speed from 0-100%*

#### Set Acceleration
*"Hexapod, set acceleration to X%" - Adjust movement acceleration from 0-100%*

#### Shut Down
![Shut Down](assets/gifs/shut_down.gif)
*"Hexapod, shut down" - Safely power down the entire system with countdown timer and LED indication*

## Key Features

### Advanced Voice Control
- Custom wake word detection ("Hexapod")
- Natural language command processing
- Multi-intent handling for complex command processing
   - Context-aware command interpretation
- Support for movement, gait control, and system commands

### Spatial Audio Processing
- Real-time Direction of Arrival (DOA) estimation
- 6-microphone circular array processing
- Multi-source tracking (up to 4 simultaneous sources)
- Beamforming for enhanced speech recognition
- Optional GUI on remote host for ODAS processing
- Real-time audio streaming and recording capabilities
- Network communication for remote processing
- Automatic audio source separation and tracking

### Intelligent Movement
   - 18-degree-of-freedom movement (3 DOF per leg)
- Multiple gait patterns (tripod, wave, custom)
- IMU-based stability control
- Circle-based targeting for direction-independent movement
- Precise inverse kinematics for accurate positioning
- State machine management for coordinated gait execution

### Visual Feedback
- LED strip integration for status indication
- Advanced LED animation system with multiple patterns
- Real-time sound source localization visualization through LED patterns
- Color-coded system status and error indication
- Brightness control and color customization (RGB based)

## Performance Characteristics

- **Voice Recognition**: >95% accuracy, <200ms latency
- **Sound Source Localization**: ±5° accuracy, real-time processing
- **Movement Control**: 50Hz servo update rate
- **Multi-source Tracking**: Up to 4 simultaneous sound sources

## Hardware

### Core Components
- **Raspberry Pi 4** (2GB+ RAM recommended)
- **18x TowerPro MG-995 Servos** (3 per leg)
- **Pololu Maestro 24-Channel Servo Controller**
- **ReSpeaker 6-Mic Circular Array**
- **ICM-20948 IMU**
- **APA102 LED Strip** (integrated in ReSpeaker)
- **5 x 1.2V 2500 mAh NiMH Battery Pack (6V total)**

### Optional Components
- **Remote ODAS  - GUI**
- **Gamepad Controller** (for manual control)

## Quick Start

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd hexapod

# Run the automated installation script
./install.sh
```

The installation script will:
- Check Python version compatibility
- Install the hexapod package and dependencies
- Create configuration directories
- Prompt for your Picovoice Access Key
- Set up the configuration file automatically

### Running the System

#### Basic Voice Control
```bash
# Run with voice control (uses default config file)
hexapod
```

#### With Gamepad Control
The system automatically detects and uses a connected DualSense controller. If a controller is detected, the system will start in manual control mode with voice control as a secondary option. If no controller is detected, the system falls back to voice control mode only.

```bash
# Run with automatic controller detection
hexapod
```

#### Custom Configuration
```bash
# Use a custom picovoice access_key configuration file
hexapod --config /path/to/your/.picovoice.env

# Override the Picovoice access key
hexapod --access-key "YOUR_PICOVOICE_KEY"
```

### Configuration Options

For a complete list of available command-line options, run:

```bash
hexapod --help
```

The system uses a configuration file at `~/.config/hexapod/.picovoice.env` by default, which is automatically created during installation.

## System Architecture

The hexapod system consists of several integrated components:

- **Voice Control System** - Picovoice integration for wake word detection and command recognition
- **ODAS Audio Processing** - Real-time spatial audio processing and sound source localization
- **Robot Movement** - 18-DOF hexapod with inverse kinematics and multiple gait patterns
- **Hardware Integration** - Servo control, IMU sensing, and LED feedback systems
- **Task Management** - Central coordination system for complex operations

### High-Level System Architecture

```mermaid
graph TB
    subgraph "Hexapod System Architecture"
        subgraph "Application Layer"
            MA[Main Application<br/>• Entry Point<br/>• Component Coordination<br/>• Control Mode Management]
            TI[Task Interface<br/>• Voice Command Processing<br/>• Task Orchestration<br/>• State Management]
        end
        
        subgraph "Control Systems"
            VC[Voice Control<br/>• Wake Word Detection<br/>• Intent Recognition<br/>• Audio Processing]
            MC[Manual Control<br/>• Gamepad Input<br/>• Mode Switching<br/>• LED Feedback]
        end
        
        subgraph "Robot Systems"
            RM[Robot Movement<br/>• Gait Generation<br/>• Inverse Kinematics<br/>• Movement Commands]
            HI[Hardware Integration<br/>• Servo Control<br/>• Sensor Integration<br/>• Power Management]
        end
        
        subgraph "Audio Processing"
            ODAS[ODAS Audio<br/>• Sound Source Localization<br/>• Spatial Processing<br/>• Direction Tracking]
        end
    end
    
    MA --> TI
    MA --> VC
    MA --> MC
    TI --> RM
    TI --> HI
    VC --> TI
    MC --> TI
    ODAS --> TI
    RM --> HI
```

### Voice Control System

```mermaid
graph TB
    subgraph "Voice Control System"
        subgraph "Audio Input"
            MA[6-Mic Array<br/>• ReSpeaker 6<br/>• 8 Channels<br/>• 16kHz Sample Rate]
            AD[Audio Device<br/>• Auto-detection<br/>• Device Selection<br/>• ALSA Integration]
        end
        
        subgraph "Voice Processing"
            PV[Picovoice Engine<br/>• Porcupine Wake Word<br/>• Rhino Intent Recognition<br/>• Real-time Processing]
            ID[Intent Dispatcher<br/>• Command Routing<br/>• Parameter Parsing<br/>• Task Interface]
        end
        
        subgraph "Robot Control"
            TI[Task Interface<br/>• Movement Commands<br/>• Light Control<br/>• System Commands]
            AR[Audio Recording<br/>• Continuous Recording<br/>• Duration-based<br/>• File Management]
        end
    end
    
    MA --> AD
    AD --> PV
    PV --> ID
    ID --> TI
    PV --> AR
```

### ODAS Audio Processing

```mermaid
graph TB
    subgraph "Audio Processing System"
        subgraph "Hardware Input"
            MA["6-Mic ReSpeaker Array<br/>• 8 Channels<br/>• 16kHz Sample Rate<br/>• 32-bit Audio"]
            AD["Audio Device<br/>• ALSA Integration<br/>• Real-time Capture<br/>• Multi-channel"]
        end
        
        subgraph "ODAS Processing"
            OD["ODAS Framework<br/>• Sound Source Localization<br/>• Direction of Arrival<br/>• Beamforming<br/>• Audio Separation"]
            CF["Configuration Files<br/>• local_odas.cfg<br/>• SSL Parameters<br/>• DOA Settings"]
        end
        
        subgraph "Data Processing"
            DS["Data Servers<br/>• Tracked Sources (Port 9000)<br/>• Potential Sources (Port 9001)<br/>• TCP Communication"]
            AP["Audio Processor<br/>• Channel Selection<br/>• Sample Rate Conversion<br/>• Picovoice Integration"]
        end
        
        subgraph "Output Streams"
            AS["Audio Streaming<br/>• Remote Playback<br/>• Real-time Transfer<br/>• WAV Conversion"]
            VS["Visualization<br/>• LED Feedback<br/>• Direction Display<br/>• Source Tracking"]
        end
    end
    
    MA --> AD
    AD --> OD
    OD --> CF
    OD --> DS
    DS --> AP
    AP --> AS
    DS --> VS
```

### Robot Movement System

```mermaid
graph TB
    subgraph "Robot Movement System"
        subgraph "Core Control"
            H[Hexapod<br/>• Main Controller<br/>• 18 Servo Management<br/>• Position Tracking]
            GG[Gait Generator<br/>• Pattern Execution<br/>• State Management<br/>• Thread Coordination]
        end
        
        subgraph "Leg Control"
            L[Leg Class<br/>• Individual Leg Control<br/>• Inverse Kinematics<br/>• Joint Management]
            J[Joint Class<br/>• Servo Control<br/>• Angle Validation<br/>• Safety Limits]
        end
        
        subgraph "Movement Patterns"
            TG[Tripod Gait<br/>• 3+3 Leg Groups<br/>• High Stability<br/>• Efficient Movement]
            WG[Wave Gait<br/>• Sequential Movement<br/>• Maximum Stability<br/>• Precise Control]
        end
        
        subgraph "Hardware Integration"
            MU[Maestro UART<br/>• Servo Communication<br/>• Real-time Control<br/>• Safety Management]
            BC[Balance Compensator<br/>• IMU Integration<br/>• Stability Control<br/>• Fall Prevention]
        end
    end
    
    H --> GG
    H --> L
    L --> J
    GG --> TG
    GG --> WG
    H --> MU
    H --> BC
    J --> MU
```

### Hardware Integration

```mermaid
graph TB
    subgraph "Hardware Integration System"
        subgraph "Control Layer"
            HC[Hexapod Controller<br/>• Joint Management<br/>• Position Control<br/>• Calibration]
            MC[Maestro Controller<br/>• UART Communication<br/>• Servo Commands<br/>• Error Handling]
        end
        
        subgraph "Hardware Components"
            SC[Servo Motors<br/>• 18 MG-995 Servos<br/>• 3 per leg<br/>• Position Control]
            IMU[IMU Sensor<br/>• ICM-20948<br/>• 9-DOF<br/>• Orientation Data]
            BTN[Button Input<br/>• GPIO Pin 26<br/>• User Interface<br/>• System Control]
            LED[ReSpeaker 6 LEDs<br/>• Integrated APA102 LEDs<br/>• 12 LEDs<br/>• Visual Feedback]
        end
        
        subgraph "Communication"
            UART[UART Interface<br/>• /dev/ttyAMA1<br/>• 9600 baud<br/>• Pololu Protocol]
            SPI[SPI Interface<br/>• LED Control<br/>• High Speed<br/>• Real-time Updates]
            GPIO[GPIO Interface<br/>• Button Input<br/>• Power Control<br/>• Digital I/O]
        end
    end
    
    HC --> MC
    MC --> UART
    UART --> SC
    HC --> IMU
    HC --> BTN
    HC --> LED
    LED --> SPI
    BTN --> GPIO
```

### Task Management System

```mermaid
graph TB
    subgraph "Task Interface"
        subgraph "Core Management"
            TI[TaskInterface<br/>• Central Coordinator<br/>• Voice Command Processing<br/>• Task Lifecycle Management]
            SR[StatusReporter<br/>• System Health Monitoring<br/>• Status Information<br/>• Diagnostic Data]
        end
        
        subgraph "Hardware Integration"
            H[Hexapod<br/>• Robot Control<br/>• Movement<br/>• Calibration]
            LH[LightsHandler<br/>• Visual Feedback<br/>• Status Display<br/>• Animations]
            BH[ButtonHandler<br/>• GPIO Input<br/>• User Interaction<br/>• State Management]
        end
        
        subgraph "Task Execution"
            TQ[Task Queue<br/>• Task Management<br/>• Lifecycle Control<br/>• Callback Handling]
            TE[Task Executor<br/>• Thread Management<br/>• Resource Allocation<br/>• Error Recovery]
        end
    end
    
    TI --> H
    TI --> LH
    TI --> BH
    TI --> SR
    TI --> TQ
    TQ --> TE
```

## Documentation

For detailed technical documentation and system architecture please refer to the [Documentation](./docs/README.md).

The documentation covers:

### Getting Started
- [Installation Guide](INSTALL.md) - Complete installation and setup instructions

### Core Systems
- [System Overview](docs/core/system_overview.md) - High-level architecture and component relationships
- [Main Application](docs/core/main_application.md) - Application entry point and component coordination
- [Configuration](docs/core/configuration.md) - System configuration and parameters

### Robot Movement
- [Movement System](docs/robot/movement_system.md) - Overview of movement capabilities
- [Kinematics](docs/robot/kinematics.md) - Inverse kinematics and coordinate systems
- [Gait System](docs/robot/gait_system.md) - Walking patterns and gait generation
- [Movement Commands](docs/robot/movement_commands.md) - High-level movement commands

### Hardware Integration
- [Hardware Integration](docs/hardware/hardware_integration.md) - Hardware components and integration
- [Servo Control](docs/hardware/servo_control.md) - Servo control system and protocols
- [Lights System](docs/hardware/lights_system.md) - LED control and visual feedback
- [IMU Data Format](docs/hardware/imu_data_format.md) - IMU sensor data and processing

### Interface Systems
- [Task Interface](docs/interface/task_interface.md) - Central task coordination and management
- [Voice Control Interface](docs/interface/voice_control_interface.md) - Voice control system interface
- [Gamepad Controller](docs/interface/gamepad_controller.md) - Gamepad control and input handling

### Voice Control & Audio
- [Voice Control System](docs/voice/voice_control_system.md) - Voice recognition and command processing
- [Audio Recording](docs/voice/audio_recording.md) - Audio recording utilities and management

### ODAS Audio Processing
- [ODAS Audio Processing](docs/odas/odas_audio_processing.md) - Multi-channel audio capture and spatial processing
- [ODAS Server](docs/odas/odas_server.md) - ODAS server setup and configuration
- [ODAS Data Format](docs/odas/odas_data_format.md) - Data formats and protocols
- [DOA SSL Processor](docs/odas/doa_ssl_processor.md) - Direction of arrival and sound source localization
- [ODAS Audio Playback](docs/odas/odas_audio_playback.md) - ODAS audio playback utilities
- [Streaming ODAS Audio Player](docs/odas/streaming_odas_audio_player.md) - Remote audio streaming

## License

Copyright (c) 2025 Krystian Głodek <krystian.glodek1717@gmail.com>. All rights reserved. 