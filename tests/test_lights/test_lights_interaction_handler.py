import pytest

from lights import LightsInteractionHandler
from lights.animation import *

@pytest.fixture
def mock_lights(mocker):
    mock = mocker.Mock()
    return mock

@pytest.fixture
def lights_interaction_handler(mocker, mock_lights):
    mocker.patch('lights.lights_interaction_handler.Lights', return_value=mock_lights)
    return LightsInteractionHandler()

@pytest.fixture
def mock_stop_animation(mocker, lights_interaction_handler):
    return mocker.patch.object(lights_interaction_handler, 'stop_animation', wraps=lights_interaction_handler.stop_animation)

@pytest.fixture
def mock_start_wheel_fill_animation(mocker):
    return mocker.patch.object(WheelFillAnimation, 'start')

@pytest.fixture
def mock_start_pulse_smoothly_animation(mocker):
    return mocker.patch.object(PulseSmoothlyAnimation, 'start')

@pytest.fixture
def mock_start_opposite_rotate_animation(mocker):
    return mocker.patch.object(OppositeRotateAnimation, 'start')

class TestLightsInteractionHandler:
    def test_initialization(self, lights_interaction_handler, mock_lights):
        assert lights_interaction_handler.lights == mock_lights
        assert lights_interaction_handler.animation is None

    def test_off(self, lights_interaction_handler, mock_lights, mock_stop_animation):
        lights_interaction_handler.animation = PulseSmoothlyAnimation(lights_interaction_handler.lights)
        lights_interaction_handler.off()
        assert lights_interaction_handler.animation is None
        mock_lights.clear.assert_called_once()
        mock_stop_animation.assert_called_once()

    def test_wakeup(self, lights_interaction_handler, mock_stop_animation, mock_start_wheel_fill_animation):
        lights_interaction_handler.wakeup()
        assert isinstance(lights_interaction_handler.animation, WheelFillAnimation)
        mock_start_wheel_fill_animation.assert_called_once()
        mock_stop_animation.assert_called_once()

    def test_listen(self, lights_interaction_handler, mock_stop_animation, mock_start_pulse_smoothly_animation):
        lights_interaction_handler.listen()
        assert isinstance(lights_interaction_handler.animation, PulseSmoothlyAnimation)
        mock_start_pulse_smoothly_animation.assert_called_once()
        mock_stop_animation.assert_called_once()

    def test_think(self, lights_interaction_handler, mock_stop_animation, mock_start_opposite_rotate_animation):
        lights_interaction_handler.think()
        assert isinstance(lights_interaction_handler.animation, OppositeRotateAnimation)
        mock_start_opposite_rotate_animation.assert_called_once()
        mock_stop_animation.assert_called_once()

    def test_speak(self, lights_interaction_handler):
        with pytest.raises(NotImplementedError):
            lights_interaction_handler.speak()

    def test_stop_animation(self, lights_interaction_handler, mocker):
        mock_animation = mocker.Mock()
        lights_interaction_handler.animation = mock_animation
        lights_interaction_handler.stop_animation()
        mock_animation.stop_animation.assert_called_once()
        assert lights_interaction_handler.animation is None

    def test_animation_decorator_sets_animation(self, lights_interaction_handler, mocker):
        mock_animation = mocker.Mock()
        mocker.patch.object(lights_interaction_handler, 'stop_animation')
        
        @LightsInteractionHandler.animation
        def dummy_method(self):
            self.animation = mock_animation
        
        dummy_method(lights_interaction_handler)
        assert lights_interaction_handler.animation == mock_animation

    def test_animation_decorator_raises_error_if_animation_not_set(self, lights_interaction_handler):
        @LightsInteractionHandler.animation
        def dummy_method(self):
            pass
        
        with pytest.raises(AttributeError, match="dummy_method must set 'self.animation' attribute"):
            dummy_method(lights_interaction_handler)
