"""
Base manual hexapod controller implementation.

This module provides the abstract base class for all manual hexapod controllers,
defining the common interface and functionality for manual control systems.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import sys
import time
import threading
from pathlib import Path
from abc import ABC, abstractmethod

# Add the src directory to the path so we can import our modules
SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = (SCRIPT_DIR.parent.parent).resolve()
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from robot import PredefinedPosition
from gait_generator import BaseGait, TripodGait
from utils import rename_thread
from lights import ColorRGB

if TYPE_CHECKING:
    from typing import Optional
    from kws import VoiceControl
    from task_interface import TaskInterface
    
logger = logging.getLogger("gamepad_logger")

class ManualHexapodController(threading.Thread, ABC):
    """Abstract base class for all manual hexapod controllers."""
    
    # Movement step parameters (easy to adjust)
    TRANSLATION_STEP = 6.0   # mm per analog unit
    ROLL_STEP = 2.0          # degrees per button press
    PITCH_STEP = 2.0         # degrees per analog unit (if you want to use a different step)
    YAW_STEP = 4.0           # degrees per analog unit (if you want to use a different step)
    Z_STEP = 4.0             # mm per analog unit (for up/down)
    GAIT_STANCE_HEIGHT_STEP = 2.0 # mm per L3/R3 press
    GAIT_MIN_STANCE_HEIGHT = -40.0
    GAIT_MAX_STANCE_HEIGHT = 40.0
    
    # Sensitivity constants
    DEFAULT_TRANSLATION_SENSITIVITY = 0.5
    DEFAULT_ROTATION_SENSITIVITY = 0.5
    DEFAULT_GAIT_DIRECTION_SENSITIVITY = 0.5
    DEFAULT_GAIT_ROTATION_SENSITIVITY = 0.5
    
    # Sensitivity adjustment constants
    SENSITIVITY_ADJUSTMENT_STEP = 0.1
    MIN_SENSITIVITY = 0.1
    MAX_SENSITIVITY = 1.0
    
    # Supported modes
    BODY_CONTROL_MODE = "body_control"
    GAIT_CONTROL_MODE = "gait_control"
    VOICE_CONTROL_MODE = "voice_control"
    DEFAULT_MODE = BODY_CONTROL_MODE
    
    def __init__(self, task_interface: 'TaskInterface', voice_control: Optional['VoiceControl'] = None, shutdown_callback: Optional[callable] = None):
        """Initialize the hexapod controller."""
        super().__init__(daemon=True)
        rename_thread(self, "ManualHexapodController")
        
        # Thread control variables
        self.stop_event = threading.Event()
        
        self.task_interface = task_interface
        self.shutdown_callback = shutdown_callback
        
        # Current movement state
        self.current_tx = 0.0
        self.current_ty = 0.0
        self.current_tz = 0.0
        self.current_roll = 0.0
        self.current_pitch = 0.0
        self.current_yaw = 0.0
        
        # Movement update rate
        self.update_rate = 20  # Hz
        self.update_interval = 1.0 / self.update_rate

        # Dual-mode support
        self.current_mode = self.DEFAULT_MODE

        # Gait steering support - separate instances for translation and rotation
        self.translation_gait = None
        self.rotation_gait = None
        self.current_gait = None  # Points to either translation_gait or rotation_gait
        
        # Gait type for both translation and rotation (must be the same)
        self.gait_type = TripodGait
        
        # Sensitivity for gait control
        self.translation_sensitivity = self.DEFAULT_TRANSLATION_SENSITIVITY
        self.rotation_sensitivity = self.DEFAULT_ROTATION_SENSITIVITY
        self.gait_direction_sensitivity = self.DEFAULT_GAIT_DIRECTION_SENSITIVITY
        self.gait_rotation_sensitivity = self.DEFAULT_GAIT_ROTATION_SENSITIVITY

        self.pause_event = threading.Event()
        self.pause_event.clear()  # Start unpaused (event is set when paused)
        self._previous_manual_mode = self.DEFAULT_MODE
        self.voice_control: Optional['VoiceControl'] = voice_control
        self.marching_enabled = False  # Marching (neutral gait) is off by default; set by subclass
        
        # Gait stance height (mm)
        # Try to get default from config, else 0.0
        try:
            self.gait_stance_height = float(self.task_interface.hexapod.gait_params.get('translation', {}).get('stance_height', 0.0))
        except Exception:
            self.gait_stance_height = 0.0
    
    @abstractmethod
    def get_inputs(self):
        """Get current input values from the interface."""
        pass
    
    @abstractmethod
    def print_help(self):
        """Print help information for the interface."""
        pass
    
    def cleanup(self):
        """Clean up common resources (gait generation, servos)."""
        try:
            # Stop light animations
            self.task_interface.lights_handler.off()
            
            # Stop gait generation if running
            if hasattr(self.task_interface.hexapod, 'gait_generator'):
                if self.task_interface.hexapod.gait_generator.is_running:
                    self.task_interface.hexapod.gait_generator.stop()
                    logger.debug("Gait generation stopped")
            
            # Reset to safe position and deactivate servos
            self.reset_position()
            self.task_interface.hexapod.deactivate_all_servos()
            logger.debug("Hexapod servos deactivated")
        except Exception as e:
            logger.exception(f"Error during base cleanup: {e}")
        
        # Call subclass-specific cleanup
        self.cleanup_controller()

    @abstractmethod
    def cleanup_controller(self):
        """Clean up resources specific to this controller type."""
        pass
    
    def set_mode(self, mode_name: str):
        """Set the current control mode (e.g., 'body_control', 'gait_control')."""
        if mode_name not in (self.BODY_CONTROL_MODE, self.GAIT_CONTROL_MODE, self.VOICE_CONTROL_MODE):
            raise ValueError(f"Unknown mode: {mode_name}")
        self.current_mode = mode_name
        logger.user_info(f"Switched to mode: {self.current_mode}")

    def reset_position(self):
        """Reset hexapod to reset position. Also resets stance height and gait instance in gait mode."""
        def _get_reset_position():
            """Return the PredefinedPosition to use for reset_position. Can be mode-dependent."""
            if self.current_mode == self.GAIT_CONTROL_MODE:
                return PredefinedPosition.ZERO
            return PredefinedPosition.LOW_PROFILE
        
        try:
            reset_position = _get_reset_position()
            self.task_interface.hexapod.move_to_position(reset_position)
            self.task_interface.hexapod.wait_until_motion_complete()

            # Reset current state
            self.current_tx = 0.0
            self.current_ty = 0.0
            self.current_tz = 0.0
            self.current_roll = 0.0
            self.current_pitch = 0.0
            self.current_yaw = 0.0

            # If in gait control mode, reset stance height and gait instance
            if self.current_mode == self.GAIT_CONTROL_MODE:
                # Enforce stance height 0
                self.gait_stance_height = 0.0
                gait_params = self.task_interface.hexapod.gait_params
                if 'translation' in gait_params:
                    gait_params['translation']['stance_height'] = 0.0
                if 'rotation' in gait_params:
                    gait_params['rotation']['stance_height'] = 0.0
                translation_params = gait_params.get('translation', {}).copy()
                rotation_params = gait_params.get('rotation', {}).copy()
                translation_params['stance_height'] = 0.0
                rotation_params['stance_height'] = 0.0
                self.task_interface.hexapod.gait_generator.create_gait('tripod', **translation_params)
                self.translation_gait = self.task_interface.hexapod.gait_generator.current_gait
                self.task_interface.hexapod.gait_generator.create_gait('tripod', **rotation_params)
                self.rotation_gait = self.task_interface.hexapod.gait_generator.current_gait
                self.current_gait = self.translation_gait

            logger.debug("Reset position completed")
        except Exception as e:
            logger.exception(f"Reset failed: {e}")
    
    def start_gait_control(self, gait_type=None, translation_params=None, rotation_params=None):
        """
        Start gait control with separate parameters for translation and rotation.
        
        Args:
            gait_type: The gait class to use (default: TripodGait)
            translation_params: Parameters for translation movement (dict)
            rotation_params: Parameters for rotation movement (dict)
        """
        
        # Set gait type if provided
        if gait_type is not None:
            self.gait_type = gait_type
        
        # Use global gait params from hexapod if available
        if translation_params is None:
            translation_params = self.task_interface.hexapod.gait_params.get('translation', {}).copy()
        if rotation_params is None:
            rotation_params = self.task_interface.hexapod.gait_params.get('rotation', {}).copy()
        
        # Create separate gait instances for translation and rotation using the new API
        self.task_interface.hexapod.gait_generator.create_gait('tripod', **translation_params)
        self.translation_gait = self.task_interface.hexapod.gait_generator.current_gait
        
        # Create rotation gait by temporarily switching parameters
        self.task_interface.hexapod.gait_generator.create_gait('tripod', **rotation_params)
        self.rotation_gait = self.task_interface.hexapod.gait_generator.current_gait
        
        # Start with translation gait as default
        self.current_gait = self.translation_gait
        
        if not self.is_gait_control_active():
            self.task_interface.hexapod.gait_generator.start()
            msg = (
                f"\nGait generation started\n"
                f"Translation gait: {translation_params}\n"
                f"Rotation gait: {rotation_params}"
            )
            logger.gamepad_mode_info(msg)

    def stop_gait_control(self):
        """Stop gait control if running."""
        if self.is_gait_control_active():
            self.task_interface.hexapod.gait_generator.stop()
            logger.gamepad_mode_info("Gait generation stopped")

    def is_gait_control_active(self):
        """Return True if gait generator is running."""
        return self.task_interface.hexapod.gait_generator.is_gait_running()
    
    def _process_stance_height_delta(self, inputs):
        """Process gait stance height delta: only affect gait control mode."""
        stance_height_delta = inputs.get('stance_height_delta', 0.0)
        if abs(stance_height_delta) > 0.0 and self.current_mode == self.GAIT_CONTROL_MODE:
            old_stance = self.gait_stance_height
            self.gait_stance_height = max(self.GAIT_MIN_STANCE_HEIGHT, min(self.GAIT_MAX_STANCE_HEIGHT, self.gait_stance_height + stance_height_delta))
            logger.gamepad_mode_info(f"Gait stance height: {self.gait_stance_height:.1f} mm")
            if self.current_gait is not None:
                self.current_gait.stance_height = self.gait_stance_height
            # Also update config so new gait instances use the new value
            gait_params = self.task_interface.hexapod.gait_params
            if 'translation' in gait_params:
                gait_params['translation']['stance_height'] = self.gait_stance_height
            if 'rotation' in gait_params:
                gait_params['rotation']['stance_height'] = self.gait_stance_height
            # Restart the gait generator to apply the new stance height immediately
            if self.is_gait_control_active():
                self.stop_gait_control()
                translation_params = gait_params.get('translation', {}).copy()
                rotation_params = gait_params.get('rotation', {}).copy()
                self.start_gait_control(
                    gait_type=self.gait_type,
                    translation_params=translation_params,
                    rotation_params=rotation_params
                )

    def process_movement_inputs(self, inputs):
        """
        Process movement inputs and apply them based on current mode.
        
        This method handles both body control and gait control modes:
        - Body Control Mode: Applies translation and rotation to hexapod body
        - Gait Control Mode: Updates gait direction and rotation inputs
        
        Args:
            inputs (dict): Input values from get_inputs() method
        """
        # Handle D-pad sensitivity deltas
        self._process_sensitivity_deltas(inputs)
        # Handle stance height steering
        self._process_stance_height_delta(inputs)
        # Route to appropriate processing based on mode
        if self.current_mode == self.BODY_CONTROL_MODE:
            self._process_body_control(inputs)
        elif self.current_mode == self.GAIT_CONTROL_MODE:
            self._process_gait_control(inputs)
        else:
            logger.warning(f"Unknown mode '{self.current_mode}'")
    
    def _process_body_control(self, inputs):
        """Process inputs for body control mode (direct IK movement)."""
        # Extract movement values and apply sensitivity
        tx = inputs.get('tx', 0.0) * self.translation_sensitivity * self.TRANSLATION_STEP
        ty = inputs.get('ty', 0.0) * self.translation_sensitivity * self.TRANSLATION_STEP
        tz = inputs.get('tz', 0.0) * self.translation_sensitivity * self.Z_STEP
        roll = inputs.get('roll', 0.0) * self.rotation_sensitivity * self.ROLL_STEP
        pitch = inputs.get('pitch', 0.0) * self.rotation_sensitivity * self.PITCH_STEP
        yaw = inputs.get('yaw', 0.0) * self.rotation_sensitivity * self.YAW_STEP
        
        # Apply movement if any input is non-zero
        if any(abs(val) > 0.01 for val in [tx, ty, tz, roll, pitch, yaw]):
            try:
                # Apply movement to hexapod
                self.task_interface.hexapod.move_body(tx=tx, ty=ty, tz=tz, roll=roll, pitch=pitch, yaw=yaw)

                # Update current state
                self.current_tx += tx
                self.current_ty += ty
                self.current_tz += tz
                self.current_roll += roll
                self.current_pitch += pitch
                self.current_yaw += yaw
            
            except Exception as e:
                logger.exception(f"Movement failed: {e}")

    def _process_gait_control(self, inputs):
        """Process inputs for gait control mode (walking movement)."""
        def _update_gait_direction(direction, rotation=0.0):
            """Update the gait direction and rotation input."""
            if self.current_gait:
                self.task_interface.hexapod.gait_generator.queue_direction(direction, rotation)

        # Extract gait control values and apply sensitivity
        direction_x = inputs.get('direction_x', 0.0) * self.gait_direction_sensitivity
        direction_y = inputs.get('direction_y', 0.0) * self.gait_direction_sensitivity
        rotation = inputs.get('rotation', 0.0) * self.gait_rotation_sensitivity

        # If marching is disabled and all movement is neutral, stop gait generator if running and do not update gait
        if not self.marching_enabled and abs(direction_x) < 0.01 and abs(direction_y) < 0.01 and abs(rotation) < 0.01:
            if self.is_gait_control_active():
                self.stop_gait_control()
            return
        # If gait is not running, start it now (first nonzero input or marching enabled)
        if not self.is_gait_control_active():
            translation_params = self.task_interface.hexapod.gait_params.get('translation', {}).copy()
            rotation_params = self.task_interface.hexapod.gait_params.get('rotation', {}).copy()
            self.start_gait_control(
                gait_type=self.gait_type,
                translation_params=translation_params,
                rotation_params=rotation_params
            )

        # Determine if we need to switch gait instances based on movement type
        has_translation = abs(direction_x) > 0.01 or abs(direction_y) > 0.01
        has_rotation = abs(rotation) > 0.01

        # Switch gait instance if needed
        if has_rotation and not has_translation:
            # Pure rotation - use rotation gait
            if self.current_gait != self.rotation_gait:
                self.current_gait = self.rotation_gait
                # Update the gait generator with the new gait instance
                if self.is_gait_control_active():
                    self.task_interface.hexapod.gait_generator.stop()
                    # Create the rotation gait in the generator
                    rotation_params = self.task_interface.hexapod.gait_params.get('rotation', {}).copy()
                    self.task_interface.hexapod.gait_generator.create_gait('tripod', **rotation_params)
                    self.task_interface.hexapod.gait_generator.start()
        elif has_translation:
            # Has translation (with or without rotation) - use translation gait
            if self.current_gait != self.translation_gait:
                self.current_gait = self.translation_gait
                # Update the gait generator with the new gait instance
                if self.is_gait_control_active():
                    self.task_interface.hexapod.gait_generator.stop()
                    # Create the translation gait in the generator
                    translation_params = self.task_interface.hexapod.gait_params.get('translation', {}).copy()
                    self.task_interface.hexapod.gait_generator.create_gait('tripod', **translation_params)
                    self.task_interface.hexapod.gait_generator.start()

        # Update gait direction and rotation
        if hasattr(self, 'current_gait') and self.current_gait is not None:
            # Update gait direction and rotation (no normalization - magnitude affects step size)
            _update_gait_direction((direction_x, direction_y), rotation=rotation)
    
    def _process_sensitivity_deltas(self, inputs):
        """Process sensitivity adjustments using the inputs dictionary."""
        sensitivity_deltas = inputs.get('sensitivity_deltas', {})
        
        # Apply translation-related sensitivity adjustment
        if sensitivity_deltas.get('translation_delta', 0.0) != 0.0:
            if self.current_mode == self.BODY_CONTROL_MODE:
                self.translation_sensitivity = max(self.MIN_SENSITIVITY, min(self.MAX_SENSITIVITY, self.translation_sensitivity + sensitivity_deltas['translation_delta']))
                logger.gamepad_mode_info(f"Translation sensitivity: {self.translation_sensitivity:.2f}")
            elif self.current_mode == self.GAIT_CONTROL_MODE:
                self.gait_direction_sensitivity = max(self.MIN_SENSITIVITY, min(self.MAX_SENSITIVITY, self.gait_direction_sensitivity + sensitivity_deltas['translation_delta']))
                logger.gamepad_mode_info(f"Gait direction sensitivity: {self.gait_direction_sensitivity:.2f}")
        
        # Apply rotation-related sensitivity adjustment
        if sensitivity_deltas.get('rotation_delta', 0.0) != 0.0:
            if self.current_mode == self.BODY_CONTROL_MODE:
                self.rotation_sensitivity = max(self.MIN_SENSITIVITY, min(self.MAX_SENSITIVITY, self.rotation_sensitivity + sensitivity_deltas['rotation_delta']))
                logger.gamepad_mode_info(f"Rotation sensitivity: {self.rotation_sensitivity:.2f}")
            elif self.current_mode == self.GAIT_CONTROL_MODE:
                self.gait_rotation_sensitivity = max(self.MIN_SENSITIVITY, min(self.MAX_SENSITIVITY, self.gait_rotation_sensitivity + sensitivity_deltas['rotation_delta']))
                logger.gamepad_mode_info(f"Gait rotation sensitivity: {self.gait_rotation_sensitivity:.2f}")

    def show_gait_status(self):
        """
        Display current gait generator status in gait control mode.
        
        Shows comprehensive information about the current gait state including:
        - Gait type and current phase
        - Which legs are in swing vs stance
        - Timing parameters (dwell time, step radius)
        - Current movement inputs with human-readable names
        - All leg positions
        
        This method is called by show_current_position() when in gait control mode.
        """
        def _get_direction_name(direction_tuple):
            """Get the closest direction name from BaseGait.DIRECTION_MAP."""
            # Check if direction magnitude is very small (near center)
            magnitude = (direction_tuple[0] ** 2 + direction_tuple[1] ** 2) ** 0.5
            if magnitude < 0.05:
                return "neutral"
            
            # Find the closest non-neutral direction by computing distances
            min_dist = float('inf')
            closest_name = None
            for name, vec in BaseGait.DIRECTION_MAP.items():
                # Skip 'neutral' when searching for closest direction
                if name == "neutral":
                    continue
                # Compute Euclidean distance between current direction and named direction
                dist = ((direction_tuple[0] - vec[0]) ** 2 + (direction_tuple[1] - vec[1]) ** 2) ** 0.5
                if dist < min_dist:
                    min_dist = dist
                    closest_name = name
            return closest_name
        
        def _get_rotation_name(rotation):
            """Get a human-readable name for the rotation value."""
            # Use small threshold to determine if rotation is effectively zero
            if abs(rotation) < 0.05:
                return "none"
            elif rotation > 0:
                return "clockwise"
            else:
                return "counterclockwise"
        
        # Check if gait is active
        if not hasattr(self, 'current_gait') or self.current_gait is None:
            logger.warning("No gait is currently active.")
            return
        lines = []
        lines.append("\nGait Control Mode Status:")
        lines.append(f"- Gait Type: {type(self.current_gait).__name__}")
        # Display current gait instance info
        if self.current_gait == self.translation_gait:
            lines.append("- Current Gait: Translation Gait")
        elif self.current_gait == self.rotation_gait:
            lines.append("- Current Gait: Rotation Gait")
        # Display parameters for both gaits
        if self.current_gait == self.translation_gait:
            lines.append(f"- Translation Gait Parameters:")
            lines.append(f"  Step Radius: {getattr(self.translation_gait, 'step_radius', 'N/A')} mm")
            lines.append(f"  Leg Lift Distance: {getattr(self.translation_gait, 'leg_lift_distance', 'N/A')} mm")
            lines.append(f"  Dwell Time: {getattr(self.translation_gait, 'dwell_time', 'N/A')}s")
        if self.current_gait == self.rotation_gait:
            lines.append(f"- Rotation Gait Parameters:")
            lines.append(f"  Step Radius: {getattr(self.rotation_gait, 'step_radius', 'N/A')} mm")
            lines.append(f"  Leg Lift Distance: {getattr(self.rotation_gait, 'leg_lift_distance', 'N/A')} mm")
            lines.append(f"  Dwell Time: {getattr(self.rotation_gait, 'dwell_time', 'N/A')}s")
        # Try to get current phase/state information from gait generator
        current_state = getattr(self.task_interface.hexapod.gait_generator, 'current_state', None)
        if current_state:
            lines.append(f"- Current Phase: {getattr(current_state, 'phase', 'N/A')}")
            lines.append(f"- Swing Legs: {getattr(current_state, 'swing_legs', 'N/A')}")
            lines.append(f"- Stance Legs: {getattr(current_state, 'stance_legs', 'N/A')}")
            lines.append(f"- Dwell Time: {getattr(current_state, 'dwell_time', 'N/A')}s")
        # Show current direction with human-readable name
        direction = getattr(self.current_gait, 'direction_input', (0.0, 0.0))
        if hasattr(direction, 'to_tuple'):
            x, y = direction.to_tuple()
        else:
            x, y = direction[0], direction[1]
        direction_name = _get_direction_name((x, y))
        
        # Show current rotation with human-readable name
        rotation = getattr(self.current_gait, 'rotation_input', 0.0)
        rotation_name = _get_rotation_name(rotation)
        lines.append(f"- Current Direction: X={x:.2f}, Y={y:.2f} ({direction_name})")
        lines.append(f"- Current Rotation: {rotation:.2f} ({rotation_name})")
        lines.append(f"- Gait Stance Height: {self.gait_stance_height:.1f} mm")
        # Display all leg positions
        lines.append("- Leg Positions:")
        for i, pos in enumerate(self.task_interface.hexapod.current_leg_positions):
            lines.append(f"    Leg {i}: {tuple(round(x, 2) for x in pos)}")
        logger.gamepad_mode_info("\n".join(lines))

    def print_current_position_details(self):
        """
        Print the current body position and orientation in a formatted way.
        
        Displays the current translation (X, Y, Z) and rotation (Roll, Pitch, Yaw)
        values in a user-friendly format with proper units and alignment.
        
        This method is called by show_current_position() when in body control mode.
        """
        msg = (
            f"\nCurrent Position:\n"
            f" Translation: X={self.current_tx:4.1f}, Y={self.current_ty:4.1f}, Z={self.current_tz:4.1f} mm\n"
            f"  Rotation:    Roll={self.current_roll:4.1f}, Pitch={self.current_pitch:4.1f}, Yaw={self.current_yaw:4.1f}°\n"
        )
        logger.gamepad_mode_info(msg)

    def print_current_sensitivity_levels(self):
        """Print the current sensitivity levels for the controller."""
        msg = (
            "\nCurrent Sensitivity Levels:\n"
            f"Translation Sensitivity: {self.translation_sensitivity:.2f}\n"
            f"Rotation Sensitivity: {self.rotation_sensitivity:.2f}\n"
            f"Gait Direction Sensitivity: {self.gait_direction_sensitivity:.2f}\n"
            f"Gait Rotation Sensitivity: {self.gait_rotation_sensitivity:.2f}"
        )
        logger.gamepad_mode_info(msg)

    def show_current_position(self):
        """
        Display current movement state or gait status depending on mode.
        
        This method provides context-appropriate feedback:
        - In body control mode: Shows current translation and rotation values
        - In gait control mode: Shows detailed gait status with direction/rotation names
        
        Called when user presses the "show current position" button.
        """
        if self.current_mode == self.GAIT_CONTROL_MODE:
            # In gait mode, show comprehensive gait status
            self.show_gait_status()
        else:
            # In body control mode, show position details
            self.print_current_position_details()
        
        # Always show current sensitivity levels
        self.print_current_sensitivity_levels()
    
    def run(self):
        """Run the hexapod controller thread."""
        self.print_help()
        self.reset_position()
        self._start_initial_animation()
        
        last_update = time.time()
        
        while not self.stop_event.is_set():
            try:
                current_time = time.time()
                
                # Update at fixed rate
                if current_time - last_update >= self.update_interval:
                    inputs = self.get_inputs()
                    # Only process inputs if not paused (pause_event is set when paused)
                    if self.pause_event.is_set():
                        time.sleep(0.1)
                        continue
                    self.process_movement_inputs(inputs)
                    last_update = current_time
                
                # Small sleep to prevent high CPU usage
                time.sleep(0.01)
                
            except Exception as e:
                logger.exception(f"Error during controller loop: {e}")
                break

    def toggle_mode(self):
        """
        Toggle between body control and gait control modes.
        Handles all printouts, state changes, and gait start/stop.
        Calls _on_mode_toggled(new_mode) for subclass-specific actions (e.g., LED feedback).
        """
        if self.current_mode == self.BODY_CONTROL_MODE:
            # Switch to gait control mode
            self.set_mode(self.GAIT_CONTROL_MODE)
            msg = (
                f"\n=== SWITCHED TO GAIT CONTROL MODE ===\n"
                "Left Stick: Movement direction\n"
                "Right Stick X: Rotation (clockwise/counterclockwise)\n"
                "The hexapod will walk using its gait generator\n"
                "Different gait parameters are used for translation vs rotation movements"
            )
            logger.gamepad_mode_info(msg)
            self.reset_position()
            # Only start gait control if marching is enabled or there is a nonzero input
            # (We can't check stick input here, so only allow auto-start if marching is enabled)
            if self.marching_enabled:
                translation_params = self.task_interface.hexapod.gait_params.get('translation', {}).copy()
                rotation_params = self.task_interface.hexapod.gait_params.get('rotation', {}).copy()
                self.start_gait_control(
                    gait_type=self.gait_type,
                    translation_params=translation_params,
                    rotation_params=rotation_params
                )
        else:
            # Switch to body control mode
            self.set_mode(self.BODY_CONTROL_MODE)
            msg = (
                f"\n=== SWITCHED TO BODY CONTROL MODE ===\n"
                "Left Stick: Body translation\n"
                "Right Stick: Body rotation\n"
                "The hexapod will move its body using inverse kinematics"
            )
            logger.gamepad_mode_info(msg)
            self.stop_gait_control()
            self.reset_position()
        self._on_mode_toggled(self.current_mode)

    def _on_mode_toggled(self, new_mode: str):
        """
        Hook for subclasses to perform additional actions (e.g., LED feedback) when mode is toggled.
        By default, starts appropriate light animations based on the mode.
        """
        # Start appropriate light animation based on mode
        if new_mode == self.BODY_CONTROL_MODE:
            self.task_interface.lights_handler.pulse_smoothly(base_color=ColorRGB.BLUE, pulse_color=ColorRGB.BLACK, pulse_speed=0.05)
        elif new_mode == self.GAIT_CONTROL_MODE:
            self.task_interface.lights_handler.think(color=ColorRGB.INDIGO)
        elif new_mode == self.VOICE_CONTROL_MODE:
            self.stop_gait_control()

    def _start_initial_animation(self):
        """
        Start the initial light animation based on the current mode.
        """
        if self.current_mode == self.BODY_CONTROL_MODE:
            self.task_interface.lights_handler.pulse_smoothly(base_color=ColorRGB.BLUE, pulse_color=ColorRGB.BLACK, pulse_speed=0.05)
        elif self.current_mode == self.GAIT_CONTROL_MODE:
            self.task_interface.lights_handler.think(color=ColorRGB.INDIGO)
        elif self.current_mode == self.VOICE_CONTROL_MODE:
            pass

    def pause(self):
        """Pause the manual controller (stop processing inputs)."""
        self.pause_event.set()

    def unpause(self):
        """Unpause the manual controller (resume processing inputs)."""
        self.pause_event.clear()

    def toggle_voice_control_mode(self):
        """
        Toggle between manual (body/gait) and voice control mode.
        Pauses/unpauses the appropriate controller. If voice_control is None, do nothing and print a warning.
        """
        if self.voice_control is None:
            logger.warning("Voice control is not available. Cannot switch to voice control mode.")
            return
        if self.current_mode != self.VOICE_CONTROL_MODE:
            # Enter voice control mode
            self._previous_manual_mode = self.current_mode
            self.set_mode(self.VOICE_CONTROL_MODE)
            msg = (
                "\n=== SWITCHED TO VOICE CONTROL MODE ===\n"
                "Manual control paused. Voice control active."
            )
            logger.gamepad_mode_info(msg)
            self.pause()
            self.voice_control.unpause()
        else:
            # Return to previous manual mode
            self.set_mode(self._previous_manual_mode)
            msg = (
                f"\n=== RETURNED TO {self.current_mode.upper()} ===\n"
                "Manual control active. Voice control paused."
            )
            logger.gamepad_mode_info(msg)
            self.voice_control.pause()
            self.unpause()
            # If returning to gait control mode, restart gait generation
            if self.current_mode == self.GAIT_CONTROL_MODE:
                translation_params = self.task_interface.hexapod.gait_params.get('translation', {}).copy()
                rotation_params = self.task_interface.hexapod.gait_params.get('rotation', {}).copy()
                self.start_gait_control(
                    gait_type=self.gait_type,
                    translation_params=translation_params,
                    rotation_params=rotation_params
                )
        self._on_mode_toggled(self.current_mode)

    def trigger_shutdown(self):
        """Trigger program shutdown via callback if provided."""
        if self.shutdown_callback:
            self.shutdown_callback()
        else:
            # Fallback: just stop this controller
            self.stop()

    def stop(self):
        """Stop the manual controller."""
        self.stop_event.set()
        self.cleanup()