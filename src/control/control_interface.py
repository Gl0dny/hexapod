from typing import Callable, Any, Optional
import logging
import sys
import os
import time
import threading
from functools import wraps
from types import MethodType
from interface.input_handler import InputHandler

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
        self.input_handler = InputHandler()
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
            method(self, *args, **kwargs)
            if not hasattr(self, 'control_task') or self.control_task is None:
                raise AttributeError(
                    f"{method.__name__} must set 'self.control_task' attribute")
        return wrapper

    def voice_command(func):
        """
        Decorator to store the last voice command before executing the function.
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            self._store_last_command(func, *args, **kwargs)
            return func(self, *args, **kwargs)
        return wrapper

    @voice_command
    @inject_lights_handler
    def hexapod_help(self, lights_handler):
        logger.info("Executing help.")
        if self.voice_control_context_info:
            print(f"Picovoice Context Info: {self.voice_control_context_info}")
        else:
            print("No context information available.")
        lights_handler.ready()

    @voice_command
    def system_status(self):
        logger.info("Executing system_status.")
        # Implement system status reporting
        # Example: Return current status of all modules
        raise NotImplementedError("The system_status method is not yet implemented.")
    
    @voice_command
    @inject_lights_handler
    @inject_hexapod
    def shut_down(self, hexapod, lights_handler):
        shutdown_delay = 15.0  # seconds
        logger.info(f"Shutting down robot. System will power off in {shutdown_delay} seconds. Press any key+Enter to cancel.")
        lights_handler.shutdown(interval=shutdown_delay / (lights_handler.lights.num_led * 1.1))
        shutdown_timer = threading.Timer(shutdown_delay, self._perform_shutdown, args=(hexapod, lights_handler))
        shutdown_timer.start()
        
        # Start a separate thread to monitor user input
        shutdown_monitor_thread = threading.Thread(
            target=self._shutdown_monitor,
            args=(lights_handler, shutdown_timer),
            daemon=True
        )
        shutdown_monitor_thread.start()
    
    def _shutdown_monitor(self, lights_handler, shutdown_timer):
        try:
            while shutdown_timer.is_alive():
                user_input = self.input_handler.get_input()
                if user_input:
                    shutdown_timer.cancel()
                    logger.info("Shutdown canceled by user.")
                    lights_handler.ready()
                    break
                time.sleep(0.1)
            else:
                logger.info("No input received. Proceeding with shutdown.")

        except Exception as e:
            logger.error(f"Unexpected error occurred during shutdown monitoring: {e}")

        finally:
            logger.info("Shutdown sequence complete.")

    def _perform_shutdown(self, hexapod, lights_handler):
        logger.info("Shutting down the system now.")
        hexapod.deactivate_all_servos()
        lights_handler.off()
        os.system("sudo shutdown now")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def emergency_stop(self, hexapod, lights_handler) -> None:
        try:
            logger.info("Executing emergency stop.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = EmergencyStopTask(hexapod, lights_handler)
            # self.control_task.start()
            print("Emergency stop executed.")
        except Exception as e:
            logger.error(f"Emergency stop failed: {e}")

    @voice_command
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

    @voice_command
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

    @voice_command
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
    
    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def run_sequence(self, hexapod, lights_handler, sequence_name) -> None:
        """
        Executes a predefined sequence of tasks.

        Args:
            hexapod (Hexapod): The hexapod instance.
            lights_handler (LightsInteractionHandler): The lights handler instance.
            sequence_name (str): The name of the sequence to execute.
        """
        try:
            logger.info(f"Executing sequence: {sequence_name}")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = RunSequenceTask(hexapod, lights_handler, sequence_name)
            # self.control_task.start()
            print(f"Sequence '{sequence_name}' started.")
        except Exception as e:
            logger.error(f"Run sequence '{sequence_name}' failed: {e}")

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

    @voice_command            
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

    @voice_command
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

    @voice_command
    @inject_lights_handler
    def set_brightness(self, lights_handler, brightness_percentage):
        logger.info(f"Setting brightness to {brightness_percentage}%.")
        lights_handler.set_brightness(brightness_percentage)

    @voice_command
    @inject_hexapod
    def set_speed(self, hexapod, speed_percentage):
        logger.info(f"Setting speed to {speed_percentage}%.")
        hexapod.set_all_servos_speed(speed_percentage)
   
    @voice_command 
    @inject_hexapod
    def set_acceleration(self, hexapod, accel_percentage):
        logger.info(f"Setting acceleration to {accel_percentage}%.")
        hexapod.set_all_servos_accel(accel_percentage)

    @voice_command
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

    @voice_command
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

    @voice_command
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

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def move(self, hexapod, lights_handler, direction) -> None:
        try:
            logger.info(f"Initiating move in direction: {direction}.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = MoveTask(hexapod, direction)
            # self.control_task.start()
            print(f"Moving {direction}.")
        except Exception as e:
            logger.error(f"Move task failed: {e}")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def stop(self, hexapod, lights_handler) -> None:
        try:
            logger.info("Executing stop.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = StopTask(hexapod, lights_handler)
            # self.control_task.start()
            print("Stop executed.")
        except Exception as e:
            logger.error(f"Stop task failed: {e}")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def rotate(self, hexapod, lights_handler, angle=None, direction=None) -> None:
        try:
            logger.info("Initiating rotate.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = RotateTask(hexapod, angle, direction)
            # self.control_task.start()
            if angle:
                print(f"Rotating {angle} degrees.")
            elif direction:
                print(f"Rotating to the {direction}.")
        except Exception as e:
            logger.error(f"Rotate task failed: {e}")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def follow(self, hexapod, lights_handler) -> None:
        try:
            logger.info("Initiating follow.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = FollowTask(hexapod, lights_handler)
            # self.control_task.start()
            print("Follow task started.")
        except Exception as e:
            logger.error(f"Follow task failed: {e}")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def sound_source_analysis(self, hexapod, lights_handler) -> None:
        try:
            logger.info("Initiating sound source analysis.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = SoundSourceAnalysisTask(hexapod, lights_handler)
            # self.control_task.start()
            print("Sound source analysis started.")
        except Exception as e:
            logger.error(f"Sound source analysis task failed: {e}")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def direction_of_arrival(self, hexapod, lights_handler) -> None:
        try:
            logger.info("Calculating direction of arrival.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = DirectionOfArrivalTask(hexapod, lights_handler)
            # self.control_task.start()
            print("Direction of arrival calculation started.")
        except Exception as e:
            logger.error(f"Direction of arrival task failed: {e}")
            
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

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def sit_up(self, hexapod, lights_handler) -> None:
        try:
            logger.info("Initiating sit-up routine.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = SitUpTask(hexapod, lights_handler)
            # self.control_task.start()
            print("Sit-up routine started.")
        except Exception as e:
            logger.error(f"Sit-up task failed: {e}")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def dance(self, hexapod, lights_handler) -> None:
        try:
            logger.info("Initiating dance routine.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = DanceTask(hexapod, lights_handler)
            # self.control_task.start()
            print("Dance routine started.")
        except Exception as e:
            logger.error(f"Dance task failed: {e}")

    @voice_command
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

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def show_off(self, hexapod, lights_handler) -> None:
        try:
            logger.info("Initiating show-off routine.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = ShowOffTask(hexapod, lights_handler)
            # self.control_task.start()
            print("Show-off routine started.")
        except Exception as e:
            logger.error(f"Show-off task failed: {e}")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def say_hello(self, hexapod, lights_handler) -> None:
        try:
            logger.info("Executing say hello.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = SayHelloTask(hexapod, lights_handler)
            # self.control_task.start()
            print("Said hello.")
        except Exception as e:
            logger.error(f"Say hello task failed: {e}")