"""
Data collection classes for gathering evaluation metrics.
"""

import psutil
import time
from datetime import datetime
from typing import Optional, List, Dict
import numpy as np
import sounddevice as sd
import threading
from pathlib import Path
import json
import logging

from .metrics import (
    DOAMetrics,
    KWSMetrics,
    SystemMetrics,
    EnvironmentalMetrics,
    MetricsAggregator
)

class DataCollector:
    """Base class for data collection."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_aggregator = MetricsAggregator()
        self.running = False
        self.logger = logging.getLogger(self.__class__.__name__)

class AudioDataCollector(DataCollector):
    """Collects audio-related metrics."""
    
    def __init__(self, output_dir: Path, sample_rate: int = 16000):
        super().__init__(output_dir)
        self.sample_rate = sample_rate
        self.audio_data: List[np.ndarray] = []
        self.recording_thread: Optional[threading.Thread] = None
    
    def start_recording(self, duration: float):
        """Start recording audio for the specified duration."""
        self.audio_data = []
        self.running = True
        
        def record():
            with sd.InputStream(samplerate=self.sample_rate, channels=1) as stream:
                while self.running:
                    data, _ = stream.read(1024)
                    self.audio_data.append(data)
        
        self.recording_thread = threading.Thread(target=record)
        self.recording_thread.start()
        
        # Stop after duration
        time.sleep(duration)
        self.stop_recording()
    
    def stop_recording(self):
        """Stop recording audio."""
        self.running = False
        if self.recording_thread:
            self.recording_thread.join()
    
    def calculate_snr(self) -> float:
        """Calculate Signal-to-Noise Ratio from recorded audio."""
        if not self.audio_data:
            return 0.0
        
        audio = np.concatenate(self.audio_data)
        signal_power = np.mean(audio ** 2)
        noise_power = np.var(audio)
        return 10 * np.log10(signal_power / noise_power) if noise_power > 0 else 0.0

class MotionDataCollector(DataCollector):
    """Collects motion-related metrics."""
    
    def __init__(self, output_dir: Path):
        super().__init__(output_dir)
        self.motion_data: List[Dict] = []
    
    def record_motion(self, gait_type: str, duration: float):
        """Record motion data for the specified gait type and duration."""
        start_time = time.time()
        while time.time() - start_time < duration:
            # Record motion data (implement based on your IMU/encoder setup)
            motion_data = {
                'timestamp': datetime.now(),
                'gait_type': gait_type,
                'position': (0, 0, 0),  # Replace with actual position data
                'orientation': (0, 0, 0),  # Replace with actual orientation data
                'velocity': (0, 0, 0)  # Replace with actual velocity data
            }
            self.motion_data.append(motion_data)
            time.sleep(0.01)  # 100Hz sampling rate

class SystemDataCollector(DataCollector):
    """Collects system performance metrics."""
    
    def __init__(self, output_dir: Path):
        super().__init__(output_dir)
        self.process = psutil.Process()
    
    def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_usage=self.process.cpu_percent(),
            memory_usage=self.process.memory_percent(),
            power_consumption=0.0,  # Implement based on your hardware
            processing_latency=0.0,  # Implement based on your timing measurements
            buffer_utilization=0.0,  # Implement based on your buffer monitoring
            frame_processing_time=0.0  # Implement based on your frame timing
        )
    
    def monitor_system(self, duration: float):
        """Monitor system metrics for the specified duration."""
        start_time = time.time()
        while time.time() - start_time < duration:
            metrics = self.collect_metrics()
            self.metrics_aggregator.add_system_metric(metrics)
            time.sleep(0.1)  # 10Hz sampling rate

class EnvironmentalDataCollector(DataCollector):
    """Collects environmental condition metrics."""
    
    def __init__(self, output_dir: Path):
        super().__init__(output_dir)
        self.audio_collector = AudioDataCollector(output_dir / "audio")
    
    def measure_environment(self, room_size: str, surface_type: str) -> EnvironmentalMetrics:
        """Measure current environmental conditions."""
        # Record audio for noise level measurement
        self.audio_collector.start_recording(1.0)  # Record for 1 second
        snr = self.audio_collector.calculate_snr()
        
        return EnvironmentalMetrics(
            timestamp=datetime.now(),
            noise_level=snr,  # Convert SNR to dB
            reverberation_time=0.0,  # Implement RT60 measurement
            room_size=room_size,
            surface_type=surface_type,
            temperature=0.0,  # Implement temperature measurement
            humidity=0.0  # Implement humidity measurement
        )
    
    def collect_environmental_data(self, room_size: str, surface_type: str, duration: float):
        """Collect environmental data for the specified duration."""
        start_time = time.time()
        while time.time() - start_time < duration:
            metrics = self.measure_environment(room_size, surface_type)
            self.metrics_aggregator.add_environmental_metric(metrics)
            time.sleep(1.0)  # 1Hz sampling rate 