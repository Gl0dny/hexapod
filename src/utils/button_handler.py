import RPi.GPIO as GPIO
import threading

class ButtonHandler:
    def __init__(self, pin=26):
        self.pin = pin
        self.is_running = True
        self.lock = threading.Lock()
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
    def get_state(self):
        return not GPIO.input(self.pin)  # Returns True when button is pressed
        
    def toggle_state(self):
        with self.lock:
            self.is_running = not self.is_running
            return self.is_running
            
    def cleanup(self):
        GPIO.cleanup(self.pin) 