from typing import Callable, Any
import logging
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lights import LightsInteractionHandler
from lights.lights import ColorRGB
from robot.hexapod import Hexapod
from control.control_tasks import *

logger = logging.getLogger(__name__)

class ControlInterface:
    def __init__(self):
        self.hexapod = Hexapod()
        self.lights_handler = LightsInteractionHandler(self.hexapod.leg_to_led)
        self.control_task: ControlTask = None
        logger.info("ControlInterface initialized with Lights and Hexapod.")

    def inject_hexapod(func):
        """
        Decorator to inject self.hexapod into the decorated function.
        """
        def wrapper(self, *args, **kwargs):
            return func(self, self.hexapod, *args, **kwargs)
        return wrapper

    def inject_lights_handler(func):
        """
        Decorator to inject self.lights_handler into the decorated function.
        """
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
        def wrapper(self, *args, **kwargs):
            method(self, *args, **kwargs)
            if not hasattr(self, 'control_task') or self.control_task is None:
                raise AttributeError(
                    f"{method.__name__} must set 'self.control_task' attribute")
        return wrapper

    # def move(self, direction):
    #     logger.info(f"Executing move: {direction}")
    #     # Implement movement logic here
    #     # Example: Send command to servo controller
    #     # Update state if using StateManager
    #     # self.state_manager.set_state(RobotState.MOVING)

    # def stop(self):
    #     logger.info("Executing stop.")
    #     # Implement stop logic here

    # def idle_stance(self):
    #     logger.info("Setting robot to idle stance.")
    #     # Implement logic to set idle stance

    # def rotate(self, angle=None, direction=None):
    #     if angle:
    #         logger.info(f"Rotating robot by {angle} degrees.")
    #         # Implement rotation logic based on angle
    #     elif direction:
    #         logger.info(f"Rotating robot to the {direction}.")
    #         # Implement rotation logic based on direction
    #     else:
    #         logger.error("No angle or direction provided for rotation.")

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

    # def repeat_last_command(self):
    #     logger.info("Repeating last command.")
    #     # Implement logic to repeat the last command

    # def say_hello(self):
    #     logger.info("Saying hello.")
    #     # Implement logic to say hello

    # def show_off(self):
    #     logger.info("Performing show-off routine.")
    #     # Implement show-off routine

    # def dance(self):
    #     logger.info("Performing dance routine.")
    #     # Implement dance routine

    # def set_speed(self, speed_percentage):
    #     logger.info(f"Setting speed to {speed_percentage}%.")
    #     # Implement logic to set speed

    # def set_acceleration(self, accel_percentage):
    #     logger.info(f"Setting acceleration to {accel_percentage}%.")
    #     # Implement logic to set acceleration

    # @inject_lights_handler
    # def set_brightness(self, lights_handler, brightness_percentage):
    #     """
    #     Sets the brightness of the lights.
        
    #     Args:
    #         lights_handler (LightsInteractionHandler): The lights handler instance.
    #         brightness_percentage (int or str): Brightness level (0-100 or '0%-100%').
    #     """
    #     try:
    #         if isinstance(brightness_percentage, str) and brightness_percentage.endswith('%'):
    #             brightness_value = int(brightness_percentage.rstrip('%'))
    #         else:
    #             brightness_value = int(brightness_percentage)
            
    #         if not 0 <= brightness_value <= 100:
    #             raise ValueError("Brightness percentage must be between 0 and 100.")
            
    #         logger.info(f"Setting brightness to {brightness_value}%.")
    #         lights_handler.lights.set_brightness(brightness_value)
    #     except ValueError as e:
    #         logger.error(f"Invalid brightness_percentage value: {brightness_percentage}. Error: {e}")
    #         print(f"Error: {e}")

    # def shut_down(self):
    #     logger.info("Shutting down robot.")
    #     # Implement shutdown logic

    # def wake_up(self):
    #     logger.info("Waking up robot.")
    #     # Implement wake-up logic

    @control_task
    @inject_lights_handler
    @inject_hexapod
    def sleep(self, hexapod, lights_handler) -> None:
        try:
            logger.info("Deactivating robot...")
            if self.control_task:
                self.control_task.stop_task()
            self.control_task = SleepTask(hexapod, lights_handler)
            print("Robot deactivated")
            
        except Exception as e:
            logger.error(f"Deactivating robot failed: {e}")

    # def set_low_profile_mode(self):
    #     logger.info("Setting robot to low profile mode.")
    #     # Implement logic to set low profile mode

    # def set_upright_mode(self):
    #     logger.info("Setting robot to upright mode.")
    #     # Implement logic to set upright mode

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