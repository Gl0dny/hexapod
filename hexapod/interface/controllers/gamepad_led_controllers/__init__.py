"""
Gamepad LED controllers package.

This package provides LED control functionality for various gamepad controllers
using inheritance to support different controller types.
"""

from hexapod.interface.controllers.gamepad_led_controllers.gamepad_led_controller import BaseGamepadLEDController, GamepadLEDColor
from hexapod.interface.controllers.gamepad_led_controllers.dual_sense_led_controller import DualSenseLEDController

__all__ = [
    'BaseGamepadLEDController',
    'DualSenseLEDController', 
    'GamepadLEDColor'
] 