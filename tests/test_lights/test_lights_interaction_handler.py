import pytest

from lights import LightsInteractionHandler
import lights.animations
from lights import ColorRGB

@pytest.fixture
def mock_lights(mocker):
    mock = mocker.Mock()
    return mock

@pytest.fixture
def lights_interaction_handler(mocker, mock_lights):
    mock_leg_to_led = mocker.Mock()
    mocker.patch('lights.lights_interaction_handler.Lights', return_value=mock_lights)
    return LightsInteractionHandler(mock_leg_to_led)

@pytest.fixture
def mock_stop_animation(mocker, lights_interaction_handler):
    return mocker.patch.object(lights_interaction_handler, 'stop_animation', wraps=lights_interaction_handler.stop_animation)

@pytest.fixture
def mock_start_wheel_fill_animation(mocker):
    return mocker.patch.object(lights.animations.WheelFillAnimation, 'start')

@pytest.fixture
def mock_start_pulse_smoothly_animation(mocker):
    return mocker.patch.object(lights.animations.PulseSmoothlyAnimation, 'start')

@pytest.fixture
def mock_start_opposite_rotate_animation(mocker):
    return mocker.patch.object(lights.animations.OppositeRotateAnimation, 'start')

@pytest.fixture
def mock_start_pulse_animation(mocker):
    return mocker.patch.object(lights.animations.PulseAnimation, 'start')

@pytest.fixture
def mock_start_calibration_animation(mocker):
    return mocker.patch.object(lights.animations.CalibrationAnimation, 'start')

@pytest.fixture
def mock_start_alternate_rotate_animation(mocker):
    return mocker.patch.object(lights.animations.AlternateRotateAnimation, 'start')

class TestLightsInteractionHandler:
    def test_initialization(self, lights_interaction_handler, mock_lights):
        assert lights_interaction_handler.lights == mock_lights
        assert lights_interaction_handler.animation is None

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

    def test_off(self, lights_interaction_handler, mock_lights, mock_stop_animation):
        lights_interaction_handler.animation = lights.animations.PulseSmoothlyAnimation(lights_interaction_handler.lights)
        lights_interaction_handler.off()
        assert lights_interaction_handler.animation is None
        mock_lights.clear.assert_called_once()
        mock_stop_animation.assert_called_once()

    def test_rainbow(self, lights_interaction_handler, mock_stop_animation, mock_start_wheel_fill_animation):
        lights_interaction_handler.rainbow(use_rainbow=True, color=ColorRGB.BLUE, interval=0.3)
        assert isinstance(lights_interaction_handler.animation, lights.animations.WheelFillAnimation)
        mock_start_wheel_fill_animation.assert_called_once()
        mock_stop_animation.assert_called_once()

    def test_listen_wakeword(self, lights_interaction_handler, mock_stop_animation, mock_start_pulse_smoothly_animation):
        lights_interaction_handler.listen_wakeword()
        assert isinstance(lights_interaction_handler.animation, lights.animations.PulseSmoothlyAnimation)
        mock_start_pulse_smoothly_animation.assert_called_once()
        mock_stop_animation.assert_called_once()

    def test_listen_intent(self, lights_interaction_handler, mock_stop_animation, mock_start_alternate_rotate_animation):
        lights_interaction_handler.listen_intent()
        assert isinstance(lights_interaction_handler.animation, lights.animations.AlternateRotateAnimation)
        mock_start_alternate_rotate_animation.assert_called_once()
        mock_stop_animation.assert_called_once()

    def test_think(self, lights_interaction_handler, mock_stop_animation, mock_start_opposite_rotate_animation):
        lights_interaction_handler.think()
        assert isinstance(lights_interaction_handler.animation, lights.animations.OppositeRotateAnimation)
        mock_start_opposite_rotate_animation.assert_called_once()
        mock_stop_animation.assert_called_once()

    def test_police(self, lights_interaction_handler, mock_stop_animation, mock_start_pulse_animation):
        lights_interaction_handler.police(pulse_speed=0.2)
        assert isinstance(lights_interaction_handler.animation, lights.animations.PulseAnimation)
        mock_start_pulse_animation.assert_called_once()
        mock_stop_animation.assert_called_once()

    def test_shutdown(self, lights_interaction_handler, mock_stop_animation, mock_start_wheel_fill_animation):
        lights_interaction_handler.shutdown(interval=1.5)
        assert isinstance(lights_interaction_handler.animation, lights.animations.WheelFillAnimation)
        mock_start_wheel_fill_animation.assert_called_once()
        mock_stop_animation.assert_called_once()

    def test_update_calibration_leds_status(self, lights_interaction_handler, mock_stop_animation, mock_start_calibration_animation):
        calibration_status = {1: 'calibrated', 2: 'calibrating'}
        lights_interaction_handler.update_calibration_leds_status(calibration_status)
        assert isinstance(lights_interaction_handler.animation, lights.animations.CalibrationAnimation)
        mock_start_calibration_animation.assert_called_once()
        mock_stop_animation.assert_called_once()

    def test_speak(self, lights_interaction_handler):
        with pytest.raises(NotImplementedError):
            lights_interaction_handler.speak()