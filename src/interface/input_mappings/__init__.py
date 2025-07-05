#!/usr/bin/env python3
"""
Input mappings package for hexapod controllers.

This package provides input mapping implementations for different input devices
and interfaces used with hexapod controllers.
"""

from .base_input_mapping import InputMapping
from .dual_sense_mapping import DualSenseMapping

__all__ = [
    'InputMapping',
    'DualSenseMapping'
]