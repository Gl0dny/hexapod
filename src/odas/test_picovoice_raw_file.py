#!/usr/bin/env python3

"""
Test script to verify Picovoice can process raw audio files.
"""

import numpy as np
from pathlib import Path
from picovoice import Picovoice
import argparse
import sounddevice as sd
import time

def main():
    parser = argparse.ArgumentParser(description='Test Picovoice with raw audio file')
    parser.add_argument('--access-key', required=True, help='Picovoice access key')
    parser.add_argument('--audio-file', required=True, help='Path to raw audio file')
    parser.add_argument('--sample-rate', type=int, default=16000, help='Audio sample rate')
    parser.add_argument('--channels', type=int, default=1, help='Number of audio channels')
    parser.add_argument('--play', action='store_true', help='Play the audio while processing')
    args = parser.parse_args()

    # Get fixed paths to model files
    keyword_path = Path(__file__).parent.parent / "kws" / "porcupine" / "hexapod_en_raspberry-pi_v3_0_0.ppn"
    context_path = Path(__file__).parent.parent / "kws" / "rhino" / "hexapod_en_raspberry-pi_v3_0_0.rhn"

    if not keyword_path.exists():
        raise FileNotFoundError(f"Keyword file not found at {keyword_path}")
    if not context_path.exists():
        raise FileNotFoundError(f"Context file not found at {context_path}")

    print(f"Using keyword file: {keyword_path}")
    print(f"Using context file: {context_path}")

    # Initialize Picovoice
    def wake_word_callback():
        print("\nWake word 'hexapod' detected!")

    def inference_callback(inference):
        if inference.is_understood:
            print("\nIntent detected:")
            print(f"Intent: {inference.intent}")
            print("Slots:")
            for slot, value in inference.slots.items():
                print(f"  {slot}: {value}")
        else:
            print("\nCommand not understood")

    picovoice = Picovoice(
        access_key=args.access_key,
        keyword_path=str(keyword_path),
        wake_word_callback=wake_word_callback,
        context_path=str(context_path),
        inference_callback=inference_callback,
        porcupine_sensitivity=0.75,
        rhino_sensitivity=0.25
    )

    # Read and process the audio file
    print(f"Reading audio file: {args.audio_file}")
    with open(args.audio_file, 'rb') as f:
        audio_data = f.read()

    # Convert to numpy array
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    
    # If stereo, convert to mono
    if args.channels > 1:
        audio_array = audio_array.reshape(-1, args.channels)
        audio_array = audio_array[:, 0]  # Take first channel

    # Normalize audio for playback
    audio_float = audio_array.astype(np.float32) / 32768.0

    # Process in chunks of frame_length
    frame_length = picovoice.frame_length
    print(f"Processing audio in frames of {frame_length} samples")
    
    if args.play:
        print("Playing audio...")
        sd.play(audio_float, args.sample_rate)
    
    for i in range(0, len(audio_array), frame_length):
        frame = audio_array[i:i + frame_length]
        if len(frame) < frame_length:
            # Pad last frame if needed
            frame = np.pad(frame, (0, frame_length - len(frame)))
        
        picovoice.process(frame)
        
        # Add small delay to match real-time processing
        if args.play:
            time.sleep(frame_length / args.sample_rate)

    if args.play:
        sd.wait()  # Wait for playback to finish

    picovoice.delete()
    print("\nDone processing audio file")

if __name__ == "__main__":
    main() 