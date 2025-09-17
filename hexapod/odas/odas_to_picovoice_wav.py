#!/usr/bin/env python3

"""
ODAS to Picovoice WAV Converter

This module provides utilities to convert ODAS raw audio files to WAV format
compatible with Picovoice voice control systems. It handles sample rate conversion,
channel selection, and format conversion for seamless integration with the
voice control pipeline.
"""

import argparse
import wave
import numpy as np
import time
from pathlib import Path
import tempfile
import sys

from odas import ODASAudioProcessor


def convert_odas_to_wav(
    input_file: Path,
    output_file: Path,
    sample_rate: int = 44100,
    channels: int = 4,
    selected_channel: int = 0,
) -> None:
    """
    Convert ODAS raw audio file to WAV format compatible with Picovoice.

    Args:
        input_file (Path): Path to the input ODAS raw file
        output_file (Path): Path to save the output WAV file
        sample_rate (int): Input sample rate (default: 44100)
        channels (int): Number of input channels (default: 4)
        selected_channel (int): Channel to extract (default: 0)
    """
    # Create a temporary directory for ODASAudioProcessor
    with tempfile.TemporaryDirectory() as temp_dir:
        odas_input = ODASAudioProcessor(
            odas_dir=Path(temp_dir),
            sample_rate=sample_rate,
            channels=channels,
            selected_channel=selected_channel,
        )

    # Open output WAV file
    wav_file = wave.open(str(output_file), "wb")
    wav_file.setnchannels(1)  # Mono
    wav_file.setsampwidth(2)  # 16-bit
    wav_file.setframerate(16000)  # Picovoice sample rate

    # Buffer to store converted audio
    converted_audio = []
    last_file_size = 0
    no_change_count = 0

    def audio_callback(audio_data: np.ndarray) -> None:
        # Store the converted audio data
        converted_audio.append(audio_data.tobytes())

    # Set up the callback
    odas_input.set_audio_callback(audio_callback)

    # Start reading and converting
    odas_input.start()

    # Wait for conversion to complete with timeout
    start_time = time.time()
    timeout = 30  # 30 seconds timeout

    while odas_input.running:
        current_file_size = input_file.stat().st_size

        # Check if file size hasn't changed
        if current_file_size == last_file_size:
            no_change_count += 1
            if no_change_count >= 5:  # If no change for 5 iterations
                print("No new data detected, stopping conversion...")
                break
        else:
            no_change_count = 0
            last_file_size = current_file_size

        # Check timeout
        if time.time() - start_time > timeout:
            print("Timeout reached, stopping conversion...")
            break

        time.sleep(0.1)  # Small delay to prevent CPU hogging

    # Stop the ODASAudioProcessor
    odas_input.stop()

    # Write all converted audio to the WAV file
    for audio_chunk in converted_audio:
        wav_file.writeframes(audio_chunk)

    # Close the WAV file
    wav_file.close()

    print(f"Successfully converted {input_file} to {output_file}")
    print(f"Output format: 16000 Hz, mono, 16-bit PCM")
    print(f"Converted {len(converted_audio)} chunks of audio")


def main() -> None:
    # Add project paths for imports when run as script
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent
    src_path = project_root / "src"

    if str(project_root) not in sys.path:
        sys.path.append(str(project_root))
    if str(src_path) not in sys.path:
        sys.path.append(str(src_path))

    parser = argparse.ArgumentParser(
        description="Convert ODAS raw audio to WAV format compatible with Picovoice"
    )
    parser.add_argument("input_file", type=str, help="Path to the input ODAS raw file")
    parser.add_argument(
        "output_file", type=str, help="Path to save the output WAV file"
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=44100,
        help="Input sample rate (default: 44100)",
    )
    parser.add_argument(
        "--channels", type=int, default=4, help="Number of input channels (default: 4)"
    )
    parser.add_argument(
        "--channel", type=int, default=0, help="Channel to extract (default: 0)"
    )

    args = parser.parse_args()

    convert_odas_to_wav(
        Path(args.input_file),
        Path(args.output_file),
        args.sample_rate,
        args.channels,
        args.channel,
    )


if __name__ == "__main__":
    main()
