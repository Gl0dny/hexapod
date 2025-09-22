# Scripts Directory

This directory contains interactive scripts and demos for testing and demonstrating hexapod functionality, organized by category.

## Directory Structure

```
scripts/
├── movement/           # Movement and kinematics testing
├── voice_control/      # Voice control and speech recognition testing
├── audio/             # Audio recording and playback utilities
└── README.md          # This file
```

## Script Categories

### Movement & Kinematics (`movement/`)
- `interactive_body_ik.py` - Interactive body inverse kinematics testing
- `gait_generator_tester.py` - Gait generation testing and demonstration
- `leg_workspace.py` - Leg workspace analysis and 3D visualization

### Voice Control Testing (`voice_control/`)
- `test_picovoice_file.py` - Picovoice file-based testing
- `test_picovoice_raw_file.py` - Picovoice raw audio file testing
- `test_porcupine_file.py` - Porcupine wake word file testing
- `test_rhino_file.py` - Rhino intent recognition file testing

### Audio Utilities (`audio/`)
- `record/` - Audio recording utilities for ReSpeaker 6-Mic Array
  - `record.py` - Basic multi-channel recording
  - `record_channels.py` - Multi-channel recording with separate files
  - `record_single_channel.py` - Single channel recording
  - `identify_audio_devices.py` - Audio device identification
- `playback/` - Audio playback and conversion utilities
  - `play_wav_audio.py` - WAV file playback and conversion
  - `play_raw_audio.py` - Raw audio file playback

## Usage

```bash
# Movement scripts
python scripts/movement/script_name.py

# Voice control scripts  
python scripts/voice_control/script_name.py

# Audio utilities
python scripts/audio/record/script_name.py
python scripts/audio/playback/script_name.py
```
