from gpiozero import LED
from .apa102 import APA102

class Lights:
    COLORS_RGB = {
    'blue': (0, 0, 255),
    'green': (0, 255, 0),
    'orange': (255, 50, 0),
    'pink': (255, 51, 183),
    'purple': (128, 0, 128),
    'red': (255, 0, 0),
    'white': (255, 255, 255),
    'yellow': (255, 215, 0),
    'brown': (139, 69, 19),
    'gray': (128, 128, 128),
    'teal': (0, 128, 128),
    'indigo': (75, 0, 130),
    }
    
    def __init__(self, num_led=12, power_pin=5, initial_color='indigo'):
        self.driver = APA102(num_led=num_led)
        self.power = LED(power_pin)
        self.power.on()
        self.led_color = initial_color

    def set_color(self, color, num_led=None):
        if num_led is None:
            num_led = self.driver.num_led
        rgb = self.COLORS_RGB.get(color.lower(), (0, 0, 0))
        for i in range(num_led):
            self.driver.set_pixel(i, rgb[0], rgb[1], rgb[2])
        self.driver.show()