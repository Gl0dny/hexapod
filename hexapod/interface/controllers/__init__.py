"""
Hexapod controller package.

This package provides various controller implementations for manual hexapod control.
"""

from .controllers.base_manual_controller import ManualHexapodController
from .controllers.gamepad_hexapod_controller import GamepadHexapodController
from .controllers.gamepad_led_controllers import BaseGamepadLEDController, DualSenseLEDController, GamepadLEDColor

__all__ = [
    'ManualHexapodController',
    'GamepadHexapodController',
    'BaseGamepadLEDController',
    'DualSenseLEDController',
    'GamepadLEDColor'
]