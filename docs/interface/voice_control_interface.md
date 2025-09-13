# Voice Control Interface

[← Previous: Task Interface](task_interface.md) | [Next: Gamepad Controller →](gamepad_controller.md)

[← Back to Documentation](../README.md)

## Table of Contents

- [Overview](#overview)
- [Voice Control System](#voice-control-system)
- [Audio Processing](#audio-processing)
- [ODAS Integration](#odas-integration)
- [Voice Commands](#voice-commands)
- [Configuration](#configuration)

---

## Overview

The voice control interface provides hands-free control of the hexapod robot through natural speech commands. The system integrates Picovoice's Porcupine wake word detection and Rhino intent recognition with a 6-microphone array for spatial audio processing and real-time response.

**Key Features**:
- **Wake Word Detection**: "Hey Hexapod" activation using Porcupine
- **Intent Recognition**: Natural language command processing with Rhino
- **Spatial Audio**: 6-microphone array for direction-aware processing
- **Real-time Response**: Low-latency voice command execution
- **Task Integration**: Seamless integration with hexapod movement tasks
- **Audio Recording**: Built-in audio recording capabilities

## Voice Control System

### **VoiceControl Class** (`src/kws/voice_control.py`)

**Role**: Main voice control system implementation
- **Threading**: Runs as daemon thread for concurrent operation
- **Picovoice Integration**: Porcupine wake word + Rhino intent recognition
- **Audio Processing**: 8-channel to single-channel audio conversion
- **Task Interface**: Direct integration with hexapod task system

**Key Components**:
- **Audio Stream**: `pyaudio` for real-time audio capture
- **Wake Word**: Porcupine for "Hey Hexapod" detection
- **Intent Recognition**: Rhino for command understanding
- **Audio Recorder**: Built-in recording capabilities

### **Intent Dispatcher** (`src/kws/intent_dispatcher.py`)

**Role**: Maps voice intents to hexapod actions
- **Intent Mapping**: 25+ voice commands mapped to actions
- **Slot Parsing**: Extracts parameters from voice commands
- **Task Execution**: Triggers appropriate hexapod tasks
- **Error Handling**: Graceful handling of unrecognized commands

**Supported Intents**:
- **System Control**: help, system_status, shut_down, wake_up, sleep
- **Movement**: move, rotate, march_in_place, idle_stance, stop
- **Advanced**: follow, sound_source_localization, calibrate
- **Entertainment**: dance, sit_up, helix, show_off, say_hello
- **Recording**: start_recording, stop_recording
- **Lights**: turn_lights, change_color, set_brightness

## Audio Processing

### **Multi-Channel Audio Capture**

**Hardware**: ReSpeaker 6-Mic Array
- **Channels**: 8 audio channels (uses first channel)
- **Sample Rate**: 16 kHz (optimized for Picovoice)
- **Format**: 16-bit PCM audio
- **Buffer Size**: 512 samples per frame

**Audio Processing Pipeline**:
1. **Raw Capture**: 8-channel audio from microphone array
2. **Channel Selection**: Extract first channel for processing
3. **Format Conversion**: Convert to Picovoice-compatible format
4. **Wake Word Detection**: Process through Porcupine
5. **Intent Recognition**: Process through Rhino if wake word detected

### **Spatial Audio Processing**

**ODAS Integration**: Sound source localization
- **Direction Detection**: Determine sound source direction
- **LED Visualization**: Visual feedback through LED strip
- **GUI Integration**: Forward data to graphical interface
- **Real-time Processing**: Continuous audio analysis

## ODAS Integration

### **ODAS Server** (`src/odas/odas_doa_ssl_processor.py`)

**Role**: Manages external ODAS process for spatial audio
- **Process Management**: Starts/stops ODAS server
- **TCP Servers**: Ports 9000 (tracked) and 9001 (potential sources)
- **Data Processing**: JSON data parsing and visualization
- **LED Control**: Visual feedback through hexapod LEDs

### **Audio Streaming** (`src/odas/streaming_odas_audio_player.py`)

**Role**: Remote audio streaming and playback
- **SSH/SFTP**: Connects to remote ODAS machine
- **File Streaming**: Streams `postfiltered.raw` and `separated.raw`
- **Audio Conversion**: Uses `sox` for raw-to-WAV conversion
- **Real-time Playback**: `sounddevice` for audio output

### **Audio Processing** (`src/odas/odas_audio_processor.py`)

**Role**: ODAS audio format processing
- **Sample Rate Conversion**: 44.1 kHz → 16 kHz
- **Channel Conversion**: 4-channel → mono
- **Frame Management**: Prepares audio for Picovoice
- **Buffer Handling**: Manages audio frame processing

## Voice Commands

### **System Control Commands**

**Basic Control**:
- **"Hey Hexapod"** - Wake word activation
- **"Help"** - Show available commands
- **"System Status"** - Display system information
- **"Shut Down"** - Power off the system
- **"Wake Up"** - Resume from sleep mode
- **"Sleep"** - Enter sleep mode

**Calibration**:
- **"Calibrate"** - Run full system calibration
- **"Repeat Last Command"** - Repeat previous command

### **Movement Commands**

**Basic Movement**:
- **"Move [direction] [cycles/duration]"** - Move in specified direction
- **"Rotate [direction] [angle/cycles/duration]"** - Rotate in place
- **"March in Place [cycles/duration]"** - March without moving
- **"Idle Stance"** - Return to neutral position
- **"Stop"** - Stop current movement

**Advanced Movement**:
- **"Follow"** - Follow sound source
- **"Sound Source Localization"** - Locate and move toward sound
- **"Dance"** - Perform dance routine
- **"Sit Up"** - Sit up movement
- **"Helix"** - Helical movement pattern
- **"Show Off"** - Demonstration routine
- **"Say Hello"** - Greeting movement

### **Recording Commands**

**Audio Recording**:
- **"Start Recording [filename]"** - Begin audio recording
- **"Stop Recording"** - End audio recording
- **"Stream ODAS Audio"** - Stream remote audio

### **Light Control Commands**

**LED Control**:
- **"Turn Lights [on/off]"** - Control LED strip
- **"Change Color [color]"** - Change LED color
- **"Set Brightness [level]"** - Adjust LED brightness
- **"Set Speed [level]"** - Adjust animation speed
- **"Set Acceleration [level]"** - Adjust movement acceleration

## Configuration

### **Picovoice Configuration**

**Wake Word Settings**:
- **Sensitivity**: 0.75 (default)
- **Model**: `hexapod_en_raspberry-pi_v3_0_0.ppn`
- **Access Key**: Required for Picovoice services

**Intent Recognition Settings**:
- **Sensitivity**: 0.25 (default)
- **Context**: `hexapod_en_raspberry-pi_v3_0_0.rhn`
- **Context Info**: Optional context information display

### **Audio Configuration**

**Microphone Settings**:
- **Device Index**: Auto-detection of ReSpeaker 6
- **Sample Rate**: 16,000 Hz
- **Channels**: 8 (uses first channel)
- **Format**: 16-bit PCM
- **Buffer Size**: 512 samples

**Recording Settings**:
- **Directory**: `data/audio/recordings`
- **Auto-split**: 30-minute segments
- **Format**: WAV files
- **Channels**: 8-channel recording

### **ODAS Configuration**

**Server Settings**:
- **Tracked Sources Port**: 9000
- **Potential Sources Port**: 9001
- **Config Files**: Located in `lib/odas/config/`
- **Process Management**: Automatic start/stop

**Streaming Settings**:
- **Remote Host**: Configurable SSH host
- **File Types**: `postfiltered.raw`, `separated.raw`
- **Conversion**: `sox` for raw-to-WAV
- **Playback**: `sounddevice` for real-time output

---

[← Previous: Task Interface](task_interface.md) | [Next: Gamepad Controller →](gamepad_controller.md)

[← Back to Documentation](../README.md)
