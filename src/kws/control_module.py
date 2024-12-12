import logging

logger = logging.getLogger(__name__)

from gpiozero import LED
from apa102 import APA102

COLORS_RGB = dict(
    blue=(0, 0, 255),
    green=(0, 255, 0),
    orange=(255, 50, 0),
    pink=(255, 51, 183),
    purple=(128, 0, 128),
    red=(255, 0, 0),
    white=(255, 255, 255),
    yellow=(255, 215, 0),
    brown=(139, 69, 19),
    gray=(128, 128, 128),
    teal=(0, 128, 128),
    indigo=(75, 0, 130),
)

driver = APA102(num_led=12)
power = LED(5)
power.on()

led_color='indigo'

def set_color(color):
    for i in range(12):
        driver.set_pixel(i, color[0], color[1], color[2])
    driver.show()

class ControlModule:
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

    def turn_lights(self, switch_state):
        if switch_state == 'off':
            logger.info(f"Turning lights off")
            set_color((0, 0, 0))
        else:
            logger.info(f"Turning lights on")
            set_color(COLORS_RGB[led_color])

    def change_color(self, color):
        logger.info(f"Switching color of the lights to {color}")
        led_color = color
        set_color(COLORS_RGB[led_color])