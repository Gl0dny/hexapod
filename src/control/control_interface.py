import logging
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lights import LightsInteractionHandler
from lights.lights import ColorRGB
from robot.hexapod import Hexapod
from control.control_tasks  import RunCalibrationTask, MonitorCalibrationStatusTask

logger = logging.getLogger(__name__)

class ControlInterface:
    def __init__(self):
        self.hexapod = Hexapod()
        self.lights_handler = LightsInteractionHandler(self.hexapod.leg_to_led)
        logger.info("ControlInterface initialized with Lights and Hexapod.")

    # def inject_hexapod(func):
    #     """
    #     Decorator to inject self.hexapod into the decorated function.
    #     """
    #     def wrapper(self, *args, **kwargs):
    #         return func(self, self.hexapod, *args, **kwargs)
    #     return wrapper

    # def inject_lights_handler(func):
    #     """
    #     Decorator to inject self.lights_handler into the decorated function.
    #     """
    #     def wrapper(self, *args, **kwargs):
    #         return func(self, self.lights_handler, *args, **kwargs)
    #     return wrapper

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

    # @inject_lights_handler
    # def turn_lights(self, lights_handler, switch_state):
    #     """
    #     Turns the lights on or off based on the switch state.
        
    #     Args:
    #         lights_handler (LightsInteractionHandler): The lights handler instance.
    #         switch_state (str): State to switch the lights to ('on' or 'off').
    #     """
    #     if switch_state == 'off':
    #         logger.info("Turning lights off")
    #         lights_handler.off()
    #     else:
    #         logger.info("Turning lights on")
    #         lights_handler.wakeup()

    # @inject_lights_handler
    # def change_color(self, lights_handler, color):
    #     """
    #     Changes the color of the lights.
        
    #     Args:
    #         lights_handler (LightsInteractionHandler): The lights handler instance.
    #         color (str): The color to change the lights to.
    #     """
    #     try:
    #         enum_color = ColorRGB[color.upper()]
    #         logger.info(f"Switching color of the lights to {color}")
    #         lights_handler.lights.set_color(enum_color)
    #     except KeyError:
    #         logger.error(f"Color '{color}' is not supported.")

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

    # def sleep(self):
    #     logger.info("Putting robot to sleep.")
    #     # Implement sleep logic

    # def set_low_profile_mode(self):
    #     logger.info("Setting robot to low profile mode.")
    #     # Implement logic to set low profile mode

    # def set_upright_mode(self):
    #     logger.info("Setting robot to upright mode.")
    #     # Implement logic to set upright mode

    # def helix(self):
    #     logger.info("Performing helix maneuver.")
    #     # Implement helix maneuver

    # # def change_mode(self, mode):
    # #     logger.info(f"Changing mode to: {mode}")
    # #     # Implement mode change logic here

    def calibrate(self):
        """
        Initiates the calibration process in a separate thread to avoid blocking other activities.
        """
        try:
            logger.info("Starting calibration.")
            calibration_task = RunCalibrationTask(self.hexapod)
            calibration_task.start()

            monitor_task = MonitorCalibrationStatusTask(self.hexapod, self.lights_handler)
            monitor_task.start()
        
        except Exception as e:
            logger.error(f"Calibration failed: {e}")
            self.lights_handler.lights.set_color(ColorRGB.RED)