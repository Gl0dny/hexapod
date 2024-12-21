import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/')))
from lights.lights import Lights

def test_init_lights(mocker):
    mock_apa102 = mocker.patch("lights.lights.APA102", autospec=True)
    mock_led = mocker.patch("lights.lights.LED", autospec=True)
    lights = Lights(num_led=5, power_pin=8, brightness=60, initial_color='teal')
    mock_apa102.assert_called_with(num_led=5)
    mock_led.assert_called_with(8)
    mock_led.return_value.on.assert_called_once()
    assert lights.brightness == 60
    assert lights.driver.global_brightness == int(0b11111 * 60 / 100)

def test_set_brightness(mocker):
    mock_apa102 = mocker.patch("lights.lights.APA102", autospec=True)
    mock_led = mocker.patch("lights.lights.LED", autospec=True)
    lights = Lights()
    lights.set_brightness(120)
    assert lights.brightness == 100
    assert lights.driver.global_brightness == 31
    lights.set_brightness(-10)
    assert lights.brightness == 0
    assert lights.driver.global_brightness == 0
    lights.set_brightness(50)
    assert lights.driver.global_brightness == int(0b11111 * 50 / 100)

def test_set_color_rgb(mocker):
    mock_apa102 = mocker.patch("lights.lights.APA102", autospec=True)
    mock_led = mocker.patch("lights.lights.LED", autospec=True)
    lights = Lights()
    lights.set_color_rgb((10, 20, 30))
    for i in range(Lights.DEFAULT_NUM_LED):
        lights.driver.set_pixel.assert_any_call(i, 10, 20, 30)
    lights.driver.show.assert_called_once()

def test_set_color_valid(mocker):
    mock_led = mocker.patch("lights.lights.LED", autospec=True)
    mock_apa102 = mocker.patch("lights.lights.APA102", autospec=True)
    mock_apa102.return_value.num_led = Lights.DEFAULT_NUM_LED
    lights = Lights()
    lights.set_color('red')
    for i in range(Lights.DEFAULT_NUM_LED):
        lights.driver.set_pixel.assert_any_call(i, 255, 0, 0)
    lights.driver.show.assert_called_once()

def test_set_color_invalid(mocker):
    mock_apa102 = mocker.patch("lights.lights.APA102", autospec=True)
    mock_apa102.return_value.num_led = 12
    mock_led = mocker.patch("lights.lights.LED", autospec=True)
    lights = Lights()
    with pytest.raises(ValueError):
        lights.set_color("magenta")

def test_set_color_invalid_input(mocker):
    mock_apa102 = mocker.patch("lights.lights.APA102", autospec=True)
    mock_led = mocker.patch("lights.lights.LED", autospec=True)
    lights = Lights()
    
    # Test with non-string input
    with pytest.raises(ValueError):
        lights.set_color(123)  # Integer instead of string
    
    with pytest.raises(ValueError):
        lights.set_color(None)  # NoneType instead of string
    
    with pytest.raises(ValueError):
        lights.set_color(['red'])  # List instead of string
    
    with pytest.raises(ValueError):
        lights.set_color({'color': 'red'})  # Dict instead of string

def test_set_color_rgb(mocker):
    mock_apa102 = mocker.patch("lights.lights.APA102", autospec=True)
    mock_apa102.return_value.num_led = Lights.DEFAULT_NUM_LED
    mock_led = mocker.patch("lights.lights.LED", autospec=True)
    lights = Lights()
    lights.set_color_rgb((10, 20, 30))
    for i in range(Lights.DEFAULT_NUM_LED):
        lights.driver.set_pixel.assert_any_call(i, 10, 20, 30)
    lights.driver.show.assert_called_once()

def test_set_color_rgb_invalid(mocker):
    mock_apa102 = mocker.patch("lights.lights.APA102", autospec=True)
    mock_led = mocker.patch("lights.lights.LED", autospec=True)
    lights = Lights()
    
    # Test with a tuple of incorrect length
    with pytest.raises(ValueError):
        lights.set_color_rgb((255, 255))  # Only two values

    # Test with non-integer values
    with pytest.raises(ValueError):
        lights.set_color_rgb((255, '255', 255))  # String in tuple

    # Test with values out of range
    with pytest.raises(ValueError):
        lights.set_color_rgb((256, 255, 255))  # Value exceeds 255

    with pytest.raises(ValueError):
        lights.set_color_rgb((-1, 255, 255))  # Negative value

    # Test with non-tuple input
    with pytest.raises(ValueError):
        lights.set_color_rgb([255, 255, 255])  # List instead of tuple

def test_rotate(mocker):
    mocker.patch("lights.lights.APA102", autospec=True)
    mocker.patch("lights.lights.LED", autospec=True)
    lights = Lights()
    lights.rotate(3)
    lights.driver.rotate.assert_called_with(3)
    lights.driver.show.assert_called()

def test_get_wheel_color(mocker):
    mock_led = mocker.patch("lights.lights.LED", autospec=True)
    mock_apa102 = mocker.patch("lights.lights.APA102", autospec=True)
    mock_apa102.return_value.num_led = Lights.DEFAULT_NUM_LED
    lights = Lights()
    assert lights.get_wheel_color(0) == (0, 255, 0)
    assert lights.get_wheel_color(85) == (255, 0, 0)
    assert lights.get_wheel_color(170) == (0, 0, 255)

def test_clear(mocker):
    mock_apa102 = mocker.patch("lights.lights.APA102", autospec=True)
    mocker.patch("lights.lights.LED", autospec=True)
    mock_apa102.return_value.num_led = Lights.DEFAULT_NUM_LED
    lights = Lights()
    lights.clear(led_indices=[1, 2])
    lights.driver.set_pixel.assert_any_call(1, 0, 0, 0)
    lights.driver.set_pixel.assert_any_call(2, 0, 0, 0)
    lights.driver.show.assert_called()