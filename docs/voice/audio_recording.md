# Audio Recording Utilities

[← Previous: Voice Control System](voice_control_system.md) | [Next: ODAS Audio Processing System →](../odas/odas_audio_processing.md)

[← Back to Documentation](../README.md)

This document describes the audio recording utilities available in the `src/utils/audio/record` directory. These utilities are designed to work with the ReSpeaker 6-Mic Array and provide different ways to record audio data.

## Prerequisites

Before using these utilities, ensure you have the required dependencies installed:

```bash
# System dependencies (macOS)
brew install portaudio

# Python dependencies
pip install pyaudio numpy
```

## Available Scripts

### 1. Basic Recording (`record.py`)

The simplest recording utility that captures all 8 channels into a single WAV file.

**Features:**
- Records all 8 channels simultaneously
- Saves raw audio data without processing
- Output: Single 8-channel WAV file (`output.wav`)

**Usage:**
```python
from src.utils.audio.record.record import record_audio

# Record 5 seconds of audio
record_audio(seconds=5, output_file="output.wav")
```

### 2. Multi-Channel Recording (`record_channels.py`)

Records from all 8 channels and saves each channel to a separate WAV file.

**Features:**
- Records all 8 channels simultaneously
- Saves each channel to a separate file
- Uses numpy for efficient data processing
- Output: Eight 1-channel WAV files (`output_channel_0.wav` through `output_channel_7.wav`)

**Usage:**
```python
from src.utils.audio.record.record_channels import record_channels

# Record 5 seconds of audio from all channels
record_channels(seconds=5, output_template="output_channel_{}.wav")
```

### 3. Single Channel Recording (`record_single_channel.py`)

Records from all 8 channels but extracts and saves only one selected channel.

**Features:**
- Records from all 8 channels
- Extracts and saves only one channel (default: channel 0)
- Uses numpy for efficient data processing
- Output: Single 1-channel WAV file (`output_one_channel.wav`)

**Usage:**
```python
from src.utils.audio.record.record_single_channel import record_single_channel

# Record 5 seconds of audio from channel 0
record_single_channel(seconds=5, channel=0, output_file="output_one_channel.wav")
```

## Common Parameters

All recording utilities share these common parameters:

- `RESPEAKER_RATE`: 16000 Hz (sample rate)
- `RESPEAKER_CHANNELS`: 8 (number of channels)
- `RESPEAKER_WIDTH`: 2 (16-bit audio)
- `CHUNK`: 1024 (samples per buffer)
- `RECORD_SECONDS`: 5 (default recording duration)

## Device Selection

To identify the correct audio device index for your ReSpeaker:

```python
from src.utils.audio.record.identify_audio_devices import list_audio_devices

# List all available audio devices
list_audio_devices()
```

## Use Cases

1. **Basic Recording (`record.py`)**
   - When you need raw multi-channel audio
   - For simple recording without channel separation
   - When working with audio processing tools that expect multi-channel input

2. **Multi-Channel Recording (`record_channels.py`)**
   - When you need to analyze each microphone separately
   - For channel-specific processing or analysis
   - When working with single-channel audio tools

3. **Single Channel Recording (`record_single_channel.py`)**
   - When you only need one microphone's data
   - For focused audio analysis on a specific channel
   - When working with single-channel audio processing

## Notes

- All recordings are saved in WAV format
- Sample rate is fixed at 16kHz
- Audio is recorded in 16-bit format
- The ReSpeaker 6-Mic Array must be properly connected and configured
- Make sure to select the correct device index for your setup

---

[← Previous: Voice Control System](voice_control_system.md) | [Next: ODAS Audio Processing System →](../odas/odas_audio_processing.md)

[← Back to Documentation](../README.md)