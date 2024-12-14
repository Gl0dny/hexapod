import pytest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/')))

from lights import Lights

@patch('lights.lights.LED')
@patch('lights.lights.APA102')
def test_lights_initialization(mock_APA102, mock_LED):
    mock_driver = mock_APA102.return_value
    mock_power = mock_LED.return_value

    lights = Lights(num_led=12, power_pin=5, brightness=50, initial_color='indigo')

    mock_APA102.assert_called_once_with(num_led=12)
    mock_LED.assert_called_once_with(5)
    mock_power.on.assert_called_once()

    assert lights.num_led == 12
    assert lights.brightness == 50
    assert lights.led_color == 'indigo'
    assert lights.driver == mock_driver
    assert lights.power == mock_power

def test_set_brightness_within_range():
    with patch('lights.lights.APA102') as mock_APA102:
        lights = Lights()
        mock_driver = mock_APA102.return_value

        lights.set_brightness(80)
        assert lights.brightness == 80
        expected_brightness = int(0b11111 * 80 / 100)
        assert mock_driver.global_brightness == expected_brightness

def test_set_brightness_above_max():
    with patch('lights.lights.APA102') as mock_APA102:
        lights = Lights()
        mock_driver = mock_APA102.return_value

        lights.set_brightness(150)
        assert lights.brightness == 100
        expected_brightness = int(0b11111 * 100 / 100)
        assert mock_driver.global_brightness == expected_brightness

def test_set_brightness_below_min():
    with patch('lights.lights.APA102') as mock_APA102:
        lights = Lights()
        mock_driver = mock_APA102.return_value

        lights.set_brightness(-10)
        assert lights.brightness == 0
        expected_brightness = int(0b11111 * 0 / 100)
        assert mock_driver.global_brightness == expected_brightness

@patch('lights.lights.APA102')
def test_set_color_valid(mock_APA102):
    mock_driver = mock_APA102.return_value
    lights = Lights()

    lights.set_color('red')
    rgb = lights.COLORS_RGB['red']

    calls = [((i, rgb[0], rgb[1], rgb[2]),) for i in range(lights.num_led)]
    mock_driver.set_pixel.assert_has_calls(calls, any_order=False)
    mock_driver.show.assert_called_once()

def test_set_color_invalid():
    lights = Lights()
    with pytest.raises(ValueError):
        lights.set_color('invalid_color')

@patch('lights.lights.APA102')
def test_set_color_with_index(mock_APA102):
    mock_driver = mock_APA102.return_value
    lights = Lights()

    lights.set_color('blue', led_index=5)
    rgb = lights.COLORS_RGB['blue']

    mock_driver.set_pixel.assert_called_once_with(5, rgb[0], rgb[1], rgb[2])
    mock_driver.show.assert_called_once()

@patch('lights.lights.APA102')
def test_rotate(mock_APA102):
    mock_driver = mock_APA102.return_value
    lights = Lights()

    lights.rotate(positions=2)
    mock_driver.rotate.assert_called_once_with(2)
    mock_driver.show.assert_called_once()

def test_get_wheel_color():
    lights = Lights()

    color = lights.get_wheel_color(0)
    assert color == (0, 255, 0)

    color = lights.get_wheel_color(85)
    assert color == (255, 0, 0)

    color = lights.get_wheel_color(170)
    assert color == (0, 0, 255)

@patch('lights.lights.APA102')
def test_clear_all(mock_APA102):
    mock_driver = mock_APA102.return_value
    lights = Lights()

    lights.clear()
    calls = [((i, 0, 0, 0),) for i in range(lights.num_led)]
    mock_driver.set_pixel.assert_has_calls(calls, any_order=False)
    mock_driver.show.assert_called_once()

@patch('lights.lights.APA102')
def test_clear_specific_indices(mock_APA102):
    mock_driver = mock_APA102.return_value
    lights = Lights()

    lights.clear(led_indices=[1, 3, 5])
    calls = [
        ((1, 0, 0, 0),),
        ((3, 0, 0, 0),),
        ((5, 0, 0, 0),)
    ]
    mock_driver.set_pixel.assert_has_calls(calls, any_order=True)
    mock_driver.show.assert_called_once()