#!/usr/bin/env python3

"""
Utility for playing raw audio files from ODAS.

ODAS Audio Formats:
1. Raw Input (from microphones):
   - Sample rate: 16000 Hz
   - Channels: 8 (ReSpeaker 6 Mic Array)
   - Bit depth: 32-bit

2. Postfiltered/Separated Output:
   - Sample rate: 44100 Hz
   - Channels: 4
   - Bit depth: 16-bit
"""

import numpy as np
import sounddevice as sd
import argparse
from pathlib import Path


def play_raw_audio(
    audio_file: Path, sample_rate: int = 44100, channels: int = 4, bit_depth: int = 16
) -> None:
    """
    Play a raw audio file.

    Args:
        audio_file (Path): Path to the raw audio file
        sample_rate (int): Sample rate of the audio (default: 44100 Hz for postfiltered/separated)
        channels (int): Number of channels in the audio (default: 4 for postfiltered/separated)
        bit_depth (int): Bit depth of the audio (default: 16 for postfiltered/separated)
    """
    # Read the raw audio file
    print(f"Reading audio file: {audio_file}")
    with open(audio_file, "rb") as f:
        audio_data = f.read()

    # Convert to numpy array based on bit depth
    if bit_depth == 16:
        dtype = np.int16
    elif bit_depth == 32:
        dtype = np.int32
    else:
        raise ValueError(f"Unsupported bit depth: {bit_depth}. Must be 16 or 32.")

    audio_array = np.frombuffer(audio_data, dtype=dtype)

    # Reshape to channels
    audio_array = audio_array.reshape(-1, channels)

    # Mix down all channels (average them)
    audio_mono = np.mean(audio_array, axis=1)

    # Normalize audio for playback
    max_value = float(2 ** (bit_depth - 1) - 1)
    audio_float = audio_mono.astype(np.float32) / max_value

    # Play the audio at original sample rate
    print(f"Playing audio at {sample_rate} Hz...")
    sd.play(audio_float, sample_rate)
    sd.wait()  # Wait for playback to finish
    print("Done playing audio")


def main():
    parser = argparse.ArgumentParser(description="Play raw audio file from ODAS")
    parser.add_argument("audio_file", help="Path to raw audio file")
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=44100,
        help="Sample rate (default: 44100 Hz for postfiltered/separated)",
    )
    parser.add_argument(
        "--channels",
        type=int,
        default=4,
        help="Number of channels (default: 4 for postfiltered/separated)",
    )
    parser.add_argument(
        "--bit-depth",
        type=int,
        default=16,
        choices=[16, 32],
        help="Bit depth (default: 16 for postfiltered/separated)",
    )

    args = parser.parse_args()

    play_raw_audio(
        Path(args.audio_file), args.sample_rate, args.channels, args.bit_depth
    )


if __name__ == "__main__":
    main()
