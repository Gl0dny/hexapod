import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/')))
from lights.lights import Lights

@pytest.fixture
def lights_fixture(mocker):
    mock_apa102 = mocker.patch("lights.lights.APA102", autospec=True)
    mock_led = mocker.patch("lights.lights.LED", autospec=True)
    mock_apa102.return_value.num_led = Lights.DEFAULT_NUM_LED
    lights = Lights()
    return mock_apa102, mock_led, lights

def test_init_lights(lights_fixture):
    mock_apa102, mock_led, lights = lights_fixture
    mock_apa102.assert_called_with(num_led=12)
    mock_led.assert_called_with(5)
    mock_led.return_value.on.assert_called_once()
    assert lights.brightness == 50
    assert lights.driver.global_brightness == int(0b11111 * 50 / 100)

def test_set_brightness(lights_fixture):
    _, _, lights = lights_fixture
    lights.set_brightness(120)
    assert lights.brightness == 100
    assert lights.driver.global_brightness == 31
    lights.set_brightness(-10)
    assert lights.brightness == 0
    assert lights.driver.global_brightness == 0
    lights.set_brightness(50)
    assert lights.driver.global_brightness == int(0b11111 * 50 / 100)

def test_set_color_rgb(lights_fixture):
    _, _, lights = lights_fixture
    lights.set_color_rgb((10, 20, 30))
    for i in range(Lights.DEFAULT_NUM_LED):
        lights.driver.set_pixel.assert_any_call(i, 10, 20, 30)
    lights.driver.show.assert_called_once()

def test_set_color_valid(lights_fixture):
    _, _, lights = lights_fixture
    lights.set_color('red')
    for i in range(Lights.DEFAULT_NUM_LED):
        lights.driver.set_pixel.assert_any_call(i, 255, 0, 0)
    lights.driver.show.assert_called_once()

def test_set_color_invalid(lights_fixture):
    _, _, lights = lights_fixture
    with pytest.raises(ValueError):
        lights.set_color("magenta")

def test_set_color_invalid_input(lights_fixture):
    _, _, lights = lights_fixture
    with pytest.raises(ValueError):
        lights.set_color(123)
    
    with pytest.raises(ValueError):
        lights.set_color(None)
    
    with pytest.raises(ValueError):
        lights.set_color(['red'])
    
    with pytest.raises(ValueError):
        lights.set_color({'color': 'red'})

def test_set_color_rgb(lights_fixture):
    _, _, lights = lights_fixture
    lights.set_color_rgb((10, 20, 30))
    for i in range(Lights.DEFAULT_NUM_LED):
        lights.driver.set_pixel.assert_any_call(i, 10, 20, 30)
    lights.driver.show.assert_called_once()

def test_set_color_rgb_invalid(lights_fixture):
    _, _, lights = lights_fixture
    with pytest.raises(ValueError):
        lights.set_color_rgb((255, 255))
    
    with pytest.raises(ValueError):
        lights.set_color_rgb((255, '255', 255))
    
    with pytest.raises(ValueError):
        lights.set_color_rgb((256, 255, 255))
    
    with pytest.raises(ValueError):
        lights.set_color_rgb((-1, 255, 255))
    
    with pytest.raises(ValueError):
        lights.set_color_rgb([255, 255, 255])

def test_rotate(lights_fixture):
    _, _, lights = lights_fixture
    lights.rotate(3)
    lights.driver.rotate.assert_called_with(3)
    lights.driver.show.assert_called()

def test_get_wheel_color(lights_fixture):
    _, _, lights = lights_fixture
    assert lights.get_wheel_color(0) == (0, 255, 0)
    assert lights.get_wheel_color(85) == (255, 0, 0)
    assert lights.get_wheel_color(170) == (0, 0, 255)

def test_clear(lights_fixture):
    _, _, lights = lights_fixture
    lights.clear(led_indices=[1, 2])
    lights.driver.set_pixel.assert_any_call(1, 0, 0, 0)
    lights.driver.set_pixel.assert_any_call(2, 0, 0, 0)
    lights.driver.show.assert_called()