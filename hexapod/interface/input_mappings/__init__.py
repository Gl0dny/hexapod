"""
Input mappings package for hexapod controllers.

This package provides input mapping implementations for different input devices
and interfaces used with hexapod controllers.
"""

from .input_mappings.base_input_mapping import InputMapping
from .input_mappings.dual_sense_usb_mapping import DualSenseUSBMapping
from .input_mappings.dual_sense_bluetooth_mapping import DualSenseBluetoothMapping

__all__ = [
    'InputMapping',
    'DualSenseUSBMapping',
    'DualSenseBluetoothMapping'
]