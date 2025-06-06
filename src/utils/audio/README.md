# Audio Utilities

This directory contains various audio processing utilities for the hexapod project, including recording and Direction of Arrival (DOA) estimation.

## Directory Structure

```
audio/
├── record/              # Audio recording utilities
│   ├── record.py        # Basic multi-channel recording
│   ├── record_channels.py    # Record each channel separately
│   ├── record_single_channel.py  # Record single channel
│   └── identify_audio_devices.py # List available audio devices
└── ssl/                 # Sound Source Localization utilities
    ├── gcc_phat.py      # GCC-PHAT DOA implementation
    ├── mic_array.py     # Microphone array handling
    └── vad_doa.py       # Voice Activity Detection with DOA
```

## Recording Utilities

The `record` directory contains utilities for recording audio from the ReSpeaker 6-Mic Array:

- `record.py`: Basic multi-channel recording
- `record_channels.py`: Record each channel to separate files
- `record_single_channel.py`: Record from a single channel
- `identify_audio_devices.py`: List available audio devices

See `record/README.md` for detailed usage instructions.

## Sound Source Localization (SSL)

The `ssl` directory contains utilities for Direction of Arrival (DOA) estimation and sound source localization:

### GCC-PHAT Implementation (`ssl/gcc_phat.py`)

A Python implementation of the Generalized Cross Correlation - Phase Transform (GCC-PHAT) algorithm for DOA estimation.

**Features:**
- Time delay estimation between microphone pairs
- Uses FFT for efficient computation
- Supports interpolation for higher accuracy

### Microphone Array Handler (`ssl/mic_array.py`)

A class for handling the ReSpeaker 6-Mic Array, including:
- Audio capture from multiple channels
- Real-time processing
- DOA estimation using GCC-PHAT

### VAD with DOA (`ssl/vad_doa.py`)

Combines Voice Activity Detection (VAD) with DOA estimation:
- Uses WebRTC VAD for speech detection
- Integrates with microphone array for DOA
- Includes visualization support

## Usage Notes

- These utilities are provided as alternatives to the main ODAS implementation
- They can be used for:
  - Testing and debugging
  - Learning about audio processing
  - Fallback implementations
  - Custom processing needs

## Dependencies

- PyAudio
- NumPy
- WebRTC VAD (for vad_doa.py)
- Matplotlib (for visualization)

## Integration with Main Project

The main project uses ODAS for DOA estimation, but these utilities can be used as:
1. Reference implementations
2. Testing tools
3. Fallback options
4. Learning resources

See the main project documentation for details on the primary ODAS implementation. 