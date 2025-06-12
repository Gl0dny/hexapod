from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import os
import time
import threading
from functools import wraps
from types import MethodType
from pathlib import Path

from lights import LightsInteractionHandler, ColorRGB
from robot import Hexapod
import control.tasks
from interface import InputHandler
from utils import rename_thread
from odas import ODASDoASSLProcessor
from utils import ButtonHandler

if TYPE_CHECKING:
    from typing import Callable, Any, Optional
    from control.tasks import ControlTask

logger = logging.getLogger("control_logger")

class ControlInterface:
    """
    Interface for controlling the hexapod based on voice commands.
    """

    def __init__(self):
        """
        Initialize the ControlInterface object.
        """
        self.hexapod = Hexapod()
        self.lights_handler = LightsInteractionHandler(self.hexapod.leg_to_led)
        
        # Configure ODAS processor
        odas_gui_config = {
            'gui_host': "192.168.0.102",
            'gui_tracked_sources_port': 9000,
            'gui_potential_sources_port': 9001,
            'forward_to_gui': True
        }
        
        odas_data_config = {
            'workspace_root': Path(__file__).parent.parent,
            'base_logs_dir': Path(__file__).parent.parent / "logs" / "odas" / "ssl",
            'odas_data_dir': Path(__file__).parent.parent / "data" / "audio" / "odas"
        }
        
        self.odas_processor = ODASDoASSLProcessor(
            lights_handler=self.lights_handler,
            tracked_sources_port=9000,
            potential_sources_port=9001,
            debug_mode=True,
            gui_config=odas_gui_config,
            data_config=odas_data_config
        )
        
        self.control_task: ControlTask = None
        self.voice_control_context_info = None
        self._last_command = None
        self._last_args = None
        self._last_kwargs = None
        # Event to pause external control (button, voice commands) during particular operations
        # like calibration, shutdown, or other maintenance tasks
        self.external_control_paused_event = threading.Event()
        self.button_handler = ButtonHandler(pin=26, external_control_paused_event=self.external_control_paused_event)
        self.task_complete_callback: Optional[Callable[[ControlTask], None]] = None
        logger.debug("ControlInterface initialized successfully.")

    def inject_hexapod(func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Decorator to inject the Hexapod instance into the decorated method.

        Args:
            func (Callable): The function to decorate.

        Returns:
            Callable: The decorated function with the hexapod injected.
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, self.hexapod, *args, **kwargs)
        return wrapper

    def inject_lights_handler(func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Decorator to inject the LightsInteractionHandler into the decorated method.

        Args:
            func (Callable): The function to decorate.

        Returns:
            Callable: The decorated function with the lights handler injected.
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, self.lights_handler, *args, **kwargs)
        return wrapper

    def inject_odas(func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Decorator to inject the ODASDoASSLProcessor into the decorated method.

        Args:
            func (Callable): The function to decorate.

        Returns:
            Callable: The decorated function with the ODAS processor injected.
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, self.odas_processor, *args, **kwargs)
        return wrapper

    def stop_control_task(self) -> None:
        """
        Stop any running control task and reset the control_task attribute.
        """
        if hasattr(self, 'control_task') and self.control_task:
            try:
                logger.debug(f"Stopping existing control_task {self.control_task}.")
                self.control_task.stop_task(timeout=5.0)
                self.control_task = None
            except Exception as e:
                logger.exception(f"Error stopping control task: {e}")
                self.control_task = None
        else:
            logger.debug("No active control_task to stop.")

    def control_task(method: Callable[..., Any]) -> Callable[..., Any]:
        """
        Decorator to manage the lifecycle of a ControlTask within a method.

        This decorator ensures that the decorated method properly initializes and starts a 
        `ControlTask`. It verifies that the method sets the `self.control_task` attribute 
        and automatically starts the task after the method execution. If the `control_task` 
        attribute is not set, it logs an error and raises an `AttributeError`.

        Args:
            method (Callable): The method to be wrapped by the decorator.

        Returns:
            Callable: Wrapped method.
        """
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            logger.debug(f"Starting control task for method {method.__name__}.")
            result = method(self, *args, **kwargs)

            if not hasattr(self, 'control_task') or self.control_task is None:
                logger.error(f"{method.__name__} must set 'self.control_task' attribute")
                raise AttributeError(f"{method.__name__} must set 'self.control_task' attribute")
            
            logger.debug(f"'{method.__name__}' successfully set control_task attribute: {self.control_task}")

            logger.debug(f"Starting control task: {self.control_task}")
            self.control_task.start()

            return result
        return wrapper

    def voice_command(func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Decorator to store the last voice command before executing the function.

        Args:
            func (Callable): The function to decorate.

        Returns:
            Callable: The decorated function with the voice command stored.
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            self._store_last_command(func, *args, **kwargs)
            return func(self, *args, **kwargs)
        return wrapper

    def set_task_complete_callback(self, callback: Callable[[ControlTask], None]) -> None:
        """
        Set the callback to be invoked upon the completion of a ControlTask.

        Args:
            callback (Callable[[ControlTask], None]): The callback function.
        """
        self.task_complete_callback = callback
        logger.debug("Task completion callback has been set.")

    def _notify_task_completion(self, task: ControlTask) -> None:
        """
        Notify when a task is completed by invoking the callback.

        Args:
            task (ControlTask): The task that has completed.
        """
        if self.task_complete_callback:
            self.task_complete_callback(task)

    @voice_command
    def hexapod_help(self) -> None:
        """
        Provide help information and set the lights to the ready state.
        """
        if getattr(self, 'voice_control_context_info', None):
            logger.user_info(f"Picovoice Context Info:\n {self.voice_control_context_info}")
        else:
            logger.warning("No context information available.")
        self.lights_handler.listen_wakeword()

    @voice_command
    def system_status(self) -> None:
        """
        Report the current system status.

        Raises:
            NotImplementedError: If the system_status method is not yet implemented.
        """
        # Implement system status reporting
        # Example: Return current status of all modules
        raise NotImplementedError("The system_status method is not yet implemented.")
    
    @voice_command
    @inject_lights_handler
    @inject_hexapod
    def shut_down(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler) -> None:
        """
        Initiate the shutdown sequence with a delay, allowing for cancellation.

        Args:
            hexapod (Hexapod): The hexapod instance.
            lights_handler (LightsInteractionHandler): Handles lights activity.
        """
        try:
            input_handler = InputHandler()
            rename_thread(input_handler, "ShutdownInputHandler")
            input_handler.start()

            self.external_control_paused_event.set()  # Signal external control paused

            shutdown_delay = 15.0  # seconds
            lights_handler.shutdown(interval=shutdown_delay / (lights_handler.lights.num_led * 1.1))
            logger.critical(f"Shutting down robot. System will power off in {shutdown_delay} seconds.\nPress any key+Enter to cancel.")
            
            shutdown_timer = threading.Timer(shutdown_delay, self._perform_shutdown, args=(hexapod, lights_handler))
            rename_thread(shutdown_timer, "ShutdownTimer")
            shutdown_timer.start()
            
            # Start a separate thread to monitor user input
            shutdown_monitor_thread = threading.Thread(
                target=self._shutdown_monitor,
                args=(shutdown_timer, input_handler),
                daemon=True
            )
            rename_thread(shutdown_monitor_thread, "ShutdownMonitor")
            shutdown_monitor_thread.start()
            
        except Exception as e:
            logger.exception("Exception occurred in shut_down: %s", e)
            raise
    
    def _shutdown_monitor(self, shutdown_timer: threading.Timer, input_handler: InputHandler) -> None:
        """
        Monitor the shutdown process to allow for cancellation based on user input.

        Args:
            shutdown_timer (threading.Timer): Timer for the scheduled shutdown.
            input_handler (InputHandler): Handles user input in a thread-safe manner.
        """
        try:
            while shutdown_timer.is_alive():
                user_input = input_handler.get_input()
                if user_input:
                    shutdown_timer.cancel()
                    self.external_control_paused_event.clear()
                    input_handler.shutdown()
                    input_handler = None
                    logger.user_info("Shutdown canceled by user.")
                    break
                time.sleep(0.1)
            else:
                logger.user_info("No input received. Proceeding with shutdown.")

        except Exception as e:
            logger.exception(f"Unexpected error occurred during shutdown monitoring: {e}")

        finally:
            pass

    def _perform_shutdown(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler) -> None:
        """
        Execute the system shutdown sequence.

        Args:
            hexapod (Hexapod): Hexapod instance to deactivate.
            lights_handler (LightsInteractionHandler): Handles lights activity.
        """
        logger.user_info("Shutting down the system now.")
        hexapod.deactivate_all_servos()
        lights_handler.off()
        os.system("sudo shutdown now")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def emergency_stop(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler) -> None:
        """
        Initiate an emergency stop to halt all activities.

        Args:
            hexapod (Hexapod): The hexapod instance.
            lights_handler (LightsInteractionHandler): Handles lights activity.
        """
        try:
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = control.tasks.EmergencyStopTask(
                hexapod, 
                lights_handler, 
                callback=lambda: self._notify_task_completion(self.control_task)
            )
        except Exception as e:
            logger.exception(f"Emergency stop failed: {e}")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def wake_up(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler) -> None:
        """
        Activate the robot from a sleep state.

        Args:
            hexapod (Hexapod): The hexapod instance.
            lights_handler (LightsInteractionHandler): Handles lights activity.
        """
        try:
            logger.user_info("Activating robot...")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = control.tasks.WakeUpTask(
                hexapod, 
                lights_handler, 
                callback=lambda: self._notify_task_completion(self.control_task)
            )
            logger.user_info("Robot activated")
            
        except Exception as e:
            logger.exception(f"Activating robot failed: {e}")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def sleep(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler) -> None:
        """
        Deactivate the robot and put it into a sleep state.

        Args:
            hexapod (Hexapod): The hexapod instance.
            lights_handler (LightsInteractionHandler): Handles lights activity.
        """
        try:
            logger.user_info("Deactivating robot...")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = control.tasks.SleepTask(
                hexapod, 
                lights_handler, 
                callback=lambda: self._notify_task_completion(self.control_task)
            )
            logger.user_info("Robot deactivated")
            
        except Exception as e:
            logger.exception(f"Deactivating robot failed: {e}")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def calibrate(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler) -> None:
        """
        Initiate the calibration process in a separate thread to avoid blocking other activities.

        Args:
            hexapod (Hexapod): The hexapod instance.
            lights_handler (LightsInteractionHandler): Handles lights activity.
        """
        try:
            self.external_control_paused_event.set()  # Signal external control paused
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = control.tasks.CompositeCalibrationTask(
                hexapod, 
                lights_handler, 
                self.external_control_paused_event, 
                callback=lambda: self._notify_task_completion(self.control_task)
            )
            logger.user_info("Calibration process started.")
        
        except Exception as e:
            logger.exception(f"Calibration failed: {e}")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def run_sequence(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, sequence_name: str) -> None:
        """
        Execute a predefined sequence of tasks.

        Args:
            hexapod (Hexapod): The hexapod object to control.
            lights_handler (LightsInteractionHandler): The lights handler instance.
            sequence_name (str): The name of the sequence to execute.
        """
        try:
            logger.info(f"Executing sequence: {sequence_name}")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = control.tasks.RunSequenceTask(
                hexapod, 
                lights_handler, 
                sequence_name, 
                callback=lambda: self._notify_task_completion(self.control_task)
            )
        except Exception as e:
            logger.exception(f"Run sequence '{sequence_name}' failed: {e}")

    def repeat_last_command(self) -> None:
        """
        Repeat the last executed command.
        """
        if self._last_command:
            logger.user_info(f"Repeating last command: {self._last_command.__name__}")
            self._last_command(*self._last_args, **self._last_kwargs)
        else:
            logger.error("No last command to repeat.")
            self.lights_handler.listen_wakeword(base_color=ColorRGB.RED, pulse_color=ColorRGB.GOLDEN)
        
    def _store_last_command(self, func: MethodType, *args: Any, **kwargs: Any) -> None:
        """
        Store the last executed command and its arguments.

        Args:
            func (MethodType): The function to store.
            *args (Any): Positional arguments for the function.
            **kwargs (Any): Keyword arguments for the function.
        """
        logger.debug(f"Storing last command: {func.__name__} with args={args}, kwargs={kwargs}.")
        if not isinstance(func, MethodType):
            func = MethodType(func, self)
        self._last_command = func
        self._last_args = args
        self._last_kwargs = kwargs

    @voice_command            
    @inject_lights_handler
    def turn_lights(self, lights_handler: LightsInteractionHandler, switch_state: str) -> None:
        """
        Turn the lights on or off based on the switch state.

        Args:
            lights_handler (LightsInteractionHandler): The lights handler instance.
            switch_state (str): State to switch the lights to ('on' or 'off').
        """
        if switch_state == 'off':
            logger.user_info("Turning lights off")
            lights_handler.off()
        else:
            logger.user_info("Turning lights on")
            self.lights_handler.listen_wakeword()

    @voice_command
    @inject_lights_handler
    def change_color(self, lights_handler: LightsInteractionHandler, color: str) -> None:
        """
        Change the color of the lights.

        Args:
            lights_handler (LightsInteractionHandler): The lights handler instance.
            color (str): The color to change the lights to.
        """
        try:
            enum_color = ColorRGB[color.upper()]
            logger.user_info(f"Switching color of the lights to {color}")
            lights_handler.set_single_color(enum_color)
        except KeyError:
            logger.exception(f"Color '{color}' is not supported.")

    @voice_command
    @inject_lights_handler
    def set_brightness(self, lights_handler: LightsInteractionHandler, brightness_percentage: float) -> None:
        """
        Set the brightness of the lights.

        Args:
            lights_handler (LightsInteractionHandler): The lights handler instance.
            brightness_percentage (float): The brightness percentage to set.
        """
        logger.debug(f"Setting brightness to {brightness_percentage}%.")
        lights_handler.set_brightness(brightness_percentage)

    @voice_command
    @inject_hexapod
    def set_speed(self, hexapod: Hexapod, speed_percentage: float) -> None:
        """
        Set the speed of all servos.

        Args:
            hexapod (Hexapod): The hexapod instance.
            speed_percentage (float): The speed percentage to set.
        """
        logger.debug(f"Setting speed to {speed_percentage}%.")
        hexapod.set_all_servos_speed(speed_percentage)
   
    @voice_command 
    @inject_hexapod
    def set_accel(self, hexapod: Hexapod, accel_percentage: float) -> None:
        """
        Set the acceleration of all servos.

        Args:
            hexapod (Hexapod): The hexapod instance.
            accel_percentage (float): The acceleration percentage to set.
        """
        logger.debug(f"Setting acceleration to {accel_percentage}%.")
        hexapod.set_all_servos_accel(accel_percentage)

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def set_low_profile_mode(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler) -> None:
        """
        Initiate low-profile mode in a separate thread.

        Args:
            hexapod (Hexapod): The hexapod instance.
            lights_handler (LightsInteractionHandler): Handles lights activity.
        """
        try:
            logger.user_info("Setting robot to low profile mode.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = control.tasks.LowProfileTask(
                hexapod, 
                lights_handler, 
                callback=lambda: self._notify_task_completion(self.control_task)
            )

        except Exception as e:
            logger.exception(f"Setting low profile mode failed: {e}")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def set_upright_mode(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler) -> None:
        """
        Initiate upright mode in a separate thread.

        Args:
            hexapod (Hexapod): The hexapod instance.
            lights_handler (LightsInteractionHandler): Handles lights activity.
        """
        try:
            logger.user_info("Setting robot to upright mode.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = control.tasks.UprightModeTask(
                hexapod, 
                lights_handler, 
                callback=lambda: self._notify_task_completion(self.control_task)
            )
            
        except Exception as e:
            logger.exception(f"Setting upright mode failed: {e}")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def idle_stance(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler) -> None:
        """
        Initiate the idle stance by setting the hexapod to the home position.

        Args:
            hexapod (Hexapod): The hexapod instance.
            lights_handler (LightsInteractionHandler): Handles lights activity.
        """
        try:
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = control.tasks.IdleStanceTask(
                hexapod, 
                lights_handler, 
                callback=lambda: self._notify_task_completion(self.control_task)
            )
                
        except Exception as e:
            logger.exception(f"Setting idle stance failed: {e}")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def move(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, direction: str) -> None:
        """
        Initiate a move in the specified direction.

        Args:
            hexapod (Hexapod): The hexapod instance.
            lights_handler (LightsInteractionHandler): Handles lights activity.
            direction (str): The direction to move.
        """
        try:
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = control.tasks.MoveTask(
                hexapod, 
                direction, 
                callback=lambda: self._notify_task_completion(self.control_task)
            )
        except Exception as e:
            logger.exception(f"Move task failed: {e}")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def stop(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler) -> None:
        """
        Stop all current activities.

        Args:
            hexapod (Hexapod): The hexapod instance.
            lights_handler (LightsInteractionHandler): Handles lights activity.
        """
        try:
            logger.user_info("Executing stop.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = control.tasks.StopTask(
                hexapod, 
                lights_handler, 
                callback=lambda: self._notify_task_completion(self.control_task)
            )
        except Exception as e:
            logger.exception(f"Stop task failed: {e}")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def rotate(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, angle: Optional[float] = None, direction: Optional[str] = None) -> None:
        """
        Rotate the hexapod by a specified angle or direction.

        Args:
            hexapod (Hexapod): The hexapod instance.
            lights_handler (LightsInteractionHandler): Handles lights activity.
            angle (Optional[float]): The angle to rotate.
            direction (Optional[str]): The direction to rotate.
        """
        try:
            logger.user_info("Initiating rotate.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = control.tasks.RotateTask(
                hexapod, 
                angle, 
                direction, 
                callback=lambda: self._notify_task_completion(self.control_task)
            )
            if angle:
                logger.user_info(f"Rotating {angle} degrees.")
            elif direction:
                logger.user_info(f"Rotating to the {direction}.")
        except Exception as e:
            logger.exception(f"Rotate task failed: {e}")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def follow(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler) -> None:
        """
        Initiate a follow task to follow a target.

        Args:
            hexapod (Hexapod): The hexapod instance.
            lights_handler (LightsInteractionHandler): Handles lights activity.
        """
        try:
            logger.user_info("Initiating follow.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = control.tasks.FollowTask(
                hexapod, 
                lights_handler, 
                callback=lambda: self._notify_task_completion(self.control_task)
            )
        except Exception as e:
            logger.exception(f"Follow task failed: {e}")

    @voice_command
    @control_task
    @inject_odas
    @inject_lights_handler
    @inject_hexapod
    def sound_source_localization(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, odas_processor: ODASDoASSLProcessor) -> None:
        """
        Initiate sound source localization.

        Args:
            hexapod (Hexapod): The hexapod instance.
            lights_handler (LightsInteractionHandler): Handles lights activity.
            odas_processor (ODASDoASSLProcessor): The ODAS processor for sound source localization.
        """
        try:
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = control.tasks.SoundSourceLocalizationTask(
                hexapod=hexapod, 
                lights_handler=lights_handler,
                odas_processor=odas_processor,
                external_control_paused_event=self.external_control_paused_event,
                callback=lambda: self._notify_task_completion(self.control_task)
            )
            logger.user_info("Sound source localization started.")
        except Exception as e:
            logger.exception(f"Sound source localization task failed: {e}")

    @voice_command
    @inject_lights_handler
    def police(self, lights_handler: LightsInteractionHandler) -> None:
        """
        Initiate the police pulsing animation.

        Args:
            lights_handler (LightsInteractionHandler): Handles lights activity.
        """
        try:
            logger.user_info("Turning on police lights...")
            lights_handler.police()
                
        except Exception as e:
            logger.exception(f"Turning on police lights failed: {e}")

    @voice_command
    @inject_lights_handler
    def rainbow(self, lights_handler: LightsInteractionHandler) -> None:
        """
        Initiate the rainbow animation.

        Args:
            lights_handler (LightsInteractionHandler): Handles lights activity.
        """
        try:
            logger.user_info("Executing rainbow command")
            lights_handler.rainbow()

        except Exception as e:
            logger.exception(f"Executing rainbow failed: {e}")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def sit_up(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler) -> None:
        """
        Initiate the sit-up routine.

        Args:
            hexapod (Hexapod): The hexapod instance.
            lights_handler (LightsInteractionHandler): Handles lights activity.
        """
        try:
            logger.user_info("Initiating sit-up routine.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = control.tasks.SitUpTask(
                hexapod, 
                lights_handler, 
                callback=lambda: self._notify_task_completion(self.control_task)
            )
        except Exception as e:
            logger.exception(f"Sit-up task failed: {e}")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def dance(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler) -> None:
        """
        Initiate the dance routine.

        Args:
            hexapod (Hexapod): The hexapod instance.
            lights_handler (LightsInteractionHandler): Handles lights activity.
        """
        try:
            logger.user_info("Initiating dance routine.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = control.tasks.DanceTask(
                hexapod, 
                lights_handler, 
                callback=lambda: self._notify_task_completion(self.control_task)
            )
        except Exception as e:
            logger.exception(f"Dance task failed: {e}")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def helix(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler) -> None:
        """
        Initiate the helix maneuver using HelixTask.

        Args:
            hexapod (Hexapod): The hexapod instance.
            lights_handler (LightsInteractionHandler): Handles lights activity.
        """
        try:
            if self.control_task:
                self.control_task.stop_task()

            self.control_task = control.tasks.HelixTask(
                hexapod, 
                lights_handler, 
                callback=lambda: self._notify_task_completion(self.control_task)
            )
            
        except Exception as e:
            logger.exception(f"Helix maneuver failed: {e}")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def show_off(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler) -> None:
        """
        Initiate the show-off routine.

        Args:
            hexapod (Hexapod): The hexapod instance.
            lights_handler (LightsInteractionHandler): Handles lights activity.
        """
        try:
            logger.user_info("Initiating show-off routine.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = control.tasks.ShowOffTask(
                hexapod, 
                lights_handler, 
                callback=lambda: self._notify_task_completion(self.control_task)
            )
        except Exception as e:
            logger.exception(f"Show-off task failed: {e}")

    @voice_command
    @control_task
    @inject_lights_handler
    @inject_hexapod
    def say_hello(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler) -> None:
        """
        Execute the say hello task.

        Args:
            hexapod (Hexapod): The hexapod instance.
            lights_handler (LightsInteractionHandler): Handles lights activity.
        """
        try:
            logger.user_info("Executing say hello.")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = control.tasks.SayHelloTask(
                hexapod, 
                lights_handler, 
                callback=lambda: self._notify_task_completion(self.control_task)
            )
        except Exception as e:
            logger.exception(f"Say hello task failed: {e}")