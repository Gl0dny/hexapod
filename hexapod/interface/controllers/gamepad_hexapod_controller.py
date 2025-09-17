"""
Gamepad-based hexapod controller implementation.

This script provides a gamepad-based interface to test the hexapod's movement
capabilities using various game controllers.

Usage:
    python gamepad_hexapod_controller.py
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import sys
import os
import warnings
from pathlib import Path
import time
from enum import Enum

# Silence pygame warnings and welcome message BEFORE importing pygame
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

warnings.filterwarnings("ignore", category=RuntimeWarning, module="pygame")
warnings.filterwarnings("ignore", category=UserWarning, module="pygame")
warnings.filterwarnings("ignore", message=".*pkg_resources.*")
warnings.filterwarnings("ignore", message=".*neon capable.*")
warnings.filterwarnings("ignore", message=".*pygame.*")

from hexapod.interface.controllers import ManualHexapodController
from hexapod.interface.input_mappings import InputMapping, DualSenseUSBMapping
from hexapod.interface.controllers.gamepad_led_controllers import (
    BaseGamepadLEDController,
    GamepadLEDColor,
    DualSenseLEDController,
)
from hexapod.utils import rename_thread
from hexapod.interface import get_custom_logger

logger = get_custom_logger("interface_logger")

try:
    import pygame

    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    logger.exception("pygame not available. Install with: pip install pygame")

if TYPE_CHECKING:
    from typing import Optional, Callable, Dict, Any
    import pygame.joystick
    from hexapod.kws import VoiceControl
    from hexapod.task_interface import TaskInterface


class GamepadHexapodController(ManualHexapodController):
    """Gamepad-based hexapod controller implementation."""

    class LEDControllerType(Enum):
        NONE = 0
        DUALSENSE = 1

    class InputMappingType(Enum):
        DUALSENSE_USB = 1
        DUALSENSE_BLUETOOTH = 2

    BUTTON_DEBOUNCE_INTERVAL = 0.3  # seconds

    @staticmethod
    def find_gamepad(input_mapping: InputMapping, check_only: bool = False) -> Optional[pygame.joystick.Joystick]:
        """
        Find and initialize a gamepad that matches the mapping, or just check for availability.
        Args:
            input_mapping: The input mapping for the gamepad
            check_only (bool): If True, only check availability (returns True/False), else returns joystick or None
        Returns:
            Joystick object if found (and not check_only), True if available (check_only), else None/False
        """
        if not "PYGAME_AVAILABLE" in globals() or not PYGAME_AVAILABLE:
            return False if check_only else None
        try:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            os.environ["SDL_AUDIODRIVER"] = "dummy"
            pygame.init()
            pygame.joystick.init()
            joystick_count = pygame.joystick.get_count()
            for i in range(joystick_count):
                joystick = pygame.joystick.Joystick(i)
                name = joystick.get_name().lower()
                if any(
                    keyword in name for keyword in input_mapping.get_interface_names()
                ):
                    if check_only:
                        pygame.quit()
                        return True
                    joystick.init()
                    return joystick
            if check_only:
                pygame.quit()
                return False
        except Exception as e:
            logger.exception(f"Error checking/finding gamepad: {e}")
            return False if check_only else None
        return None

    @staticmethod
    def get_gamepad_connection_type(gamepad: pygame.joystick.Joystick) -> Optional[str]:
        """Return 'bluetooth' if the gamepad name contains 'wireless' or 'bluetooth', else 'usb'. Accepts a gamepad object."""
        if not gamepad:
            return None
        name_lower = gamepad.get_name().lower()
        if "wireless" in name_lower or "bluetooth" in name_lower:
            return "bluetooth"
        return "usb"

    def __init__(
        self,
        task_interface: TaskInterface,
        voice_control: Optional[VoiceControl] = None,
        input_mapping_type: Optional[InputMappingType] = None,
        led_controller_type: Optional[LEDControllerType] = None,
        shutdown_callback: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize the gamepad hexapod controller.

        Args:
            input_mapping_type: Enum specifying which input mapping to use
            task_interface: Task interface for hexapod operations
            voice_control: Optional voice control mode
            led_controller_type: Enum specifying which LED controller to use
            shutdown_callback: Optional callback function to call when PS5 button is pressed
        """
        super().__init__(
            task_interface=task_interface,
            voice_control=voice_control,
            shutdown_callback=shutdown_callback,
        )
        rename_thread(self, "GamepadHexapodController")

        if not PYGAME_AVAILABLE:
            raise ImportError("pygame is required for gamepad support")

        # Set defaults to DUALSENSE if not provided
        if input_mapping_type is None:
            input_mapping_type = self.InputMappingType.DUALSENSE_BLUETOOTH
        if led_controller_type is None:
            led_controller_type = self.LEDControllerType.DUALSENSE

        # Try Bluetooth mapping first (default), fallback to USB if needed
        self.input_mapping: Optional[InputMapping] = None
        if input_mapping_type == self.InputMappingType.DUALSENSE_BLUETOOTH:
            from hexapod.interface import DualSenseBluetoothMapping

            self.input_mapping = DualSenseBluetoothMapping()
        elif input_mapping_type == self.InputMappingType.DUALSENSE_USB:
            from hexapod.interface import DualSenseUSBMapping

            self.input_mapping = DualSenseUSBMapping()

        if self.input_mapping is None:
            raise ValueError(
                "No valid input mapping type provided or mapping instantiation failed."
            )

        # Initialize gamepad state
        self.gamepad: Optional[pygame.joystick.Joystick] = None
        self.analog_inputs: Dict[str, float] = {}
        self.button_states: Dict[str, bool] = {}
        self.last_button_states: Dict[str, bool] = {}
        self._button_last_press_time: Dict[str, float] = {}
        self.current_led_state: Optional[str] = None
        self.marching_enabled = False  # Marching (neutral gait) is off by default

        # Set display environment for headless systems
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"

        # Initialize pygame for gamepad support
        pygame.init()
        pygame.joystick.init()

        # Find and initialize gamepad
        self.gamepad = self.find_gamepad(self.input_mapping, check_only=False)
        if not self.gamepad:
            # If Bluetooth mapping failed, try USB mapping as fallback
            if input_mapping_type == self.InputMappingType.DUALSENSE_BLUETOOTH:
                logger.user_info(
                    "Bluetooth mapping failed, trying USB mapping as fallback..."
                )
                from hexapod.interface import DualSenseUSBMapping

                self.input_mapping = DualSenseUSBMapping()
                self.gamepad = self.find_gamepad(self.input_mapping, check_only=False)

            if not self.gamepad:
                logger.user_info(
                    "No compatible gamepad found - falling back to voice control mode"
                )
                raise RuntimeError(
                    f"Gamepad not found. This script only supports: {', '.join(self.input_mapping.get_interface_names())}"
                )
            else:
                logger.user_info(
                    "Compatible gamepad found (USB mode) - starting manual control mode"
                )
        else:
            logger.user_info(
                "Compatible gamepad found (Bluetooth mode) - starting manual control mode"
            )

        # Now it's safe to get connection_type
        connection_type = self.get_gamepad_connection_type(self.gamepad)

        self.led_controller: Optional[BaseGamepadLEDController] = None
        if connection_type != "bluetooth" and led_controller_type is not None:
            if led_controller_type == self.LEDControllerType.DUALSENSE:
                try:
                    from hexapod.interface.controllers.gamepad_led_controllers import (
                        DualSenseLEDController,
                    )

                    self.led_controller = DualSenseLEDController()
                except Exception as e:
                    logger.warning(
                        f"Failed to initialize DualSense LED controller: {e}"
                    )
        elif (
            connection_type == "bluetooth"
            and led_controller_type is not None
            and led_controller_type != self.LEDControllerType.NONE
        ):
            logger.warning(
                "Gamepad is in Bluetooth mode: Gamepad LED controller is not supported and will not be initialized."
            )

        logger.gamepad_mode_info(
            f"Gamepad '{self.gamepad.get_name()}' initialized successfully"
        )
        logger.gamepad_mode_info(f"Current mode: {self.current_mode}")

        # Deadzone for analog sticks (specific to gamepad hardware)
        self.deadzone = 0.1

        # Initialize LED controller if provided
        if self.led_controller is not None:
            if self.led_controller.is_available():
                # Set initial LED animation based on controller type
                if "dualsense" or "ps5" in self.gamepad.get_name().lower():
                    self.led_controller.pulse(
                        GamepadLEDColor.BLUE, duration=2.0, cycles=0
                    )  # Infinite blue pulse
                else:
                    self.led_controller.pulse(
                        GamepadLEDColor.GREEN, duration=2.0, cycles=0
                    )  # Infinite green pulse
            else:
                logger.warning("Gamepad LED control not available")
                logger.warning("Make sure:")
                logger.warning("1. PS5 DualSense controller is connected")
                logger.warning("2. dualsense-controller library is installed")
        else:
            logger.warning("Gamepad LED control disabled")

        # For buffered stance height adjustment
        self._stance_height_buffer: float = 0.0
        self._stance_height_hold_start: Dict[str, Optional[float]] = {"l2": None, "r2": None}
        self._stance_height_last_increment: Dict[str, Optional[float]] = {"l2": None, "r2": None}

    def _start_initial_animation(self) -> None:
        """
        Start the initial light animation based on the current mode.
        """
        # Call parent method to start hexapod light animations
        super()._start_initial_animation()

        # Handle gamepad LED feedback - synchronized with hexapod LEDs (2.0s cycle)
        if not (self.led_controller and self.led_controller.is_available()):
            return

        if self.current_mode == self.GAIT_CONTROL_MODE:
            self.led_controller.pulse(GamepadLEDColor.INDIGO, duration=2.0, cycles=0)
            self.current_led_state = "gait_mode"
        elif self.current_mode == self.BODY_CONTROL_MODE:
            self.led_controller.pulse(GamepadLEDColor.BLUE, duration=2.0, cycles=0)
            self.current_led_state = "body_mode"
        elif self.current_mode == self.VOICE_CONTROL_MODE:
            self.led_controller.pulse_two_colors(
                GamepadLEDColor.BLUE, GamepadLEDColor.GREEN, duration=2.0, cycles=0
            )
            self.current_led_state = "voice_mode"

    def _apply_deadzone(self, value: float) -> float:
        """Apply deadzone to analog stick values."""
        if abs(value) < self.deadzone:
            return 0.0
        # Normalize the value after deadzone
        sign = 1 if value > 0 else -1
        normalized = (abs(value) - self.deadzone) / (1.0 - self.deadzone)
        return sign * normalized

    def _get_analog_inputs(self) -> Dict[str, float]:
        """Get analog stick inputs with deadzone applied."""
        if not self.gamepad or not self.input_mapping:
            return {}
            
        # Process events to update gamepad state
        for event in pygame.event.get():
            pass

        # Get axes using input mapping
        axis_mappings = self.input_mapping.get_axis_mappings()
        left_x = self._apply_deadzone(self.gamepad.get_axis(axis_mappings["left_x"]))
        left_y = self._apply_deadzone(self.gamepad.get_axis(axis_mappings["left_y"]))
        right_x = self._apply_deadzone(self.gamepad.get_axis(axis_mappings["right_x"]))
        l2 = self._apply_deadzone(self.gamepad.get_axis(axis_mappings["l2"]))
        r2 = self._apply_deadzone(self.gamepad.get_axis(axis_mappings["r2"]))
        right_y = self._apply_deadzone(self.gamepad.get_axis(axis_mappings["right_y"]))

        return {
            "left_x": left_x,
            "left_y": left_y,
            "right_x": right_x,
            "right_y": right_y,
            "l2": l2,
            "r2": r2,
        }

    def _get_button_states(self) -> Dict[str, bool]:
        """Get current button states."""
        if not self.gamepad or not self.input_mapping:
            return {}
            
        # Process events to clear pygame event queue, update gamepad state - prevents button stuck issue
        for event in pygame.event.get():
            pass

        # Get buttons using input mapping
        button_mappings = self.input_mapping.get_button_mappings()
        axis_mappings = self.input_mapping.get_axis_mappings()
        buttons = {
            "square": self.gamepad.get_button(button_mappings["square"]),
            "x": self.gamepad.get_button(button_mappings["x"]),
            "circle": self.gamepad.get_button(button_mappings["circle"]),
            "triangle": self.gamepad.get_button(button_mappings["triangle"]),
            "l1": self.gamepad.get_button(button_mappings["l1"]),
            "r1": self.gamepad.get_button(button_mappings["r1"]),
            "create": self.gamepad.get_button(button_mappings["create"]),
            "options": self.gamepad.get_button(button_mappings["options"]),
            "l3": self.gamepad.get_button(button_mappings["l3"]),
            "r3": self.gamepad.get_button(button_mappings["r3"]),
            "ps5": self.gamepad.get_button(button_mappings["ps5"]),
            "touchpad": self.gamepad.get_button(button_mappings["touchpad"]),
        }

        # Handle D-pad based on mapping type
        dpad_states = self._get_dpad_states(button_mappings)
        buttons.update(dpad_states)

        # Treat L2/R2 as digital buttons: pressed if axis > 0.5
        l2_axis = (
            self.gamepad.get_axis(axis_mappings["l2"]) if "l2" in axis_mappings else 0.0
        )
        r2_axis = (
            self.gamepad.get_axis(axis_mappings["r2"]) if "r2" in axis_mappings else 0.0
        )
        buttons["l2"] = l2_axis > 0.5
        buttons["r2"] = r2_axis > 0.5
        return buttons

    def _get_dpad_states(self, button_mappings: Dict[str, Any]) -> Dict[str, float]:
        """Get D-pad button states based on mapping type."""
        if not self.gamepad or not self.input_mapping:
            return {}
            
        hat_mappings = self.input_mapping.get_hat_mappings()
        if hat_mappings and "dpad" in hat_mappings:
            dpad_mapping = hat_mappings["dpad"]
            if dpad_mapping == "buttons":
                # USB mode: D-pad as buttons
                return {
                    "dpad_up": self.gamepad.get_button(button_mappings["dpad_up"]),
                    "dpad_down": self.gamepad.get_button(button_mappings["dpad_down"]),
                    "dpad_left": self.gamepad.get_button(button_mappings["dpad_left"]),
                    "dpad_right": self.gamepad.get_button(
                        button_mappings["dpad_right"]
                    ),
                }
            elif dpad_mapping == "hat":
                # Bluetooth mode: D-pad as actual hat
                hat_value = self.gamepad.get_hat(0)
                return {
                    "dpad_up": hat_value[1] == 1,
                    "dpad_down": hat_value[1] == -1,
                    "dpad_left": hat_value[0] == -1,
                    "dpad_right": hat_value[0] == 1,
                }

        # Fallback: D-pad as buttons
        return {
            "dpad_up": self.gamepad.get_button(button_mappings.get("dpad_up", 0)),
            "dpad_down": self.gamepad.get_button(button_mappings.get("dpad_down", 0)),
            "dpad_left": self.gamepad.get_button(button_mappings.get("dpad_left", 0)),
            "dpad_right": self.gamepad.get_button(button_mappings.get("dpad_right", 0)),
        }

    def _check_button_press(self, button_name: str) -> bool:
        """Check if a button was just pressed (not held), with debounce."""
        current = self.button_states.get(button_name, False)
        last = self.last_button_states.get(button_name, False)
        now = time.time()
        if current and not last:
            last_time = self._button_last_press_time.get(button_name, 0)
            if now - last_time >= self.BUTTON_DEBOUNCE_INTERVAL:
                self._button_last_press_time[button_name] = now
                return True
        return False

    def _on_mode_toggled(self, new_mode: str) -> None:
        """
        Handle LED feedback when mode is toggled.
        """
        # Call parent method to start hexapod light animations
        super()._on_mode_toggled(new_mode)

        if not (self.led_controller and self.led_controller.is_available()):
            return
        self.led_controller.stop_animation()
        if new_mode == self.GAIT_CONTROL_MODE:
            self.led_controller.pulse(GamepadLEDColor.INDIGO, duration=2.0, cycles=0)
            self.current_led_state = "gait_mode"
        elif new_mode == self.BODY_CONTROL_MODE:
            self.led_controller.pulse(GamepadLEDColor.BLUE, duration=2.0, cycles=0)
            self.current_led_state = "body_mode"
        elif new_mode == self.VOICE_CONTROL_MODE:
            self.led_controller.pulse_two_colors(
                GamepadLEDColor.BLUE, GamepadLEDColor.GREEN, duration=2.0, cycles=0
            )
            self.current_led_state = "voice_mode"

    def get_inputs(self) -> Dict[str, Any]:
        """Get current input values from the gamepad."""
        # Get gamepad inputs
        self.analog_inputs = self._get_analog_inputs()
        self.button_states = self._get_button_states()

        # Always allow shutdown with PS5 button, regardless of mode
        if self._check_button_press("ps5"):
            self.trigger_shutdown()

        # Handle mode toggles
        if self._check_button_press("options"):
            # Only toggle manual control modes if not in voice control mode
            if self.current_mode != self.VOICE_CONTROL_MODE:
                self.toggle_mode()
        if self._check_button_press("create"):
            self.toggle_voice_control_mode()

        # Only process manual inputs if not in voice control mode
        if self.current_mode == self.BODY_CONTROL_MODE:
            return self._get_body_control_inputs()
        elif self.current_mode == self.GAIT_CONTROL_MODE:
            return self._get_gait_control_inputs()
        else:
            return {}  # No manual input in voice control mode

    def _process_stance_height_l2_r2(self) -> float:
        """Handle L2/R2 stance height adjustment with buffering, timing, and preview printing. Returns stance_height_delta."""
        now = time.time()
        debounce = self.BUTTON_DEBOUNCE_INTERVAL
        l2_held = self.button_states.get("l2", False)
        r2_held = self.button_states.get("r2", False)
        preview_printed = False
        # Track hold start times and last increment times
        for btn, held in [("l2", l2_held), ("r2", r2_held)]:
            if held:
                if self._stance_height_hold_start[btn] is None:
                    self._stance_height_hold_start[btn] = now
                    self._stance_height_last_increment[btn] = now
            else:
                # If released before debounce, treat as a single click
                start = self._stance_height_hold_start[btn]
                if start is not None and (now - start) < debounce:
                    if btn == "l2" and not r2_held:
                        self._stance_height_buffer -= self.GAIT_STANCE_HEIGHT_STEP
                        preview_printed = True
                    elif btn == "r2" and not l2_held:
                        self._stance_height_buffer += self.GAIT_STANCE_HEIGHT_STEP
                        preview_printed = True
                self._stance_height_hold_start[btn] = None
                self._stance_height_last_increment[btn] = None
        # Accumulate buffer only if held long enough, and repeat every debounce interval
        if l2_held and not r2_held:
            start = self._stance_height_hold_start["l2"]
            last = self._stance_height_last_increment["l2"]
            if start is not None and (now - start) >= debounce:
                if last is None or (now - last) >= debounce:
                    self._stance_height_buffer -= self.GAIT_STANCE_HEIGHT_STEP
                    self._stance_height_last_increment["l2"] = now
                    preview_printed = True
        elif r2_held and not l2_held:
            start = self._stance_height_hold_start["r2"]
            last = self._stance_height_last_increment["r2"]
            if start is not None and (now - start) >= debounce:
                if last is None or (now - last) >= debounce:
                    self._stance_height_buffer += self.GAIT_STANCE_HEIGHT_STEP
                    self._stance_height_last_increment["r2"] = now
                    preview_printed = True
        # Print preview if buffer changed this tick
        if preview_printed:
            try:
                base = self.gait_stance_height
            except AttributeError:
                base = 0.0
            preview = base + self._stance_height_buffer
            logger.gamepad_mode_info(f"Gait stance height: {preview:.1f} mm (pending)")
        # When both released, output buffer and reset
        stance_height_delta = 0.0
        if not l2_held and not r2_held and self._stance_height_buffer != 0.0:
            stance_height_delta = self._stance_height_buffer
            self._stance_height_buffer = 0.0
        return stance_height_delta

    def _get_body_control_inputs(self) -> Dict[str, Any]:
        """Process inputs for body control mode."""
        # Process analog inputs for movement (raw values, sensitivity applied in base class)
        tx = self.analog_inputs["left_x"]
        ty = -self.analog_inputs["left_y"]  # Invert Y axis
        roll = self.analog_inputs["right_x"]
        pitch = -self.analog_inputs["right_y"]  # Invert Y axis
        tz = self.analog_inputs["r2"] - self.analog_inputs["l2"]
        yaw = 0.0

        # Process button inputs
        stance_height_delta = 0.0  # Stance height is only for gait mode
        if self._check_button_press("triangle"):
            self.reset_position()
        elif self._check_button_press("square"):
            self.show_current_position()
        elif self._check_button_press("circle"):
            self.print_help()

        # Continuous yaw while holding L1/R1
        if self.button_states.get("l1", False):
            yaw = -1.0  # Raw value, sensitivity applied in base class
        if self.button_states.get("r1", False):
            yaw = 1.0  # Raw value, sensitivity applied in base class

        # Handle D-pad sensitivity adjustments
        sensitivity_deltas = {"translation_delta": 0.0, "rotation_delta": 0.0}

        # D-pad left/right: Adjust translation sensitivity (only on press)
        if self._check_button_press("dpad_left"):
            sensitivity_deltas["translation_delta"] = -self.SENSITIVITY_ADJUSTMENT_STEP

        if self._check_button_press("dpad_right"):
            sensitivity_deltas["translation_delta"] = self.SENSITIVITY_ADJUSTMENT_STEP

        # D-pad down/up: Adjust rotation sensitivity (only on press)
        if self._check_button_press("dpad_down"):
            sensitivity_deltas["rotation_delta"] = -self.SENSITIVITY_ADJUSTMENT_STEP

        if self._check_button_press("dpad_up"):
            sensitivity_deltas["rotation_delta"] = self.SENSITIVITY_ADJUSTMENT_STEP

        # Update button states for next frame
        self.last_button_states = self.button_states.copy()

        return {
            "tx": tx,
            "ty": ty,
            "tz": tz,
            "roll": roll,
            "pitch": pitch,
            "yaw": yaw,
            "sensitivity_deltas": sensitivity_deltas,
            "stance_height_delta": stance_height_delta,
        }

    def _get_gait_control_inputs(self) -> Dict[str, Any]:
        """Process inputs for gait control mode - returns raw input values."""

        # Process analog inputs for gait control (raw values, sensitivity applied in base class)
        # Left stick controls movement direction
        direction_x = self.analog_inputs["left_x"]
        direction_y = -self.analog_inputs["left_y"]  # Invert Y axis

        # Marching toggle logic: just toggle marching_enabled and print status
        if self._check_button_press("x"):
            self.marching_enabled = not self.marching_enabled
            if self.marching_enabled:
                logger.gamepad_mode_info(
                    "Marching (neutral gait) ENABLED. Press X again to stop."
                )
            else:
                logger.gamepad_mode_info(
                    "Marching (neutral gait) DISABLED. Press X to start."
                )

        # Right stick X controls rotation
        rotation = self.analog_inputs["right_x"]

        # Process L2/R2 stance height adjustment
        stance_height_delta = self._process_stance_height_l2_r2()

        # Process button inputs
        if self._check_button_press("triangle"):
            self.reset_position()
        elif self._check_button_press("square"):
            self.show_current_position()
        elif self._check_button_press("circle"):
            self.print_help()
        elif self._check_button_press("ps5"):
            self.trigger_shutdown()

        # Handle D-pad sensitivity adjustments
        sensitivity_deltas = {"translation_delta": 0.0, "rotation_delta": 0.0}

        # D-pad left/right: Adjust gait direction sensitivity (only on press)
        if self._check_button_press("dpad_left"):
            sensitivity_deltas["translation_delta"] = -self.SENSITIVITY_ADJUSTMENT_STEP

        if self._check_button_press("dpad_right"):
            sensitivity_deltas["translation_delta"] = self.SENSITIVITY_ADJUSTMENT_STEP

        # D-pad down/up: Adjust gait rotation sensitivity (only on press)
        if self._check_button_press("dpad_down"):
            sensitivity_deltas["rotation_delta"] = -self.SENSITIVITY_ADJUSTMENT_STEP

        if self._check_button_press("dpad_up"):
            sensitivity_deltas["rotation_delta"] = self.SENSITIVITY_ADJUSTMENT_STEP

        # Update button states for next frame
        self.last_button_states = self.button_states.copy()

        # Return raw input values for base class to process
        return {
            "direction_x": direction_x,
            "direction_y": direction_y,
            "rotation": rotation,
            "sensitivity_deltas": sensitivity_deltas,
            "stance_height_delta": stance_height_delta,
        }

    def print_help(self) -> None:
        """Print the help menu using a single gamepad_mode_info log message."""
        controller_type = (
            type(self.input_mapping).__name__.replace("Mappings", "").replace("_", " ")
        )
        help_message = (
            "\n" + "=" * 60 + "\n"
            f"{controller_type.upper()} GAMEPAD HEXAPOD CONTROLLER\n" + "=" * 60 + "\n"
            "MODE CONTROLS:\n"
            "  Options Button - Toggle between Body Control and Gait Control modes\n"
            "  Create Button  - Toggle Voice Control mode (enable/disable voice commands)\n"
            "\n"
            "BODY CONTROL MODE (Inverse Kinematics):\n"
            "  Left Stick X    - Left/Right translation\n"
            "  Left Stick Y    - Forward/Backward translation\n"
            "  L2/R2 Triggers  - Down/Up translation\n"
            "  Right Stick X   - Roll rotation (left/right)\n"
            "  Right Stick Y   - Pitch rotation (forward/backward)\n"
            "  L1/R1           - Yaw left/right\n"
            "\n"
            "GAIT CONTROL MODE (Walking):\n"
            "  Left Stick      - Movement direction (forward/backward/left/right/diagonal directions)\n"
            "  Right Stick X   - Rotation (clockwise/counterclockwise)\n"
            "  L2/R2           - Raise/Lower gait stance height (body up/down)\n"
            "  X (Cross)       - Toggle marching in place (neutral gait) ON/OFF (default: OFF)\n"
            "      - When marching is OFF, robot stands still when stick is centered.\n"
            "      - When marching is ON, robot marches in place when stick is centered.\n"
            "  The hexapod will walk using its gait generator\n"
            "  Different gait parameters are used for translation vs rotation movements\n"
            "\n"
            "COMMON BUTTON CONTROLS:\n"
            "  Triangle        - Reset to start position (also resets stance height to 0 in gait mode)\n"
            "  Square          - Show current position\n"
            "  Circle          - Show this help menu\n"
            "  PS5             - Shutdown entire program\n"
            "\n"
            "SENSITIVITY CONTROLS (D-Pad):\n"
            "  D-Pad Left/Right - Decrease/Increase translation/gait direction sensitivity\n"
            "  D-Pad Down/Up   - Decrease/Increase rotation/gait rotation sensitivity\n"
            "  (Sensitivity type depends on current mode)\n"
            "\n"
            "LED INDICATORS:\n"
            "  Blue Pulse      - Body control mode (idle)\n"
            "  Purple Pulse    - Gait control mode (idle)\n"
            "  Lime Pulse      - Movement detected (both modes)\n" + "=" * 60
        )
        logger.gamepad_mode_info(help_message)

    def cleanup_controller(self) -> None:
        """Clean up gamepad-specific resources."""
        # Cleanup LED controller
        if hasattr(self, "led_controller") and self.led_controller:
            try:
                if self.led_controller:
                    self.led_controller.turn_off()
                    self.led_controller.cleanup()
                    logger.debug("Gamepad LED turned off")
            except Exception as e:
                logger.exception(f"Error during LED cleanup: {e}")

        # Cleanup pygame
        if PYGAME_AVAILABLE:
            pygame.quit()
