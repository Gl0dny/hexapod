#!/usr/bin/env python3
"""
Base input mapping implementation.

This module provides the abstract base class for input interface mappings.
"""

from abc import ABC, abstractmethod

class InputMapping(ABC):
    """Abstract base class for input interface mappings."""
    
    @abstractmethod
    def get_axis_mappings(self):
        """Return a dictionary of axis/input mappings."""
        pass
    
    @abstractmethod
    def get_button_mappings(self):
        """Return a dictionary of button/control mappings."""
        pass
    
    @abstractmethod
    def get_interface_names(self):
        """Return a list of interface names this mapping supports."""
        pass
    
    @abstractmethod
    def get_axis_name(self, axis_index):
        """Get the name of an axis/input by its index."""
        pass
    
    @abstractmethod
    def get_button_name(self, button_index):
        """Get the name of a button/control by its index."""
        pass
    
    @abstractmethod
    def print_mappings_info(self):
        """Print information about the interface mappings."""
        pass 