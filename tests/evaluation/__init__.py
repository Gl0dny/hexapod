"""
Evaluation module for the hexapod auditory perception system.
This module contains tools and scripts for evaluating the system's performance.
"""

from .metrics import (
    DOAMetrics,
    KWSMetrics,
    SystemMetrics,
    EnvironmentalMetrics
)

from .data_collector import (
    DataCollector,
    AudioDataCollector,
    MotionDataCollector,
    SystemDataCollector
)

from .evaluator import (
    Evaluator,
    StaticEvaluator,
    DynamicEvaluator,
    EnvironmentalEvaluator
)

__all__ = [
    'DOAMetrics',
    'KWSMetrics',
    'SystemMetrics',
    'EnvironmentalMetrics',
    'DataCollector',
    'AudioDataCollector',
    'MotionDataCollector',
    'SystemDataCollector',
    'Evaluator',
    'StaticEvaluator',
    'DynamicEvaluator',
    'EnvironmentalEvaluator'
] 