"""
Mock audio data for testing.
"""
import numpy as np
from typing import Dict, Any


def generate_sine_wave(frequency: float = 440.0, duration: float = 1.0, 
                      sample_rate: int = 16000) -> np.ndarray:
    """Generate a sine wave for testing."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    return np.sin(2 * np.pi * frequency * t).astype(np.float32)


def generate_white_noise(duration: float = 1.0, sample_rate: int = 16000) -> np.ndarray:
    """Generate white noise for testing."""
    return np.random.normal(0, 0.1, int(sample_rate * duration)).astype(np.float32)


def generate_multi_channel_audio(channels: int = 6, duration: float = 1.0, 
                                sample_rate: int = 16000) -> np.ndarray:
    """Generate multi-channel audio data for testing."""
    samples = int(sample_rate * duration)
    return np.random.normal(0, 0.1, (channels, samples)).astype(np.float32)


def get_sample_audio_config() -> Dict[str, Any]:
    """Get sample audio configuration for testing."""
    return {
        'sample_rate': 16000,
        'channels': 6,
        'format': 'float32',
        'chunk_size': 1024,
        'duration': 1.0
    }


def get_sample_odas_config() -> Dict[str, Any]:
    """Get sample ODAS configuration for testing."""
    return {
        'doa_enabled': True,
        'ssl_enabled': True,
        'beamforming_enabled': True,
        'noise_reduction_enabled': True,
        'confidence_threshold': 0.7
    }
