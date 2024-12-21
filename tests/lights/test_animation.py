import pytest
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/')))
from lights.animation import (
    AlternateRotateAnimation,
    WheelFillAnimation,
    PulseSmoothlyAnimation,
    PulseAnimation,
    WheelAnimation,
    OppositeRotateAnimation
)

@pytest.fixture
def mock_lights(mocker):
    mock = mocker.Mock()
    mock.num_led = 12
    mock.rotate_positions = 12
    mock.COLORS_RGB = {
        'indigo': (75, 0, 130),
        'golden': (255, 215, 0),
        'blue': (0, 0, 255),
        'green': (0, 255, 0),
        'red': (255, 0, 0),
        'white': (255, 255, 255)
    }
    return mock

@pytest.fixture
def setup_animation(mocker, mock_lights):
    mocker.patch.object(mock_lights, 'set_color')
    mocker.patch.object(mock_lights, 'rotate')
    mocker.patch.object(mock_lights, 'set_color_rgb')
    mocker.patch.object(mock_lights, 'get_wheel_color')
    mocker.patch.object(mock_lights, 'clear')
    return mock_lights

def test_alternate_rotate_animation_run(mocker, setup_animation):
    mock_lights = setup_animation
    animation = AlternateRotateAnimation(mock_lights)
    mocker.patch.object(animation.stop_event, 'wait', side_effect=[False]*animation.lights.num_led*2 + [True])  # returns False for each LED and then True once the animation should stop
    animation.start()
    animation.stop_animation()
    assert mock_lights.set_color.call_count == mock_lights.num_led
    assert mock_lights.rotate.call_count == mock_lights.rotate_positions

def test_wheel_fill_animation_run(mocker, setup_animation):
    mock_lights = setup_animation
    animation = WheelFillAnimation(mock_lights)
    mocker.patch.object(animation.stop_event, 'wait', side_effect=[False]*animation.lights.num_led + [True]) # returns False for each LED and then True once the animation should stop
    animation.start()
    animation.stop_animation()
    assert mock_lights.get_wheel_color.call_count == mock_lights.num_led
    assert mock_lights.set_color_rgb.call_count == mock_lights.num_led

def test_pulse_smoothly_animation_run(mocker, setup_animation):
    mock_lights = setup_animation
    animation = PulseSmoothlyAnimation(mock_lights)
    mocker.patch.object(animation.stop_event, 'wait', side_effect=[False, False, True])  # Allow two iterations
    animation.start()
    animation.stop_animation()
    assert mock_lights.set_color_rgb.call_count == 2  # Assert alternation between base and pulse colors

def test_pulse_animation_run(mocker, setup_animation):
    mock_lights = setup_animation
    animation = PulseAnimation(mock_lights)
    mocker.patch.object(animation.stop_event, 'wait', side_effect=[False, False, True]) # Allow two iterations
    animation.start()
    animation.stop_animation()
    assert mock_lights.set_color.call_count == 2  # Assert alternation between base and pulse colors

def test_wheel_animation_run(mocker, setup_animation):
    mock_lights = setup_animation
    animation = WheelAnimation(mock_lights)
    mocker.patch.object(animation.stop_event, 'wait', side_effect=[False]*animation.lights.num_led + [True]) # returns False for each LED and then True once the animation should stop.
    animation.start()
    animation.stop_animation()
    assert mock_lights.get_wheel_color.call_count == mock_lights.num_led
    assert mock_lights.clear.call_count == mock_lights.num_led
    assert mock_lights.set_color_rgb.call_count == mock_lights.num_led

def test_opposite_rotate_animation_run(mocker, setup_animation):
    mock_lights = setup_animation
    animation = OppositeRotateAnimation(mock_lights)
    max_offset = mock_lights.num_led // 2
    rotations = (1 + (max_offset-1) + 1)*2
    loops_number=[False]*rotations + [True]
    mocker.patch.object(animation.stop_event, 'wait', side_effect = loops_number)
    animation.start()
    animation.stop_animation()
    assert mock_lights.set_color.call_count == (1 + 2*(max_offset-1) + 1)*2
    assert mock_lights.clear.call_count == rotations

def test_alternate_rotate_animation_init(mock_lights):
    animation = AlternateRotateAnimation(mock_lights, color_even='red', color_odd='blue', delay=0.5, positions=10)
    assert animation.color_even == 'red'
    assert animation.color_odd == 'blue'
    assert animation.delay == 0.5
    assert animation.positions == 10

def test_wheel_fill_animation_init(mock_lights):
    animation = WheelFillAnimation(mock_lights, use_rainbow=False, color='green', interval=0.3)
    assert not animation.use_rainbow
    assert animation.color == 'green'
    assert animation.interval == 0.3

def test_pulse_smoothly_animation_init(mock_lights):
    animation = PulseSmoothlyAnimation(mock_lights, base_color='yellow', pulse_color='purple', pulse_speed=0.1)
    assert animation.base_color == 'yellow'
    assert animation.pulse_color == 'purple'
    assert animation.pulse_speed == 0.1

def test_pulse_animation_init(mock_lights):
    animation = PulseAnimation(mock_lights, base_color='white', pulse_color='black', pulse_speed=0.2)
    assert animation.base_color == 'white'
    assert animation.pulse_color == 'black'
    assert animation.pulse_speed == 0.2

def test_wheel_animation_init(mock_lights):
    animation = WheelAnimation(mock_lights, use_rainbow=True, color='orange', interval=0.25)
    assert animation.use_rainbow
    assert animation.color == 'orange'
    assert animation.interval == 0.25

def test_opposite_rotate_animation_init(mock_lights):
    animation = OppositeRotateAnimation(mock_lights, interval=0.15, color='cyan')
    assert animation.interval == 0.15
    assert animation.color == 'cyan'