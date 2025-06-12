#!/usr/bin/env python3

import argparse
import wave
import numpy as np
import pvrhino
import struct
from pathlib import Path

def test_rhino_on_file(input_file: Path, access_key: str):
    """
    Test Rhino speech-to-intent on a WAV file.
    
    Args:
        input_file (Path): Path to the input WAV file
        access_key (str): Picovoice access key
    """
    # Open the WAV file
    wav_file = wave.open(str(input_file), 'rb')
    
    # Verify the WAV file format
    if wav_file.getnchannels() != 1:
        raise ValueError("WAV file must be mono")
    if wav_file.getsampwidth() != 2:
        raise ValueError("WAV file must be 16-bit")
    if wav_file.getframerate() != 16000:
        raise ValueError("WAV file must be 16000 Hz")
    
    # Get fixed path to model file
    context_path = Path(__file__).parent.parent.parent.parent / "src" / "kws" / "rhino" / "hexapod_en_raspberry-pi_v3_0_0.rhn"
    if not context_path.exists():
        raise FileNotFoundError(f"Context file not found at {context_path}")
    
    print(f"Using context file: {context_path}")
    
    # Initialize Rhino
    rhino = pvrhino.create(
        access_key=access_key,
        context_path=str(context_path)
    )
    
    # Get the frame length that Rhino expects
    frame_length = rhino.frame_length
    
    # Read and process the audio in chunks
    print(f"Processing {input_file}...")
    intent_detected = False
    
    while True:
        # Read a chunk of audio
        audio_data = wav_file.readframes(frame_length)
        if len(audio_data) == 0:
            break
        
        # Convert to 16-bit integers
        audio_frame = struct.unpack_from("h" * frame_length, audio_data)
        
        # Process the frame
        is_finalized = rhino.process(audio_frame)
        
        if is_finalized:
            # Get the inference result
            inference = rhino.get_inference()
            if inference.is_understood:
                intent_detected = True
                print("\nIntent detected:")
                print(f"Intent: {inference.intent}")
                print("Slots:")
                for slot, value in inference.slots.items():
                    print(f"  {slot}: {value}")
            else:
                print("\nCommand not understood")
    
    # Clean up
    rhino.delete()
    wav_file.close()
    
    if not intent_detected:
        print("No intents detected in the file")

def main():
    parser = argparse.ArgumentParser(description='Test Rhino speech-to-intent on a WAV file')
    parser.add_argument('input_file', type=str, help='Path to the input WAV file')
    parser.add_argument('--access-key', type=str, required=True, help='Picovoice access key')
    
    args = parser.parse_args()
    
    test_rhino_on_file(
        Path(args.input_file),
        args.access_key
    )

if __name__ == '__main__':
    main() 