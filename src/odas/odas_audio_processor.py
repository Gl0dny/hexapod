#!/usr/bin/env python3

"""
ODAS Voice Input

This module provides an interface between ODAS audio streams and the voice control pipeline.
It reads audio from local ODAS output files and feeds it into the voice control system for wake word detection
and intent recognition.
"""

import logging
import threading
from pathlib import Path
import numpy as np
from typing import Optional, Callable
import resampy
import time

# Configure logger
logger = logging.getLogger("odas_voice")
logger.setLevel(logging.DEBUG)  # Set to DEBUG level

class ODASAudioProcessor:
    """
    Class to read audio from ODAS raw output files and convert it to a format
    suitable for voice control systems.
    """
    
    def __init__(
        self,
        odas_dir: Path,
        sample_rate: int = 44100,
        channels: int = 4,
        buffer_size: int = 1024,
        check_interval: float = 0.5,
        target_sample_rate: int = 16000,  # Picovoice's required sample rate
        target_channels: int = 1,  # Picovoice's required channel count
        selected_channel: int = 0,  # Which channel to use from the array
        frame_length: int = 512  # Picovoice's frame length
    ):
        """
        Initialize the ODAS audio processor.

        Args:
            odas_dir (Path): Directory where ODAS creates raw files
            sample_rate (int): Sample rate of the audio files
            channels (int): Number of channels in the audio files
            buffer_size (int): Size of audio buffer in bytes
            check_interval (float): Interval in seconds to check for new audio data
            target_sample_rate (int): Target sample rate for Picovoice (default: 16000)
            target_channels (int): Target number of channels for Picovoice (default: 1)
            selected_channel (int): Which channel to use from the array (default: 0)
            frame_length (int): Number of samples per frame (default: 512)
        """
        print(f"Initializing ODASAudioProcessor with directory: {odas_dir}")
        self.odas_dir = odas_dir
        self.audio_file = self.odas_dir / "postfiltered.raw"
        print(f"Audio file path: {self.audio_file}")
        
        self.audio_callback: Optional[Callable[[np.ndarray], None]] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Audio conversion parameters
        self.source_sample_rate = sample_rate
        self.target_sample_rate = target_sample_rate
        self.source_channels = channels
        self.target_channels = target_channels
        self.selected_channel = selected_channel
        self.buffer_size = buffer_size
        self.check_interval = check_interval
        self.frame_length = frame_length
        
        # Calculate resampling ratio
        self.resample_ratio = target_sample_rate / sample_rate
        
        # Track last file size for reading new data
        self._last_file_size = 0
        self._buffer = bytearray()
        
        print(f"Initialized with sample_rate={sample_rate}, channels={channels}, "
              f"frame_length={frame_length}, target_sample_rate={target_sample_rate}")
        
    def set_audio_callback(self, callback: Callable[[np.ndarray], None]) -> None:
        """
        Set the callback function to receive audio data.

        Args:
            callback (Callable[[np.ndarray], None]): Function to call with audio data
        """
        self.audio_callback = callback
        
    def start(self) -> None:
        """
        Start reading audio from ODAS and feeding it to the callback.
        """
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._read_audio, daemon=True)
        self.thread.start()
        logger.info("Started ODAS voice input reading")
        
    def stop(self) -> None:
        """
        Stop reading audio from ODAS.
        """
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Stopped ODAS voice input reading")
        
    def _convert_audio(self, audio_data: bytes) -> np.ndarray:
        """
        Convert audio data from ODAS format to Picovoice format.

        Args:
            audio_data (bytes): Raw audio data from ODAS

        Returns:
            np.ndarray: Converted audio data in Picovoice format
        """
        # Convert bytes to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        # Reshape to separate channels
        audio_array = audio_array.reshape(-1, self.source_channels)
        
        # Select the desired channel
        mono_audio = audio_array[:, self.selected_channel]
        
        # Calculate the target number of samples after resampling
        # We need to maintain the frame length of 512 samples at 16000Hz
        # So we need to resample to get exactly 512 samples
        target_samples = self.frame_length
        source_samples = int(target_samples * (self.source_sample_rate / self.target_sample_rate))
        
        # Ensure we have enough samples
        if len(mono_audio) < source_samples:
            # Instead of returning zeros, accumulate samples until we have enough
            if not hasattr(self, '_sample_buffer'):
                self._sample_buffer = np.array([], dtype=np.int16)
            
            self._sample_buffer = np.concatenate([self._sample_buffer, mono_audio])
            
            if len(self._sample_buffer) < source_samples:
                return None
            
            # Take exactly the number of samples we need
            mono_audio = self._sample_buffer[:source_samples]
            self._sample_buffer = self._sample_buffer[source_samples:]
            
        # Take exactly the number of samples we need
        mono_audio = mono_audio[:source_samples]
        
        # Resample to target sample rate
        resampled_audio = resampy.resample(
            mono_audio,
            self.source_sample_rate,
            self.target_sample_rate
        )
        
        # Ensure we have exactly the target number of samples
        if len(resampled_audio) > target_samples:
            resampled_audio = resampled_audio[:target_samples]
        elif len(resampled_audio) < target_samples:
            resampled_audio = np.pad(resampled_audio, (0, target_samples - len(resampled_audio)))
        
        # Convert to 16-bit PCM
        resampled_audio = np.clip(resampled_audio, -32768, 32767).astype(np.int16)
        
        return resampled_audio
        
    def _read_audio(self) -> None:
        """
        Internal method to read audio from ODAS and feed it to the callback.
        """
        try:
            print(f"Starting to read audio from {self.audio_file}")
            print(f"Initial file size: {self.audio_file.stat().st_size if self.audio_file.exists() else 'File does not exist'}")
            
            while self.running:
                try:
                    if not self.audio_file.exists():
                        logger.warning(f"ODAS audio file not found: {self.audio_file}")
                        time.sleep(self.check_interval)
                        continue
                        
                    current_size = self.audio_file.stat().st_size
                    
                    if current_size > self._last_file_size:
                        # Read new audio data
                        with open(self.audio_file, 'rb') as f:
                            f.seek(self._last_file_size)
                            new_data = f.read(current_size - self._last_file_size)
                            
                            if new_data:
                                # Add new data to buffer
                                self._buffer.extend(new_data)
                                
                                # Calculate bytes per frame (2 bytes per sample * number of channels)
                                bytes_per_frame = 2 * self.source_channels * self.frame_length
                                
                                # Process complete frames
                                while len(self._buffer) >= bytes_per_frame:
                                    # Extract one frame
                                    frame_data = bytes(self._buffer[:bytes_per_frame])
                                    self._buffer = self._buffer[bytes_per_frame:]
                                    
                                    if self.audio_callback is not None:
                                        # Convert audio format and feed to callback
                                        converted_audio = self._convert_audio(frame_data)
                                        if converted_audio is not None:
                                            self.audio_callback(converted_audio)
                                
                        self._last_file_size = current_size
                        
                    time.sleep(self.check_interval)
                    
                except Exception as e:
                    logger.error(f"Error reading audio: {e}")
                    time.sleep(self.check_interval)
                    continue
                    
        except Exception as e:
            logger.error(f"Fatal error in ODAS audio reading: {e}") 