import logging
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lights import LightsInteractionHandler
from lights.lights import ColorRGB
from robot.hexapod import Hexapod

logger = logging.getLogger(__name__)

class ControlModule:
    def __init__(self):
        self.hexapod = Hexapod()
        self.lights_handler = LightsInteractionHandler()
        logger.info("ControlModule initialized with Lights and Hexapod.")

    def move(self, direction):
        logger.info(f"Executing move: {direction}")
        # Implement movement logic here
        # Example: Send command to servo controller
        # Update state if using StateManager
        # self.state_manager.set_state(RobotState.MOVING)

    def stop(self):
        logger.info("Executing stop.")
        # Implement stop logic here

    def idle_stance(self):
        logger.info("Setting robot to idle stance.")
        # Implement logic to set idle stance

    def rotate(self, angle=None, direction=None):
        if angle:
            logger.info(f"Rotating robot by {angle} degrees.")
            # Implement rotation logic based on angle
        elif direction:
            logger.info(f"Rotating robot to the {direction}.")
            # Implement rotation logic based on direction
        else:
            logger.error("No angle or direction provided for rotation.")

    def turn_lights(self, switch_state):
        if switch_state == 'off':
            logger.info(f"Turning lights off")
            self.lights_handler.off()
        else:
            logger.info(f"Turning lights on")
            self.lights_handler.wakeup()

    def change_color(self, color):
        try:
            enum_color = ColorRGB[color.upper()]
            logger.info(f"Switching color of the lights to {color}")
            self.lights_handler.lights.set_color(enum_color)
        except KeyError:
            logger.error(f"Color '{color}' is not supported.")

    def repeat_last_command(self):
        logger.info("Repeating last command.")
        # Implement logic to repeat the last command

    def say_hello(self):
        logger.info("Saying hello.")
        # Implement logic to say hello

    def show_off(self):
        logger.info("Performing show-off routine.")
        # Implement show-off routine

    def dance(self):
        logger.info("Performing dance routine.")
        # Implement dance routine

    def set_speed(self, speed_percentage):
        logger.info(f"Setting speed to {speed_percentage}%.")
        # Implement logic to set speed

    def set_acceleration(self, accel_percentage):
        logger.info(f"Setting acceleration to {accel_percentage}%.")
        # Implement logic to set acceleration

    def set_brightness(self, brightness_percentage):
        logger.info(f"Setting brightness to {brightness_percentage}%.")
        # Implement logic to set lights brightness

    def shut_down(self):
        logger.info("Shutting down robot.")
        # Implement shutdown logic

    def wake_up(self):
        logger.info("Waking up robot.")
        # Implement wake-up logic

    def sleep(self):
        logger.info("Putting robot to sleep.")
        # Implement sleep logic

    def set_low_profile_mode(self):
        logger.info("Setting robot to low profile mode.")
        # Implement logic to set low profile mode

    def set_upright_mode(self):
        logger.info("Setting robot to upright mode.")
        # Implement logic to set upright mode

    def helix(self):
        logger.info("Performing helix maneuver.")
        # Implement helix maneuver

    # def change_mode(self, mode):
    #     logger.info(f"Changing mode to: {mode}")
    #     # Implement mode change logic here

    def calibrate(self, hexapod):
        """
        Initiates and monitors the calibration process for the hexapod.
        Updates LED colors based on the current calibration status of each leg.
        
        Args:
            hexapod (Hexapod): The hexapod instance to calibrate.
        
        Returns:
            dict: A dictionary with leg indices as keys and their calibration status.
        """
        logger.info("Starting calibration.")
        
        # Set initial LED color to indicate calibration start
        self.lights_handler.lights.set_color(ColorRGB.YELLOW)
        
        # Start calibration in a separate thread if needed
        hexapod.calibrate_all_servos()
        
        # Retrieve current calibration calibration_status
        calibration_status = hexapod.calibration.get_calibration_status()
        
        # Determine LED color based on calibration calibration_status
        all_calibrated = all(status == "calibrated" for status in calibration_status.values())
        
        if all_calibrated:
            # All legs calibrated successfully
            self.lights_handler.lights.set_color(ColorRGB.GREEN)
            logger.info("Calibration completed successfully.")
        else:
            # Some legs are still calibrating or failed
            self.lights_handler.lights.set_color(ColorRGB.RED)
            logger.warning("Calibration incomplete or some legs failed.")
        
        return calibration_status