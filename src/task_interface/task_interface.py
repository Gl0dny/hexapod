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
from robot import Hexapod, ButtonHandler, PredefinedPosition
import task_interface.tasks
from interface import NonBlockingConsoleInputHandler
from utils import rename_thread
from odas import ODASDoASSLProcessor

if TYPE_CHECKING:
    from typing import Callable, Any, Optional
    from task_interface.tasks import Task

logger = logging.getLogger("task_interface_logger")

class TaskInterface:
    """
    Interface for controlling the hexapod based on voice commands.
    """

    def __init__(self):
        """
        Initialize the TaskInterface object.
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
            'odas_logs_dir': Path(__file__).parent.parent.parent / "logs" / "odas" / "ssl",
            'odas_data_dir': Path(__file__).parent.parent.parent / "data" / "audio" / "odas"
        }
        
        self.odas_processor = ODASDoASSLProcessor(
            lights_handler=self.lights_handler,
            tracked_sources_port=9000,
            potential_sources_port=9001,
            debug_mode=True,
            gui_config=odas_gui_config,
            data_config=odas_data_config
        )
        
        self.task: Task = None
        self.voice_control_context_info = None
        self._last_command = None
        self._last_args = None
        self._last_kwargs = None
        # Event to pause external control (button, voice commands) during particular operations
        # like calibration, shutdown, or other maintenance tasks
        self.external_control_paused_event = threading.Event()
        self.button_handler = ButtonHandler(pin=26, external_control_paused_event=self.external_control_paused_event)
        self.task_complete_callback: Optional[Callable[[Task], None]] = None
        logger.debug("TaskInterface initialized successfully.")

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

    def stop_task(self) -> None:
        """
        Stop any running task and reset the task attribute.
        """
        if hasattr(self, 'task') and self.task:
            try:
                logger.debug(f"Stopping existing task {self.task}.")
                self.task.stop_task(timeout=5.0)
            except Exception as e:
                logger.exception(f"Error stopping task: {e}")
        else:
            logger.debug("No active task to stop.")

    def task(method: Callable[..., Any]) -> Callable[..., Any]:
        """
        Decorator to manage the lifecycle of a Task within a method.

        This decorator ensures that the decorated method properly initializes and starts a 
        `Task`. It verifies that the method sets the `self.task` attribute 
        and automatically starts the task after the method execution. If the `task` 
        attribute is not set, it logs an error and raises an `AttributeError`.

        Args:
            method (Callable): The method to be wrapped by the decorator.

        Returns:
            Callable: Wrapped method.
        """
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            logger.debug(f"Starting task for method {method.__name__}.")
            result = method(self, *args, **kwargs)

            if not hasattr(self, 'task') or self.task is None:
                logger.error(f"{method.__name__} must set 'self.task' attribute")
                raise AttributeError(f"{method.__name__} must set 'self.task' attribute")
            
            logger.debug(f"'{method.__name__}' successfully set task attribute: {self.task}")

            logger.debug(f"Starting task: {self.task}")
            self.task.start()

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

    def set_task_complete_callback(self, callback: Callable[[Task], None]) -> None:
        """
        Set the callback to be invoked upon the completion of a Task.

        Args:
            callback (Callable[[Task], None]): The callback function.
        """
        self.task_complete_callback = callback
        logger.debug("Task completion callback has been set.")

    def _notify_task_completion(self, task: Task) -> None:
        """
        Notify when a task is completed by invoking the callback.

        Args:
            task (Task): The task that has completed.
        """
        if self.task_complete_callback:
            self.task_complete_callback(task)
        # Ensure self.task is cleared if the completed task is the current one
        if self.task is task:
            self.task = None

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
            input_handler = NonBlockingConsoleInputHandler()
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
    
    def _shutdown_monitor(self, shutdown_timer: threading.Timer, input_handler: NonBlockingConsoleInputHandler) -> None:
        """
        Monitors for shutdown input and handles the shutdown process.
        
        Args:
            shutdown_timer (threading.Timer): Timer for automatic shutdown.
            input_handler (NonBlockingConsoleInputHandler): Handles user input in a thread-safe manner.
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
    @task
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
            self.task = task_interface.tasks.WakeUpTask(
                hexapod, 
                lights_handler, 
                callback=lambda: self._notify_task_completion(self.task)
            )
            logger.user_info("Robot activated")
            
        except Exception as e:
            logger.exception(f"Activating robot failed: {e}")

    @voice_command
    @task
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
            self.task = task_interface.tasks.SleepTask(
                hexapod, 
                lights_handler, 
                callback=lambda: self._notify_task_completion(self.task)
            )
            logger.user_info("Robot deactivated")
            
        except Exception as e:
            logger.exception(f"Deactivating robot failed: {e}")

    @voice_command
    @task
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
            self.task = task_interface.tasks.CompositeCalibrationTask(
                hexapod, 
                lights_handler, 
                self.external_control_paused_event, 
                callback=lambda: self._notify_task_completion(self.task)
            )
            logger.user_info("Calibration process started.")
        
        except Exception as e:
            logger.exception(f"Calibration failed: {e}")

    @voice_command
    @task
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
            self.task = task_interface.tasks.RunSequenceTask(
                hexapod, 
                lights_handler, 
                sequence_name, 
                callback=lambda: self._notify_task_completion(self.task)
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
        lights_handler.listen_wakeword()

    @voice_command
    @inject_lights_handler
    @inject_hexapod
    def set_speed(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, speed_percentage: float) -> None:
        """
        Set the speed of all servos.

        Args:
            hexapod (Hexapod): The hexapod instance.
            speed_percentage (float): The speed percentage to set.
        """
        logger.debug(f"Setting speed to {speed_percentage}%.")
        hexapod.set_all_servos_speed(speed_percentage)
        lights_handler.listen_wakeword()
   
    @voice_command 
    @inject_lights_handler
    @inject_hexapod
    def set_accel(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, accel_percentage: float) -> None:
        """
        Set the acceleration of all servos.

        Args:
            hexapod (Hexapod): The hexapod instance.
            accel_percentage (float): The acceleration percentage to set.
        """
        logger.debug(f"Setting acceleration to {accel_percentage}%.")
        hexapod.set_all_servos_accel(accel_percentage)
        lights_handler.listen_wakeword()

    @voice_command
    @task
    @inject_lights_handler
    @inject_hexapod
    def march_in_place(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, duration: Optional[float] = None) -> None:
        """
        Execute the marching in place task.

        Args:
            hexapod (Hexapod): The hexapod instance.
            lights_handler (LightsInteractionHandler): Handles lights activity.
            duration (Optional[float]): Duration of marching in place in seconds. If None, uses default duration.
        """
        try:
            self.task = task_interface.tasks.MarchInPlaceTask(
                hexapod, 
                lights_handler,
                duration=duration,
                callback=lambda: self._notify_task_completion(self.task)
            )
        except Exception as e:
            logger.exception(f"March in place task failed: {e}")

    @voice_command
    @task
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
            self.task = task_interface.tasks.IdleStanceTask(
                hexapod, 
                lights_handler, 
                callback=lambda: self._notify_task_completion(self.task)
            )
                
        except Exception as e:
            logger.exception(f"Setting idle stance failed: {e}")

    @voice_command
    @task
    @inject_lights_handler
    @inject_hexapod
    def move(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, direction: str, cycles: int = None, duration: float = None) -> None:
        """
        Initiate a move in the specified direction, for a number of cycles or duration if provided.

        Args:
            hexapod (Hexapod): The hexapod instance.
            lights_handler (LightsInteractionHandler): Handles lights activity.
            direction (str): The direction to move.
            cycles (int, optional): Number of gait cycles to execute.
            duration (float, optional): Duration to move in seconds.
        """
        try:
            self.task = task_interface.tasks.MoveTask(
                hexapod,
                lights_handler,
                direction,
                cycles=cycles,
                duration=duration,
                callback=lambda: self._notify_task_completion(self.task)
            )
        except Exception as e:
            logger.exception(f"Move task failed: {e}")

    @voice_command
    @task
    @inject_lights_handler
    @inject_hexapod
    def rotate(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, angle: float = None, turn_direction: str = None, cycles: int = None, duration: float = None) -> None:
        """
        Rotate the hexapod by a specified angle, direction, cycles, or duration.

        Args:
            hexapod (Hexapod): The hexapod instance.
            lights_handler (LightsInteractionHandler): Handles lights activity.
            angle (float, optional): The angle to rotate.
            turn_direction (str, optional): The direction to rotate.
            cycles (int, optional): Number of gait cycles to execute.
            duration (float, optional): Duration to rotate in seconds.
        """
        try:
            self.task = task_interface.tasks.RotateTask(
                hexapod,
                lights_handler,
                angle=angle,
                turn_direction=turn_direction,
                cycles=cycles,
                duration=duration,
                callback=lambda: self._notify_task_completion(self.task)
            )
        except Exception as e:
            logger.exception(f"Rotate task failed: {e}")

    @voice_command
    @task
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
            self.task = task_interface.tasks.FollowTask(
                hexapod,
                lights_handler,
                self.odas_processor,
                self.external_control_paused_event,
                callback=lambda: self._notify_task_completion(self.task)
            )
        except Exception as e:
            logger.exception(f"Follow task failed: {e}")

    @voice_command
    @task
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
            self.task = task_interface.tasks.SoundSourceLocalizationTask(
                hexapod=hexapod, 
                lights_handler=lights_handler,
                odas_processor=odas_processor,
                external_control_paused_event=self.external_control_paused_event,
                callback=lambda: self._notify_task_completion(self.task)
            )
            logger.user_info("Sound source localization started.")
        except Exception as e:
            logger.exception(f"Sound source localization task failed: {e}")

    @voice_command
    @task
    @inject_odas
    @inject_lights_handler
    @inject_hexapod
    def stream_odas_audio(self, hexapod: Hexapod, lights_handler: LightsInteractionHandler, odas_processor: ODASDoASSLProcessor, stream_type: str = "separated") -> None:
        """
        Initiate the ODAS audio streaming task. First runs sound source localization to ensure ODAS is properly initialized.

        Args:
            hexapod (Hexapod): The hexapod instance.
            lights_handler (LightsInteractionHandler): Handles lights activity.
            odas_processor (ODASDoASSLProcessor): The ODAS processor for sound source localization.
            stream_type (str): Type of audio stream to play (default: "separated").
        """
        try:
            self.task = task_interface.tasks.StreamODASAudioTask(
                hexapod=hexapod, 
                lights_handler=lights_handler,
                odas_processor=odas_processor,
                external_control_paused_event=self.external_control_paused_event,
                stream_type=stream_type,
                callback=lambda: self._notify_task_completion(self.task)
            )
        except Exception as e:
            logger.exception(f"ODAS audio streaming task failed: {e}")

    @voice_command
    @inject_lights_handler
    def police(self, lights_handler: LightsInteractionHandler) -> None:
        """
        Initiate the police pulsing animation.

        Args:
            lights_handler (LightsInteractionHandler): Handles lights activity.
        """
        try:
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
            lights_handler.rainbow()

        except Exception as e:
            logger.exception(f"Executing rainbow failed: {e}")

    @voice_command
    @task
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
            self.task = task_interface.tasks.SitUpTask(
                hexapod, 
                lights_handler, 
                callback=lambda: self._notify_task_completion(self.task)
            )
        except Exception as e:
            logger.exception(f"Sit-up task failed: {e}")

    @voice_command
    @task
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
            self.task = task_interface.tasks.DanceTask(
                hexapod, 
                lights_handler, 
                callback=lambda: self._notify_task_completion(self.task)
            )
        except Exception as e:
            logger.exception(f"Dance task failed: {e}")

    @voice_command
    @task
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
            self.task = task_interface.tasks.HelixTask(
                hexapod, 
                lights_handler, 
                callback=lambda: self._notify_task_completion(self.task)
            )
            
        except Exception as e:
            logger.exception(f"Helix maneuver failed: {e}")

    @voice_command
    @task
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
            self.task = task_interface.tasks.ShowOffTask(
                hexapod, 
                lights_handler, 
                callback=lambda: self._notify_task_completion(self.task)
            )
        except Exception as e:
            logger.exception(f"Show-off task failed: {e}")

    @voice_command
    @task
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
            self.task = task_interface.tasks.SayHelloTask(
                hexapod, 
                lights_handler, 
                callback=lambda: self._notify_task_completion(self.task)
            )
        except Exception as e:
            logger.exception(f"Say hello task failed: {e}")

    @voice_command
    @inject_lights_handler
    @inject_hexapod
    def stop(self, hexapod, lights_handler):
        """
        Stop all current activities: stop the current task, deactivate servos, and turn off lights.
        """
        try:
            # Stop any running task
            if self.task:
            # Deactivate servos
                if hexapod:
                    if hexapod.gait_generator.is_gait_running():
                        hexapod.gait_generator.stop()
                    self.task.stop_task()
                    hexapod.move_to_position(PredefinedPosition.ZERO)
                    hexapod.wait_until_motion_complete()
                    logger.info("Hexapod gait generator stopped.")
            else:
                lights_handler.listen_wakeword()
                logger.user_info("No active task to stop.")
        except Exception as e:
            logger.exception(f"Stop failed: {e}")
            
    def cleanup(self):
        """
        Clean up the task interface.
        """
        self.stop()
        # Clean up button handler
        if self.button_handler:
            self.button_handler.cleanup()
            logger.info("Button handler cleaned up.")
        # Turn off lights
        if self.lights_handler:
            self.lights_handler.off()
            logger.info("Lights turned off.")
        if self.hexapod:
            self.hexapod.deactivate_all_servos()
            logger.info("Hexapod servos deactivated.")
