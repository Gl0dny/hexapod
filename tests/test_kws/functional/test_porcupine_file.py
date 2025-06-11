#!/usr/bin/env python3

import argparse
import wave
import numpy as np
import pvporcupine
import struct
from pathlib import Path

def test_picovoice_on_file(input_file: Path, access_key: str):
    """
    Test Picovoice keyword spotting on a WAV file using the hexapod keyword model.
    
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
    keyword_path = Path(__file__).parent.parent.parent.parent / "src" / "kws" / "porcupine" / "hexapod_en_raspberry-pi_v3_0_0.ppn"
    if not keyword_path.exists():
        raise FileNotFoundError(f"Keyword model file not found at {keyword_path}")
    
    print(f"Using keyword model: {keyword_path}")
    
    # Initialize Porcupine with the hexapod keyword model
    porcupine = pvporcupine.create(
        access_key=access_key,
        keyword_paths=[str(keyword_path)]
    )
    
    # Get the frame length that Porcupine expects
    frame_length = porcupine.frame_length
    
    # Read and process the audio in chunks
    print(f"Processing {input_file}...")
    keyword_detected = False
    
    while True:
        # Read a chunk of audio
        audio_data = wav_file.readframes(frame_length)
        if len(audio_data) == 0:
            break
        
        # Convert to 16-bit integers
        audio_frame = struct.unpack_from("h" * frame_length, audio_data)
        
        # Process the frame
        keyword_index = porcupine.process(audio_frame)
        
        if keyword_index >= 0:
            keyword_detected = True
            print(f"Keyword 'hexapod' detected at frame {wav_file.tell() // (frame_length * 2)}")
    
    # Clean up
    porcupine.delete()
    wav_file.close()
    
    if not keyword_detected:
        print("No keywords detected in the file")

def main():
    parser = argparse.ArgumentParser(description='Test Picovoice keyword spotting on a WAV file using the hexapod keyword model')
    parser.add_argument('input_file', type=str, help='Path to the input WAV file')
    parser.add_argument('--access-key', type=str, required=True, help='Picovoice access key')
    
    args = parser.parse_args()
    
    test_picovoice_on_file(
        Path(args.input_file),
        args.access_key
    )

if __name__ == '__main__':
    main() 