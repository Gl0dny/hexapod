"""
Metrics classes for evaluating different aspects of the system.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np
from datetime import datetime

@dataclass
class DOAMetrics:
    """Metrics for Sound Source Localization (SSL) evaluation."""
    timestamp: datetime
    true_angle: float
    estimated_angle: float
    confidence: float
    distance: float
    snr: float
    motion_state: str  # 'static' or 'dynamic'
    gait_type: Optional[str] = None
    
    @property
    def angular_error(self) -> float:
        """Calculate the absolute angular error in degrees."""
        error = abs(self.estimated_angle - self.true_angle)
        return min(error, 360 - error)  # Handle circular nature of angles

@dataclass
class KWSMetrics:
    """Metrics for Keyword Spotting (KWS) evaluation."""
    timestamp: datetime
    wake_word_detected: bool
    command_recognized: bool
    command_text: Optional[str]
    confidence: float
    processing_time: float
    false_positive: bool = False
    false_negative: bool = False

@dataclass
class SystemMetrics:
    """Metrics for system performance evaluation."""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    power_consumption: float
    processing_latency: float
    buffer_utilization: float
    frame_processing_time: float

@dataclass
class EnvironmentalMetrics:
    """Metrics for environmental conditions evaluation."""
    timestamp: datetime
    noise_level: float  # dB
    reverberation_time: float  # RT60
    room_size: str  # 'small', 'medium', 'large'
    surface_type: str  # 'hard', 'soft', 'mixed'
    temperature: float
    humidity: float

class MetricsAggregator:
    """Class for aggregating and analyzing metrics."""
    
    def __init__(self):
        self.doa_metrics: List[DOAMetrics] = []
        self.kws_metrics: List[KWSMetrics] = []
        self.system_metrics: List[SystemMetrics] = []
        self.environmental_metrics: List[EnvironmentalMetrics] = []
    
    def add_doa_metric(self, metric: DOAMetrics) -> None:
        self.doa_metrics.append(metric)
    
    def add_kws_metric(self, metric: KWSMetrics) -> None:
        self.kws_metrics.append(metric)
    
    def add_system_metric(self, metric: SystemMetrics) -> None:
        self.system_metrics.append(metric)
    
    def add_environmental_metric(self, metric: EnvironmentalMetrics) -> None:
        self.environmental_metrics.append(metric)
    
    def get_doa_statistics(self) -> Dict:
        """Calculate statistics for DOA metrics."""
        if not self.doa_metrics:
            return {}
        
        errors = [m.angular_error for m in self.doa_metrics]
        return {
            'mean_absolute_error': np.mean(errors),
            'root_mean_square_error': np.sqrt(np.mean(np.square(errors))),
            'max_error': np.max(errors),
            'min_error': np.min(errors),
            'std_error': np.std(errors)
        }
    
    def get_kws_statistics(self) -> Dict:
        """Calculate statistics for KWS metrics."""
        if not self.kws_metrics:
            return {}
        
        return {
            'false_acceptance_rate': sum(1 for m in self.kws_metrics if m.false_positive) / len(self.kws_metrics),
            'false_rejection_rate': sum(1 for m in self.kws_metrics if m.false_negative) / len(self.kws_metrics),
            'average_processing_time': np.mean([m.processing_time for m in self.kws_metrics]),
            'recognition_rate': sum(1 for m in self.kws_metrics if m.command_recognized) / len(self.kws_metrics)
        }
    
    def get_system_statistics(self) -> Dict:
        """Calculate statistics for system metrics."""
        if not self.system_metrics:
            return {}
        
        return {
            'average_cpu_usage': np.mean([m.cpu_usage for m in self.system_metrics]),
            'average_memory_usage': np.mean([m.memory_usage for m in self.system_metrics]),
            'average_power_consumption': np.mean([m.power_consumption for m in self.system_metrics]),
            'average_processing_latency': np.mean([m.processing_latency for m in self.system_metrics]),
            'average_buffer_utilization': np.mean([m.buffer_utilization for m in self.system_metrics])
        }
    
    def get_environmental_statistics(self) -> Dict:
        """Calculate statistics for environmental metrics."""
        if not self.environmental_metrics:
            return {}
        
        return {
            'average_noise_level': np.mean([m.noise_level for m in self.environmental_metrics]),
            'average_reverberation_time': np.mean([m.reverberation_time for m in self.environmental_metrics]),
            'average_temperature': np.mean([m.temperature for m in self.environmental_metrics]),
            'average_humidity': np.mean([m.humidity for m in self.environmental_metrics])
        } 