#!/usr/bin/env python3

"""
Utility for playing WAV files and optionally converting raw ODAS audio to WAV.

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
import wave
from pathlib import Path


def convert_raw_to_wav(
    input_file: Path,
    output_file: Path,
    sample_rate: int = 44100,  # Default for postfiltered/separated
    channels: int = 4,  # Default for postfiltered/separated
    bit_depth: int = 16,  # Default for postfiltered/separated
) -> None:
    """
    Convert raw audio file to WAV format using ODAS postfiltered/separated defaults.

    Args:
        input_file (Path): Path to the raw audio file
        output_file (Path): Path to save the WAV file
        sample_rate (int): Sample rate of the raw audio (default: 44100 Hz)
        channels (int): Number of channels in the raw audio (default: 4)
        bit_depth (int): Bit depth of the raw audio (default: 16)
    """
    print(f"Converting {input_file} to WAV format...")
    print(
        f"Using ODAS postfiltered/separated defaults: {sample_rate} Hz, {channels} channels, {bit_depth}-bit"
    )

    # Read the raw audio file
    with open(input_file, "rb") as f:
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

    # Convert to 16-bit PCM for WAV
    audio_mono = np.clip(audio_mono, -32768, 32767).astype(np.int16)

    # Write WAV file
    with wave.open(str(output_file), "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_mono.tobytes())

    print(f"Conversion complete. WAV file saved to: {output_file}")


def play_wav_file(wav_file: Path):
    """
    Play a WAV file.

    Args:
        wav_file (Path): Path to the WAV file
    """
    print(f"Playing WAV file: {wav_file}")

    # Read WAV file
    with wave.open(str(wav_file), "rb") as wav:
        # Get WAV parameters
        n_channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        frame_rate = wav.getframerate()
        n_frames = wav.getnframes()

        print(f"Format: {n_channels} channels, {sample_width*8}-bit, {frame_rate} Hz")

        # Read all frames
        audio_data = wav.readframes(n_frames)

        # Convert to numpy array
        dtype = np.int16 if sample_width == 2 else np.int32
        audio_array = np.frombuffer(audio_data, dtype=dtype)

        # Reshape to channels
        audio_array = audio_array.reshape(-1, n_channels)

        # Mix down all channels (average them)
        audio_mono = np.mean(audio_array, axis=1)

        # Normalize audio for playback
        max_value = float(2 ** (sample_width * 8 - 1) - 1)
        audio_float = audio_mono.astype(np.float32) / max_value

        # Play the audio
        print(f"Playing audio at {frame_rate} Hz...")
        sd.play(audio_float, frame_rate)
        sd.wait()  # Wait for playback to finish
        print("Done playing audio")


def main():
    parser = argparse.ArgumentParser(
        description="Play WAV files and optionally convert raw ODAS audio to WAV"
    )
    parser.add_argument("audio_file", help="Path to audio file (WAV or raw)")
    parser.add_argument(
        "--convert", action="store_true", help="Convert raw file to WAV before playing"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output WAV file path (required if --convert is used)",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=44100,
        help="Sample rate for raw files (default: 44100 Hz for postfiltered/separated)",
    )
    parser.add_argument(
        "--channels",
        type=int,
        default=4,
        help="Number of channels for raw files (default: 4 for postfiltered/separated)",
    )
    parser.add_argument(
        "--bit-depth",
        type=int,
        default=16,
        choices=[16, 32],
        help="Bit depth for raw files (default: 16 for postfiltered/separated)",
    )

    args = parser.parse_args()

    input_path = Path(args.audio_file)

    # Check if file exists
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        return

    # Handle raw file conversion if requested
    if args.convert:
        if not args.output:
            print("Error: --output argument is required when using --convert")
            return

        output_path = Path(args.output)
        if output_path.suffix.lower() != ".wav":
            output_path = output_path.with_suffix(".wav")

        # Use default ODAS postfiltered/separated settings
        convert_raw_to_wav(
            input_path,
            output_path,
            args.sample_rate,  # Default: 44100 Hz
            args.channels,  # Default: 4 channels
            args.bit_depth,  # Default: 16-bit
        )

        # Play the converted WAV file
        play_wav_file(output_path)
    else:
        # Check if input is WAV
        if input_path.suffix.lower() != ".wav":
            print("Error: Input file must be WAV format. Use --convert for raw files.")
            return

        # Play WAV file directly
        play_wav_file(input_path)


if __name__ == "__main__":
    main()
