"""
Base input mapping implementation.

This module provides the abstract base class for gamepad input interface mappings.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, List, Any


class InputMapping(ABC):
    """Abstract base class for input interface mappings."""

    @abstractmethod
    def get_axis_mappings(self) -> Dict[str, Any]:
        """Return a dictionary of axis/input mappings."""
        pass

    @abstractmethod
    def get_button_mappings(self) -> Dict[str, Any]:
        """Return a dictionary of button/control mappings."""
        pass

    @abstractmethod
    def get_hat_mappings(self) -> Dict[str, Any]:
        """Return a dictionary of hat mappings."""
        pass

    @abstractmethod
    def get_interface_names(self) -> List[str]:
        """Return a list of interface names this mapping supports."""
        pass

    @abstractmethod
    def get_axis_name(self, axis_index: int) -> str:
        """Get the name of an axis/input by its index."""
        pass

    @abstractmethod
    def get_button_name(self, button_index: int) -> str:
        """Get the name of a button/control by its index."""
        pass

    @abstractmethod
    def print_mappings_info(self) -> None:
        """Print information about the interface mappings."""
        pass
