# Audio Utilities

This directory contains various audio processing utilities for the hexapod project, including recording utilities.

## Directory Structure

```
audio/
├── record/              # Audio recording utilities
│   ├── record.py        # Basic multi-channel recording
│   ├── record_channels.py    # Record each channel separately
│   ├── record_single_channel.py  # Record single channel
│   └── identify_audio_devices.py # List available audio devices
```

## Recording Utilities

The `record` directory contains utilities for recording audio from the ReSpeaker 6-Mic Array:

- `record.py`: Basic multi-channel recording
- `record_channels.py`: Record each channel to separate files
- `record_single_channel.py`: Record from a single channel
- `identify_audio_devices.py`: List available audio devices

See `record/README.md` for detailed usage instructions.

## Dependencies

- PyAudio
- NumPy

## Integration with Main Project

These utilities provide audio recording capabilities for the hexapod project and can be used for:
1. Testing and debugging
2. Learning about audio processing
3. Custom recording needs 