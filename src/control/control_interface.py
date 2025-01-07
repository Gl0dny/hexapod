from typing import Callable, Any, Optional
import logging
import sys
import os
import threading
from functools import wraps
from types import MethodType

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lights import LightsInteractionHandler
from lights.lights import ColorRGB
from robot.hexapod import Hexapod
from control.control_tasks import *

logger = logging.getLogger(__name__)

class ControlInterface:
    def __init__(self, voice_control_context_info: Optional[str] = None):
        """
        Initialize the ControlInterface object.

        Args:
            voice_control_context_info (Optional[str]): The context information from Picovoice.
        """
        self.hexapod = Hexapod()
        self.lights_handler = LightsInteractionHandler(self.hexapod.leg_to_led)
        self.control_task: ControlTask = None
        self.voice_control_context_info = voice_control_context_info
        self._last_command = None
        self._last_args = None
        self._last_kwargs = None
        logger.info("ControlInterface initialized with Lights and Hexapod.")

    def inject_hexapod(func):
        """
        Decorator to inject self.hexapod into the decorated function.
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, self.hexapod, *args, **kwargs)
        return wrapper

    def inject_lights_handler(func):
        """
        Decorator to inject self.lights_handler into the decorated function.
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, self.lights_handler, *args, **kwargs)
        return wrapper

    def stop_control_task(self) -> None:
        """
        Stop any running control_task and reset the control_task attribute.
        """
        if hasattr(self, 'control_task') and self.control_task:
            self.control_task.stop_task()
            self.control_task = None

    def control_task(method: Callable[..., Any]) -> Callable[..., Any]:
        """
        Decorator to ensure that a method sets the 'self.control_task' attribute.

        Args:
            method (function): The method to wrap.

        Returns:
            function: Wrapped method.
        """
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            self._store_last_command(method, *args, **kwargs)
            method(self, *args, **kwargs)
            if not hasattr(self, 'control_task') or self.control_task is None:
                raise AttributeError(
                    f"{method.__name__} must set 'self.control_task' attribute")
        return wrapper

    @inject_lights_handler
    def hexapod_help(self, lights_handler):
        logger.info("Executing help.")
        if self.voice_control_context_info:
            print(f"Picovoice Context Info: {self.voice_control_context_info}")
        else:
            print("No context information available.")
        lights_handler.ready()

    def system_status(self):
        logger.info("Executing system_status.")
        # Implement system status reporting
        # Example: Return current status of all modules
        raise NotImplementedError("The system_status method is not yet implemented.")

    @inject_lights_handler
    def shut_down(self, lights_handler):
        logger.info("Shutting down robot. System will power off in 10 seconds. Press any key to cancel.")
        shutdown_timer = threading.Timer(10.0, self._perform_shutdown)
        shutdown_timer.start()
        try:
            input("Press any key to cancel shutdown...\n")
            shutdown_timer.cancel()
            logger.info("Shutdown canceled by user.")
            lights_handler.ready()

        except EOFError:
            logger.warning("Input stream closed. Shutdown will proceed.")
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
            lights_handler.set_single_color(ColorRGB.RED)
        finally:
            logger.info("Shutdown sequence complete.")

    def _perform_shutdown(self):
        logger.info("Shutting down the system now.")
        os.system("sudo shutdown now")

    def emergency_stop(self):
        logger.info("Executing emergency_stop.")
        # Implement emergency stop logic here
        # Example: Immediately halt all movements and actions
        raise NotImplementedError("The emergency_stop method is not yet implemented.")

    @control_task
    @inject_lights_handler
    @inject_hexapod
    def wake_up(self, hexapod, lights_handler) -> None:
        try:
            logger.info("Activating robot...")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = WakeUpTask(hexapod, lights_handler)
            self.control_task.start()
            print("Robot activated")
            
        except Exception as e:
            logger.error(f"Aactivating robot failed: {e}")

    @control_task
    @inject_lights_handler
    @inject_hexapod
    def sleep(self, hexapod, lights_handler) -> None:
        try:
            logger.info("Deactivating robot...")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = SleepTask(hexapod, lights_handler)
            self.control_task.start()
            print("Robot deactivated")
            
        except Exception as e:
            logger.error(f"Deactivating robot failed: {e}")

    @control_task
    @inject_lights_handler
    @inject_hexapod
    def calibrate(self, hexapod, lights_handler) -> None:
        """
        Initiates the calibration process in a separate thread to avoid blocking other activities.
        """
        try:
            print("Initiating calibration process.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = CompositeCalibrationTask(hexapod, lights_handler)
            self.control_task.start()
            print("Calibration process started.")
        
        except Exception as e:
            logger.error(f"Calibration failed: {e}")

    def run_sequence(self, sequence_name):
        logger.info(f"Executing run_sequence: {sequence_name}.")
        # Implement run sequence logic here
        # Example: Trigger predefined action sequence
        raise NotImplementedError("The run_sequence method is not yet implemented.")

    @inject_lights_handler
    def repeat_last_command(self, lights_handler):
        if self._last_command:
            logger.info(f"Repeating last command: {self._last_command.__name__}")
            self._last_command(*self._last_args, **self._last_kwargs)
        else:
            logger.info("No last command to repeat.")
            lights_handler.ready()
        
    def _store_last_command(self, func, *args, **kwargs):
        if not isinstance(func, MethodType):
            func = MethodType(func, self)
        self._last_command = func
        self._last_args = args
        self._last_kwargs = kwargs
            
    @inject_lights_handler
    def turn_lights(self, lights_handler, switch_state):
        """
        Turns the lights on or off based on the switch state.
        
        Args:
            lights_handler (LightsInteractionHandler): The lights handler instance.
            switch_state (str): State to switch the lights to ('on' or 'off').
        """
        if switch_state == 'off':
            logger.info("Turning lights off")
            lights_handler.off()
        else:
            logger.info("Turning lights on")
            lights_handler.wakeup()

    @inject_lights_handler
    def change_color(self, lights_handler, color):
        """
        Changes the color of the lights.
        
        Args:
            lights_handler (LightsInteractionHandler): The lights handler instance.
            color (str): The color to change the lights to.
        """
        try:
            enum_color = ColorRGB[color.upper()]
            logger.info(f"Switching color of the lights to {color}")
            lights_handler.lights.set_color(enum_color)
        except KeyError:
            logger.error(f"Color '{color}' is not supported.")

    @inject_lights_handler
    def set_brightness(self, lights_handler, brightness_percentage):
        logger.info(f"Setting brightness to {brightness_percentage}%.")
        lights_handler.set_brightness(brightness_percentage)

    @inject_hexapod
    def set_speed(self, hexapod, speed_percentage):
        logger.info(f"Setting speed to {speed_percentage}%.")
        hexapod.set_all_servos_speed(speed_percentage)
    
    @inject_hexapod
    def set_acceleration(self, hexapod, accel_percentage):
        logger.info(f"Setting acceleration to {accel_percentage}%.")
        hexapod.set_all_servos_accel(accel_percentage)

    @control_task
    @inject_lights_handler
    @inject_hexapod
    def set_low_profile_mode(self, hexapod, lights_handler):
        """
        Initiates low-profile mode in a separate thread.
        """
        try:
            logger.info("Setting robot to low profile mode.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = LowProfileTask(hexapod, lights_handler)
            self.control_task.start()

        except Exception as e:
            logger.error(f"Setting low profile mode failed: {e}")

    @control_task
    @inject_lights_handler
    @inject_hexapod
    def set_upright_mode(self, hexapod, lights_handler):
        """
        Initiates upright mode in a separate thread.
        """
        try:
            logger.info("Setting robot to upright mode.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = UprightModeTask(hexapod, lights_handler)
            self.control_task.start()
            
        except Exception as e:
            logger.error(f"Setting upright mode failed: {e}")

    @control_task
    @inject_lights_handler
    @inject_hexapod
    def idle_stance(self, hexapod, lights_handler) -> None:
        """
        Initiates the idle stance by setting the hexapod to the home position.
        """
        try:
            logger.info("Setting robot to idle stance...")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = IdleStanceTask(hexapod, lights_handler)
            self.control_task.start()
            print("Robot is now in idle stance.")
                
        except Exception as e:
            logger.error(f"Setting idle stance failed: {e}")

    def move(self, direction):
        logger.info(f"Executing move: {direction}")
        # Implement movement logic here
        # Example: Send command to servo controller
        # Update state if using StateManager
        # self.state_manager.set_state(RobotState.MOVING)
        raise NotImplementedError("The move method is not yet implemented.")

    def stop(self):
        logger.info("Executing stop.")
        # Implement stop logic here
        raise NotImplementedError("The stop method is not yet implemented.")

    def rotate(self, angle=None, direction=None):
        if angle:
            logger.info(f"Rotating robot by {angle} degrees.")
            # Implement rotation logic based on angle
        elif direction:
            logger.info(f"Rotating robot to the {direction}.")
            # Implement rotation logic based on direction
        else:
            logger.error("No angle or direction provided for rotation.")

        raise NotImplementedError("The rotate method is not yet implemented.")

    def follow(self):
        logger.info("Executing follow.")
        # Implement follow logic here
        # Example: Start tracking mode
        raise NotImplementedError("The follow method is not yet implemented.")

    def sound_source_analysis(self):
        logger.info("Executing sound_source_analysis.")
        # Implement sound source analysis logic here
        # Example: Activate ODAS system
        raise NotImplementedError("The sound_source_analysis method is not yet implemented.")

    def direction_of_arrival(self):
        logger.info("Executing direction_of_arrival.")
        # Implement direction of arrival logic here
        # Example: Determine sound direction
        raise NotImplementedError("The direction_of_arrival method is not yet implemented.")

    @inject_lights_handler
    def police(self, lights_handler) -> None:
        """
        Initiates the police pulsing animation.
        """
        try:
            logger.info("Turning on police lights...")
            lights_handler.police()
                
        except Exception as e:
            logger.error(f"Turning on police lights failed: {e}")

    def sit_up(self):
        logger.info("Executing sit_up.")
        # Implement sit-up routine
        # Example: Control servos to perform sit-ups
        raise NotImplementedError("The sit_up method is not yet implemented.")

    def dance(self):
        logger.info("Performing dance routine.")
        # Implement dance routine
        raise NotImplementedError("The dance method is not yet implemented.")

    @control_task
    @inject_lights_handler
    @inject_hexapod
    def helix(self, hexapod, lights_handler) -> None:
        """
        Initiates the helix maneuver using HelixTask.
        """
        try:
            print("Initiating helix maneuver.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = HelixTask(hexapod, lights_handler)
            self.control_task.start()
            print("Helix maneuver initiated.")
            
        except Exception as e:
            logger.error(f"Helix maneuver failed: {e}")

    def show_off(self):
        logger.info("Performing show-off routine.")
        # Implement show-off routine
        raise NotImplementedError("The show_off method is not yet implemented.")

    def say_hello(self):
        logger.info("Saying hello.")
        # Implement logic to say hello
        raise NotImplementedError("The say_hello method is not yet implemented.")