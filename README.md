## Thesis : "Hexapod autonomous control system based on auditory scene analysis: real-time sound source localization and keyword spotting for voice command recognition"
--- In progress

Diploma project completed at Warsaw University of Science and Technology as a part of Master of Science - Computer Science.

This project aims to develop an autonomous control system for a hexapod walking robot, using auditory scene analysis as the primary modality for navigation and environmental interaction. The system integrates sound source localization (Direction of Arrival estimation - DOA) and beamforming techniques via the ODAS framework, employing a circular microphone array for enhanced spatial precision. This enables the robot to accurately detect and characterize sound sources, allowing real-time responses to acoustic stimuli for dynamic, context-aware behavior.

A Keyword Spotting (KWS) module, powered by machine learning, is incorporated to recognize predefined voice commands, enabling effective human-robot interaction. The research focuses on developing the hardware and software infrastructure to seamlessly integrate acoustic processing with the robot's control system.

The project includes designing and building the robot's platform, encompassing both the mechanical structure and embedded systems. The hexapod's platform is engineered to support advanced auditory processing, ensuring optimal performance in real-world scenarios. This involves creating a robust mechanical framework for stable, agile locomotion and an embedded system architecture for real-time processing and decision-making.

The hardware is designed to accommodate the circular microphone array, ensuring precise sound capture, while the software facilitates seamless communication between auditory processing modules, the control system, and actuators. This comprehensive approach ensures the robot can perform complex tasks, such as navigating dynamic environments and responding accurately to auditory cues.

![](./assets/hexapod_alum.jpg)

## Implementation Details

### Hardware Configuration
- Raspberry Pi 4 (8GB) running Raspberry Pi OS
- 6x MG996R servo motors
- Pololu Maestro 24-Channel USB Servo Controller
- ReSpeaker 6-Mic Circular Array
- ICM-20948 IMU
- WS2812B LED strip (30 LEDs)
- 5V 10A power supply

### Software Stack
- Python 3.8+
- ODAS v1.0.0 for audio processing
- Picovoice Porcupine v2.1.3 for wake word detection
- Picovoice Rhino v2.1.1 for command recognition
- RPi.GPIO v0.7.1 for hardware control
- NumPy v2.1.2 for numerical computations

### Core Systems

#### Audio Processing Pipeline
```
Microphone Array (6 channels)
    ↓
ODAS Processing
    ↓
DOA Estimation (16 directions)
    ↓
Beamforming
    ↓
Command Processing
```

- Sample rate: 16kHz
- Buffer size: 512 samples
- Processing latency: ~32ms
- DOA resolution: 22.5°

#### Voice Control System
- Wake word: "Hey Hexapod"
- Command vocabulary: 15 custom commands
- Context file: `src/kws/rhino/hexapod_en_raspberry-pi_v3_0_0.rhn`
- Wake word model: `src/kws/porcupine/hexapod_en_raspberry-pi_v3_0_0.ppn`
- Intent configuration: `src/kws/intent.yml`
  ```yaml
  intents:
    move:
      patterns:
        - "move {direction} {speed}"
        - "go {direction} {speed}"
      parameters:
        direction: [forward, backward, left, right]
        speed: [slow, normal, fast]
    
    rotate:
      patterns:
        - "turn {direction} {angle}"
        - "rotate {direction} {angle}"
      parameters:
        direction: [left, right]
        angle: [45, 90, 180]
    
    stop:
      patterns:
        - "stop"
        - "halt"
        - "freeze"
    
    home:
      patterns:
        - "go home"
        - "return to home"
        - "home position"
  ```

#### Movement Control
- Servo update rate: 50Hz
- Gait patterns:
  - Tripod (default)
  - Wave
  - Custom
- Leg configuration:
  - 3 DOF per leg
  - 18 servos total
  - Maestro controller channels: 0-17

#### Sensor Integration
- IMU sampling rate: 100Hz
- Sensor fusion: Madgwick algorithm
- Orientation output: Quaternion
- Calibration: Auto-calibration on startup

### Project Structure
```
src/
├── robot/           # Core movement control
│   ├── gait.py     # Gait pattern generation
│   ├── leg.py      # Leg control and IK
│   └── servo.py    # Servo interface
├── kws/            # Voice recognition
│   ├── porcupine/  # Wake word models
│   └── rhino/      # Command models
├── odas/           # Audio processing
│   ├── config/     # ODAS configuration
│   └── processing/ # Audio pipeline
├── control/        # High-level control
├── imu/            # IMU interface
└── lights/         # LED control
```

### Key Dependencies
```python
# Core dependencies
numpy==2.1.2
picovoice==2.1.1
pvporcupine==2.1.3
pvrhino==2.1.1
RPi.GPIO==0.7.1
icm20948==1.0.0

# Audio processing
PyAudio==0.2.14
webrtc-audio-processing==0.1.3
webrtcvad==2.0.10

# Hardware control
gpiozero==2.0.1
lgpio==0.2.2.0
```

### Development Environment
- IDE: VSCode with Python extension
- Version control: Git
- Testing: pytest
- Documentation: MkDocs
- Code style: PEP 8
- Type checking: mypy

### Build and Run
```bash
# Install dependencies
pip install -r requirements.txt

# Run with ODAS
python main.py --access-key "YOUR_PICOVOICE_KEY" --use-odas

# Run without ODAS (direct mic input)
python main.py --access-key "YOUR_PICOVOICE_KEY"
```

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test suite
pytest tests/test_robot.py
pytest tests/test_audio.py
pytest tests/test_imu.py
```

### Logging
- Log directory: `logs/`
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Log format: JSON with timestamps
- Rotation: Daily with 7-day retention

## License

Copyright (c) 2025 Krystian Głodek <krystian.glodek1717@gmail.com>. All rights reserved.
