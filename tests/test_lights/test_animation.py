import pytest

from lights import ColorRGB
import lights.animations

@pytest.fixture
def mock_lights(mocker):
    mock = mocker.Mock()
    mock.num_led = 12
    mock.rotate_positions = 12
    return mock

@pytest.fixture
def setup_animation(mocker, mock_lights):
    mocker.patch.object(mock_lights, 'set_color')
    mocker.patch.object(mock_lights, 'rotate')
    mocker.patch.object(mock_lights, 'set_color_rgb')
    mocker.patch.object(mock_lights, 'get_wheel_color')
    mocker.patch.object(mock_lights, 'clear')
    return mock_lights

class TestAnimations:

    def test_alternate_rotate_animation_run(self, mocker, setup_animation):
        mock_lights = setup_animation
        animation = lights.animations.AlternateRotateAnimation(mock_lights)
        mocker.patch.object(animation.stop_event, 'wait', side_effect=[False]*animation.lights.num_led*2 + [True])
        animation.start()
        animation.stop_animation()
        assert mock_lights.set_color.call_count == mock_lights.num_led
        assert mock_lights.rotate.call_count == mock_lights.rotate_positions

    def test_wheel_fill_animation_run(self, mocker, setup_animation):
        mock_lights = setup_animation
        animation = lights.animations.WheelFillAnimation(mock_lights)
        mocker.patch.object(animation.stop_event, 'wait', side_effect=[False]*animation.lights.num_led + [True])
        animation.start()
        animation.stop_animation()
        assert mock_lights.get_wheel_color.call_count == mock_lights.num_led
        assert mock_lights.set_color_rgb.call_count == mock_lights.num_led

    def test_pulse_smoothly_animation_run(self, mocker, setup_animation):
        mock_lights = setup_animation
        animation = lights.animations.PulseSmoothlyAnimation(mock_lights)
        mocker.patch.object(animation.stop_event, 'wait', side_effect=[False, False, True])
        animation.start()
        animation.stop_animation()
        assert mock_lights.set_color_rgb.call_count == 2

    def test_pulse_animation_run(self, mocker, setup_animation):
        mock_lights = setup_animation
        animation = lights.animations.PulseAnimation(mock_lights)
        mocker.patch.object(animation.stop_event, 'wait', side_effect=[False, False, True])
        animation.start()
        animation.stop_animation()
        assert mock_lights.set_color.call_count == 2

    def test_wheel_animation_run(self, mocker, setup_animation):
        mock_lights = setup_animation
        animation = lights.animations.WheelAnimation(mock_lights)
        mocker.patch.object(animation.stop_event, 'wait', side_effect=[False]*animation.lights.num_led + [True])
        animation.start()
        animation.stop_animation()
        assert mock_lights.get_wheel_color.call_count == mock_lights.num_led
        assert mock_lights.clear.call_count == mock_lights.num_led
        assert mock_lights.set_color_rgb.call_count == mock_lights.num_led

    def test_opposite_rotate_animation_run(self, mocker, setup_animation):
        mock_lights = setup_animation
        animation = lights.animations.OppositeRotateAnimation(mock_lights)
        max_offset = mock_lights.num_led // 2
        rotations = (1 + (max_offset-1) + 1)*2
        loops_number=[False]*rotations + [True]
        mocker.patch.object(animation.stop_event, 'wait', side_effect = loops_number)
        animation.start()
        animation.stop_animation()
        assert mock_lights.set_color.call_count == (1 + 2*(max_offset-1) + 1)*2
        assert mock_lights.clear.call_count == rotations

    def test_alternate_rotate_animation_init(self, mock_lights):
        animation = lights.animations.AlternateRotateAnimation(mock_lights, color_even='red', color_odd='blue', delay=0.5, positions=10)
        assert animation.color_even == 'red'
        assert animation.color_odd == 'blue'
        assert animation.delay == 0.5
        assert animation.positions == 10

    def test_wheel_fill_animation_init(self, mock_lights):
        animation = lights.animations.WheelFillAnimation(mock_lights, use_rainbow=False, color=ColorRGB.GREEN, interval=0.3)
        assert not animation.use_rainbow
        assert animation.color == ColorRGB.GREEN
        assert animation.interval == 0.3

    def test_pulse_smoothly_animation_init(self, mock_lights):
        animation = lights.animations.PulseSmoothlyAnimation(mock_lights, base_color=ColorRGB.YELLOW, pulse_color=ColorRGB.PURPLE, pulse_speed=0.1)
        assert animation.base_color == ColorRGB.YELLOW
        assert animation.pulse_color == ColorRGB.PURPLE
        assert animation.pulse_speed == 0.1

    def test_pulse_animation_init(self, mock_lights):
        animation = lights.animations.PulseAnimation(mock_lights, base_color=ColorRGB.WHITE, pulse_color=ColorRGB.BLUE, pulse_speed=0.2)
        assert animation.base_color == ColorRGB.WHITE
        assert animation.pulse_color == ColorRGB.BLUE
        assert animation.pulse_speed == 0.2

    def test_wheel_animation_init(self, mock_lights):
        animation = lights.animations.WheelAnimation(mock_lights, use_rainbow=True, color=ColorRGB.ORANGE, interval=0.25)
        assert animation.use_rainbow
        assert animation.color == ColorRGB.ORANGE
        assert animation.interval == 0.25

    def test_opposite_rotate_animation_init(self, mock_lights):
        animation = lights.animations.OppositeRotateAnimation(mock_lights, interval=0.15, color='cyan')
        assert animation.interval == 0.15
        assert animation.color == 'cyan'