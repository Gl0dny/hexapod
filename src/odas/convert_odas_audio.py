#!/usr/bin/env python3

import argparse
import wave
import numpy as np
import time
from pathlib import Path
from odas_voice_input import ODASVoiceInput

def convert_odas_to_wav(input_file: Path, output_file: Path, sample_rate: int = 44100, channels: int = 4, selected_channel: int = 0):
    """
    Convert ODAS raw audio file to WAV format compatible with Picovoice.
    
    Args:
        input_file (Path): Path to the input ODAS raw file
        output_file (Path): Path to save the output WAV file
        sample_rate (int): Input sample rate (default: 44100)
        channels (int): Number of input channels (default: 4)
        selected_channel (int): Channel to extract (default: 0)
    """
    # Create a temporary directory for ODASVoiceInput
    temp_dir = input_file.parent
    odas_input = ODASVoiceInput(
        odas_dir=temp_dir,
        sample_rate=sample_rate,
        channels=channels,
        selected_channel=selected_channel
    )
    
    # Open output WAV file
    wav_file = wave.open(str(output_file), 'wb')
    wav_file.setnchannels(1)  # Mono
    wav_file.setsampwidth(2)  # 16-bit
    wav_file.setframerate(16000)  # Picovoice sample rate
    
    # Buffer to store converted audio
    converted_audio = []
    last_file_size = 0
    no_change_count = 0
    
    def audio_callback(audio_data):
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
    
    # Stop the ODASVoiceInput
    odas_input.stop()
    
    # Write all converted audio to the WAV file
    for audio_chunk in converted_audio:
        wav_file.writeframes(audio_chunk)
    
    # Close the WAV file
    wav_file.close()
    
    print(f"Successfully converted {input_file} to {output_file}")
    print(f"Output format: 16000 Hz, mono, 16-bit PCM")
    print(f"Converted {len(converted_audio)} chunks of audio")

def main():
    parser = argparse.ArgumentParser(description='Convert ODAS raw audio to WAV format compatible with Picovoice')
    parser.add_argument('input_file', type=str, help='Path to the input ODAS raw file')
    parser.add_argument('output_file', type=str, help='Path to save the output WAV file')
    parser.add_argument('--sample-rate', type=int, default=44100, help='Input sample rate (default: 44100)')
    parser.add_argument('--channels', type=int, default=4, help='Number of input channels (default: 4)')
    parser.add_argument('--channel', type=int, default=0, help='Channel to extract (default: 0)')
    
    args = parser.parse_args()
    
    convert_odas_to_wav(
        Path(args.input_file),
        Path(args.output_file),
        args.sample_rate,
        args.channels,
        args.channel
    )

if __name__ == '__main__':
    main() 