from gpiozero import Button
from signal import pause

button = Button(26)

def button_pressed():
    print("on")

def button_released():
    print("off")

button.when_pressed = button_pressed
button.when_released = button_released

pause()  # Keep the script running
