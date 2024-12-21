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

def test_alternate_rotate_animation_run(mocker, mock_lights):
    mocker.patch.object(mock_lights, 'set_color')
    mocker.patch.object(mock_lights, 'rotate')
    animation = AlternateRotateAnimation(mock_lights)
    mocker.patch.object(animation.stop_event, 'wait', side_effect=[False]*animation.lights.num_led*2 + [True])  # returns False for each LED and then True once the animation should stop
    animation.start()
    animation.stop_animation()
    assert mock_lights.set_color.call_count == mock_lights.num_led
    assert mock_lights.rotate.call_count == mock_lights.rotate_positions

def test_wheel_fill_animation_run(mocker, mock_lights):
    mocker.patch.object(mock_lights, 'set_color_rgb')
    mocker.patch.object(mock_lights, 'get_wheel_color')
    animation = WheelFillAnimation(mock_lights)
    mocker.patch.object(animation.stop_event, 'wait', side_effect=[False]*animation.lights.num_led + [True]) # returns False for each LED and then True once the animation should stop
    animation.start()
    animation.stop_animation()
    mock_lights.set_color_rgb.assert_called()
    assert mock_lights.get_wheel_color.call_count == mock_lights.num_led
    assert mock_lights.set_color_rgb.call_count == mock_lights.num_led

def test_pulse_smoothly_animation_run(mocker, mock_lights):
    mocker.patch.object(mock_lights, 'set_color_rgb')
    animation = PulseSmoothlyAnimation(mock_lights)
    mocker.patch.object(animation.stop_event, 'wait', side_effect=[False, False, True])  # Allow two iterations
    animation.start()
    animation.stop_animation()
    assert mock_lights.set_color_rgb.call_count == 2  # Assert alternation between base and pulse colors

def test_pulse_animation_run(mocker, mock_lights):
    mocker.patch.object(mock_lights, 'set_color')
    animation = PulseAnimation(mock_lights)
    mocker.patch.object(animation.stop_event, 'wait', side_effect=[False, False, True]) # Allow two iterations
    animation.start()
    animation.stop_animation()
    assert mock_lights.set_color.call_count == 2  # Assert alternation between base and pulse colors

def test_wheel_animation_run(mocker, mock_lights):
    mocker.patch.object(mock_lights, 'get_wheel_color')
    mocker.patch.object(mock_lights, 'clear')
    mocker.patch.object(mock_lights, 'set_color_rgb')

    animation = WheelAnimation(mock_lights)
    mocker.patch.object(animation.stop_event, 'wait', side_effect=[False]*animation.lights.num_led + [True]) # returns False for each LED and then True once the animation should stop.
    animation.start()
    animation.stop_animation()
    assert mock_lights.get_wheel_color.call_count == mock_lights.num_led
    assert mock_lights.clear.call_count == mock_lights.num_led
    assert mock_lights.set_color_rgb.call_count == mock_lights.num_led


def test_opposite_rotate_animation_run(mocker, mock_lights):
    mocker.patch.object(mock_lights, 'set_color')
    mocker.patch.object(mock_lights, 'clear')
    animation = OppositeRotateAnimation(mock_lights)
    max_offset = mock_lights.num_led // 2
    rotations = (1 + (max_offset-1) + 1)*2
    loops_number=[False]*rotations + [True]
    mocker.patch.object(animation.stop_event, 'wait', side_effect = loops_number)
    animation.start()
    animation.stop_animation()
    assert mock_lights.set_color.call_count == (1 + 2*(max_offset-1) + 1)*2
    assert mock_lights.clear.call_count == rotations