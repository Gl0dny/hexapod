# Sound Source Localization (SSL) Utilities

This document describes the Sound Source Localization (SSL) utilities available in the `src/utils/audio/ssl` directory. These utilities provide alternative implementations for Direction of Arrival (DOA) estimation using the ReSpeaker 6-Mic Array.

> **Related Documentation:**
> - [Audio Recording](audio_recording.md) - For recording audio data
> - [ODAS Server](../odas/odas_server.md) - Main DOA implementation
> - [ODAS Data Format](../odas/odas_data_format.md) - Data format specifications

## Prerequisites

Before using these utilities, ensure you have the required dependencies installed:

```bash
# Python dependencies
pip install pyaudio numpy webrtcvad matplotlib
```

## Available Components

### 1. GCC-PHAT Implementation (`gcc_phat.py`)

A Python implementation of the Generalized Cross Correlation - Phase Transform (GCC-PHAT) algorithm for DOA estimation.

**Features:**
- Time delay estimation between microphone pairs
- Uses FFT for efficient computation
- Supports interpolation for higher accuracy
- Configurable parameters for fine-tuning

**Usage:**
```python
from src.utils.audio.ssl.gcc_phat import GCCPhat

# Initialize the GCC-PHAT estimator
estimator = GCCPhat(
    sample_rate=16000,
    mic_positions=mic_positions,  # Array of microphone positions
    interpolation_factor=4        # Optional: for higher accuracy
)

# Estimate DOA from audio data
doa = estimator.estimate_doa(audio_data)
```

### 2. Microphone Array Handler (`mic_array.py`)

A class for handling the ReSpeaker 6-Mic Array, including audio capture and real-time processing.

**Features:**
- Audio capture from multiple channels
- Real-time processing capabilities
- Integration with GCC-PHAT for DOA estimation
- Configurable buffer sizes and processing parameters

**Usage:**
```python
from src.utils.audio.ssl.mic_array import MicArray

# Initialize the microphone array
mic_array = MicArray(
    sample_rate=16000,
    channels=8,
    chunk_size=1024
)

# Start real-time DOA estimation
mic_array.start_doa_estimation(callback=process_doa)
```

### 3. VAD with DOA (`vad_doa.py`)

Combines Voice Activity Detection (VAD) with DOA estimation for more accurate sound source localization.

**Features:**
- Uses WebRTC VAD for speech detection
- Integrates with microphone array for DOA
- Includes visualization support
- Configurable VAD sensitivity

**Usage:**
```python
from src.utils.audio.ssl.vad_doa import VADDOA

# Initialize VAD-DOA system
vad_doa = VADDOA(
    sample_rate=16000,
    vad_mode=3,  # VAD aggressiveness (0-3)
    mic_positions=mic_positions
)

# Process audio and get DOA estimates
doa_estimates = vad_doa.process_audio(audio_data)
```

## Integration with ODAS

While the main project uses ODAS for DOA estimation, these utilities can be used as:

1. **Reference Implementation**
   - Understanding DOA algorithms
   - Testing and validation
   - Educational purposes

2. **Fallback Option**
   - When ODAS is not available
   - For specific use cases
   - During development and testing

3. **Custom Processing**
   - When specific modifications are needed
   - For research and experimentation
   - For specialized applications

## Configuration

### GCC-PHAT Parameters
- `sample_rate`: Audio sample rate (default: 16000 Hz)
- `mic_positions`: Array of microphone positions
- `interpolation_factor`: FFT interpolation factor (default: 4)

### Microphone Array Parameters
- `sample_rate`: Audio sample rate (default: 16000 Hz)
- `channels`: Number of channels (default: 8)
- `chunk_size`: Processing buffer size (default: 1024)

### VAD-DOA Parameters
- `sample_rate`: Audio sample rate (default: 16000 Hz)
- `vad_mode`: VAD aggressiveness (0-3)
- `mic_positions`: Array of microphone positions

## Notes

- These utilities are provided as alternatives to ODAS
- They may have different performance characteristics
- Consider using them for specific use cases or as learning resources
- The main project's primary DOA implementation is ODAS 