"""
Evaluation classes for running and analyzing tests.
"""

import time
from datetime import datetime
from pathlib import Path
import json
import logging
from typing import List, Dict, Optional
import numpy as np
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor

from .metrics import (
    DOAMetrics,
    KWSMetrics,
    SystemMetrics,
    EnvironmentalMetrics,
    MetricsAggregator
)
from .data_collector import (
    AudioDataCollector,
    MotionDataCollector,
    SystemDataCollector,
    EnvironmentalDataCollector
)

class Evaluator:
    """Base class for evaluation."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_aggregator = MetricsAggregator()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def save_results(self, filename: str):
        """Save evaluation results to a JSON file."""
        results = {
            'doa_statistics': self.metrics_aggregator.get_doa_statistics(),
            'kws_statistics': self.metrics_aggregator.get_kws_statistics(),
            'system_statistics': self.metrics_aggregator.get_system_statistics(),
            'environmental_statistics': self.metrics_aggregator.get_environmental_statistics()
        }
        
        with open(self.output_dir / filename, 'w') as f:
            json.dump(results, f, indent=2)
    
    def plot_results(self, filename: str):
        """Plot evaluation results."""
        # Implement plotting based on your needs
        pass

class StaticEvaluator(Evaluator):
    """Evaluates system performance in static conditions."""
    
    def __init__(self, output_dir: Path):
        super().__init__(output_dir)
        self.audio_collector = AudioDataCollector(output_dir / "audio")
        self.system_collector = SystemDataCollector(output_dir / "system")
    
    def evaluate_doa(self, true_angles: List[float], distances: List[float], duration: float = 5.0):
        """Evaluate DOA estimation accuracy for different angles and distances."""
        for angle, distance in zip(true_angles, distances):
            # Start system monitoring
            self.system_collector.monitor_system(duration)
            
            # Record audio and estimate DOA
            self.audio_collector.start_recording(duration)
            
            # Create DOA metrics (replace with actual DOA estimation)
            metrics = DOAMetrics(
                timestamp=datetime.now(),
                true_angle=angle,
                estimated_angle=angle + np.random.normal(0, 5),  # Simulated error
                confidence=0.9,
                distance=distance,
                snr=self.audio_collector.calculate_snr(),
                motion_state='static'
            )
            self.metrics_aggregator.add_doa_metric(metrics)
    
    def evaluate_kws(self, commands: List[str], duration: float = 5.0):
        """Evaluate keyword spotting accuracy for different commands."""
        for command in commands:
            # Start system monitoring
            self.system_collector.monitor_system(duration)
            
            # Record audio and perform KWS
            self.audio_collector.start_recording(duration)
            
            # Create KWS metrics (replace with actual KWS results)
            metrics = KWSMetrics(
                timestamp=datetime.now(),
                wake_word_detected=True,
                command_recognized=True,
                command_text=command,
                confidence=0.9,
                processing_time=0.1
            )
            self.metrics_aggregator.add_kws_metric(metrics)

class DynamicEvaluator(Evaluator):
    """Evaluates system performance during motion."""
    
    def __init__(self, output_dir: Path):
        super().__init__(output_dir)
        self.audio_collector = AudioDataCollector(output_dir / "audio")
        self.motion_collector = MotionDataCollector(output_dir / "motion")
        self.system_collector = SystemDataCollector(output_dir / "system")
    
    def evaluate_motion_compensation(self, gait_types: List[str], duration: float = 10.0):
        """Evaluate motion compensation effectiveness for different gaits."""
        for gait in gait_types:
            # Start motion recording
            self.motion_collector.record_motion(gait, duration)
            
            # Start system monitoring
            self.system_collector.monitor_system(duration)
            
            # Record audio and estimate DOA
            self.audio_collector.start_recording(duration)
            
            # Create DOA metrics with motion compensation
            metrics = DOAMetrics(
                timestamp=datetime.now(),
                true_angle=0.0,  # Replace with actual angle
                estimated_angle=0.0,  # Replace with actual estimation
                confidence=0.9,
                distance=1.0,
                snr=self.audio_collector.calculate_snr(),
                motion_state='dynamic',
                gait_type=gait
            )
            self.metrics_aggregator.add_doa_metric(metrics)

class EnvironmentalEvaluator(Evaluator):
    """Evaluates system performance under different environmental conditions."""
    
    def __init__(self, output_dir: Path):
        super().__init__(output_dir)
        self.audio_collector = AudioDataCollector(output_dir / "audio")
        self.environmental_collector = EnvironmentalDataCollector(output_dir / "environmental")
        self.system_collector = SystemDataCollector(output_dir / "system")
    
    def evaluate_environmental_robustness(self, room_sizes: List[str], surface_types: List[str], duration: float = 30.0):
        """Evaluate system performance in different environments."""
        for room_size in room_sizes:
            for surface_type in surface_types:
                # Collect environmental data
                self.environmental_collector.collect_environmental_data(room_size, surface_type, duration)
                
                # Start system monitoring
                self.system_collector.monitor_system(duration)
                
                # Record audio and perform evaluation
                self.audio_collector.start_recording(duration)
                
                # Create metrics for this environment
                metrics = EnvironmentalMetrics(
                    timestamp=datetime.now(),
                    noise_level=self.audio_collector.calculate_snr(),
                    reverberation_time=0.0,  # Implement RT60 measurement
                    room_size=room_size,
                    surface_type=surface_type,
                    temperature=0.0,  # Implement temperature measurement
                    humidity=0.0  # Implement humidity measurement
                )
                self.metrics_aggregator.add_environmental_metric(metrics) 