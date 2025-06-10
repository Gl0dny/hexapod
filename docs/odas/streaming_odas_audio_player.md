# Streaming ODAS Audio Player

## Overview

The Streaming ODAS Audio Player is a Python utility that enables real-time monitoring of ODAS (Open embeddeD Audition System) audio streams from a remote machine. It continuously monitors ODAS audio streams, transfers new audio data, and plays it locally in real-time with minimal latency.

## Features

- Real-time streaming of ODAS audio from a remote machine
- Support for both post-filtered and separated audio streams
- Low-latency audio playback using sounddevice
- Automatic channel mixing for multi-channel audio
- Efficient data transfer (only transfers new audio data)
- Robust error handling and recovery
- Configurable parameters for customization

## Audio Stream Types

ODAS creates two types of continuous raw audio streams:

1. **Post-filtered Audio** (`postfiltered.raw`)
   - Optimized for listening
   - Contains the main audio stream after processing
   - Default stream type

2. **Separated Audio** (`separated.raw`)
   - Contains separated audio streams
   - One stream for each detected sound source
   - Useful for source separation analysis

## Technical Details

### Audio Format

- **Sample Rate**: 44100 Hz (default)
- **Channels**: 4 (default)
- **Bit Depth**: 16-bit
- **Output**: Mono (mixed down from multi-channel)

### Streaming Process

1. **Remote Monitoring**
   - Connects to remote machine via SSH
   - Monitors specified directory for ODAS audio files
   - Detects new audio data by tracking file size changes

2. **Data Transfer**
   - Transfers only new audio data
   - Uses SFTP for efficient file transfer
   - Maintains temporary local files for processing

3. **Audio Processing**
   - Converts raw audio to WAV format
   - Mixes down multi-channel audio to mono
   - Normalizes audio for playback
   - Splits audio into 1024-sample chunks

4. **Playback System**
   - Uses sounddevice for low-latency playback
   - Implements streaming callback system
   - Maintains audio queue for smooth playback
   - Processes audio in real-time

## Usage

### Command Line Arguments

```bash
python streaming_odas_audio_player.py [options]
```

Options:
- `--host`: Remote host address (default: 192.168.0.122)
- `--user`: Remote username (default: hexapod)
- `--remote-dir`: Remote directory containing ODAS audio files
- `--local-dir`: Local directory to store audio files
- `--sample-rate`: Audio sample rate (default: 44100)
- `--channels`: Number of audio channels (default: 4)
- `--ssh-key`: Path to SSH private key
- `--buffer-size`: Buffer size for audio processing (default: 1024)
- `--check-interval`: Interval to check for new audio data (default: 0.5)
- `--file-type`: Type of audio file to play (postfiltered, separated, or both)
- `--log-dir`: Directory to store logs
- `--log-config-file`: Path to log configuration file
- `--clean`: Clean all logs in the logs directory

### Example Usage

```bash
# Play post-filtered audio with default settings
python streaming_odas_audio_player.py

# Play separated audio with custom settings
python streaming_odas_audio_player.py --file-type separated --sample-rate 48000 --channels 8

# Play both audio types with custom remote settings
python streaming_odas_audio_player.py --file-type both --host 192.168.1.100 --user custom_user
```

## Requirements

- Python 3.x
- Required Python packages:
  - paramiko (for SSH/SFTP)
  - sounddevice (for audio playback)
  - numpy (for audio processing)
  - sox (for audio conversion)

## Error Handling

The player includes robust error handling for:
- Network disconnections
- File access issues
- Audio processing errors
- Playback problems

It will automatically:
- Attempt to reconnect on network issues
- Clean up temporary files
- Recover from audio processing errors
- Gracefully shut down on keyboard interrupt

## Performance Considerations

- **Latency**: Typically < 100ms
- **CPU Usage**: Moderate (depends on audio processing load)
- **Memory Usage**: Low (streams audio in chunks)
- **Network Usage**: Efficient (only transfers new data)