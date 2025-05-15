#!/usr/bin/env python3

"""
Simple script to play raw audio files and test with Picovoice.
"""

import numpy as np
import sounddevice as sd
import argparse
from pathlib import Path
from picovoice import Picovoice

def main():
    parser = argparse.ArgumentParser(description='Play raw audio file and test with Picovoice')
    parser.add_argument('audio_file', help='Path to raw audio file')
    parser.add_argument('--access-key', help='Picovoice access key for testing')
    args = parser.parse_args()

    # Read the raw audio file
    print(f"Reading audio file: {args.audio_file}")
    with open(args.audio_file, 'rb') as f:
        audio_data = f.read()

    # Convert to numpy array (4 channels at 44.1kHz)
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    
    # Reshape to 4 channels
    audio_array = audio_array.reshape(-1, 4)
    
    # Mix down all channels (average them)
    audio_mono = np.mean(audio_array, axis=1)
    
    # Normalize audio for playback
    audio_float = audio_mono.astype(np.float32) / 32768.0

    # Play the audio at original sample rate
    print("Playing audio at 44100 Hz...")
    sd.play(audio_float, 44100)
    sd.wait()  # Wait for playback to finish
    print("Done playing audio")

    if args.access_key:
        print("\nTesting with Picovoice...")
        # Get paths to model files
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

        # Resample to 16kHz for Picovoice
        from scipy import signal
        audio_16k = signal.resample_poly(audio_mono, 16000, 44100).astype(np.int16)

        # Process in chunks
        frame_length = picovoice.frame_length
        print(f"Processing audio in frames of {frame_length} samples")
        
        for i in range(0, len(audio_16k), frame_length):
            frame = audio_16k[i:i + frame_length]
            if len(frame) < frame_length:
                # Pad last frame if needed
                frame = np.pad(frame, (0, frame_length - len(frame)))
            
            picovoice.process(frame)

        picovoice.delete()
        print("\nDone processing with Picovoice")

if __name__ == "__main__":
    main() 