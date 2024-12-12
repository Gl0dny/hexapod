import logging
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lights import Lights

logger = logging.getLogger(__name__)

class ControlModule:
    def __init__(self):
        self.lights = Lights()
        logger.info("ControlModule initialized with Lights.")

    def turn_lights(self, switch_state):
        if switch_state == 'off':
            logger.info(f"Turning lights off")
            self.lights.set_color((0, 0, 0))
        else:
            logger.info(f"Turning lights on")
            self.lights.set_color('indigo')

    def change_color(self, color):
        if color in self.lights.COLORS_RGB:
            logger.info(f"Switching color of the lights to {color}")
            self.lights.set_color(color)
        else:
            logger.error(f"Color '{color}' is not supported.")

    def move(self, direction):
        logger.info(f"Executing move: {direction}")
        # Implement movement logic here
        # Example: Send command to servo controller
        # Update state if using StateManager
        # self.state_manager.set_state(RobotState.MOVING)

    def turn(self, direction):
        logger.info(f"Executing turn: {direction}")
        # Implement turning logic here

    def stop(self):
        logger.info("Executing stop.")
        # Implement stop logic here

    def change_mode(self, mode):
        logger.info(f"Changing mode to: {mode}")
        # Implement mode change logic here