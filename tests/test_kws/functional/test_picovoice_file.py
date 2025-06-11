#!/usr/bin/env python3

import argparse
import wave
import numpy as np
import struct
from pathlib import Path
from picovoice import Picovoice

def test_picovoice_on_file(input_file: Path, access_key: str):
    """
    Test complete Picovoice pipeline (wake word + intent) on a WAV file.
    
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
    
    # Get the paths to the keyword and context files
    keyword_path = Path(__file__).parent.parent.parent.parent / "src" / "kws" / "porcupine" / "hexapod_en_raspberry-pi_v3_0_0.ppn"
    context_path = Path(__file__).parent.parent.parent.parent / "src" / "kws" / "rhino" / "hexapod_en_raspberry-pi_v3_0_0.rhn"
    
    if not keyword_path.exists():
        raise FileNotFoundError(f"Keyword file not found at {keyword_path}")
    if not context_path.exists():
        raise FileNotFoundError(f"Context file not found at {context_path}")
    
    print(f"Using keyword file: {keyword_path}")
    print(f"Using context file: {context_path}")
    
    # Callback for wake word detection
    def wake_word_callback():
        print("\nWake word 'hexapod' detected!")
    
    # Callback for intent inference
    def inference_callback(inference):
        if inference.is_understood:
            print("\nIntent detected:")
            print(f"Intent: {inference.intent}")
            print("Slots:")
            for slot, value in inference.slots.items():
                print(f"  {slot}: {value}")
        else:
            print("\nCommand not understood")
    
    # Initialize Picovoice
    picovoice = Picovoice(
        access_key=access_key,
        keyword_path=str(keyword_path),
        wake_word_callback=wake_word_callback,
        context_path=str(context_path),
        inference_callback=inference_callback,
        porcupine_sensitivity=0.75,
        rhino_sensitivity=0.25
    )
    
    # Get the frame length that Picovoice expects
    frame_length = picovoice.frame_length
    
    # Read and process the audio in chunks
    print(f"Processing {input_file}...")
    
    while True:
        # Read a chunk of audio
        audio_data = wav_file.readframes(frame_length)
        if len(audio_data) == 0:
            break
        
        # Convert to 16-bit integers
        audio_frame = struct.unpack_from("h" * frame_length, audio_data)
        
        # Process the frame
        picovoice.process(audio_frame)
    
    # Clean up
    picovoice.delete()
    wav_file.close()
    
    print("\nProcessing complete")

def main():
    parser = argparse.ArgumentParser(description='Test complete Picovoice pipeline on a WAV file')
    parser.add_argument('input_file', type=str, help='Path to the input WAV file')
    parser.add_argument('--access-key', type=str, required=True, help='Picovoice access key')
    
    args = parser.parse_args()
    
    test_picovoice_on_file(
        Path(args.input_file),
        args.access_key
    )

if __name__ == '__main__':
    main() 