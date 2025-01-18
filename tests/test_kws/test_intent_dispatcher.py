import pytest

from control import ControlInterface
from kws import IntentDispatcher

@pytest.fixture
def control_interface_mock(mocker):
    return mocker.Mock(spec=ControlInterface)

@pytest.fixture
def dispatcher(control_interface_mock):
    return IntentDispatcher(control_interface_mock)

INTENT_HANDLERS = {
  # 'intent_name':              ('handler_method',                    slots_dict,                        expected_args, expected_kwargs)
    'help':                     ('hexapod_help',                      {},                                (),            {}),
    'system_status':            ('system_status',                     {},                                (),            {}),
    'shut_down':                ('shut_down',                         {},                                (),            {}),
    'emergency_stop':           ('emergency_stop',                    {},                                (),            {}),
    'wake_up':                  ('wake_up',                           {},                                (),            {}),
    'sleep':                    ('sleep',                             {},                                (),            {}),
    'calibrate':                ('calibrate',                         {},                                (),            {}),
    'run_sequence':             ('run_sequence',                      {'sequence_name': 'test_sequence'},(),            {'sequence_name': 'test_sequence'}),
    'repeat':                   ('repeat_last_command',               {},                                (),            {}),
    'turn_lights':              ('turn_lights',                       {'switch_state': True},            (),            {'switch_state': True}),
    'change_color':             ('change_color',                      {'color': 'blue'},                 (),            {'color': 'blue'}),
    'set_brightness':           ('set_brightness',                    {'brightness_percentage': '50%'},  (),            {'brightness_percentage': 50}),
    'set_speed':                ('set_speed',                         {'speed_percentage': '70%'},       (),            {'speed_percentage': 70}),
    'set_accel':                ('set_accel',                         {'accel_percentage': '30%'},       (),            {'accel_percentage': 30}),
    'low_profile_mode':         ('set_low_profile_mode',              {},                                (),            {}),
    'upright_mode':             ('set_upright_mode',                  {},                                (),            {}),
    'idle_stance':              ('idle_stance',                       {},                                (),            {}),
    'move':                     ('move',                              {'direction': 'forward'},          (),            {'direction': 'forward'}),
    'stop':                     ('stop',                              {},                                (),            {}),
    'rotate':                   ('rotate',                            {'angle': 90},                     (),            {'angle': 90}),
    'follow':                   ('follow',                            {},                                (),            {}),
    'sound_source_analysis':    ('sound_source_analysis',             {},                                (),            {}),
    'direction_of_arrival':     ('direction_of_arrival',              {},                                (),            {}),
    'police':                   ('police',                            {},                                (),            {}),
    'rainbow':                  ('rainbow',                           {},                                (),            {}),
    'sit_up':                   ('sit_up',                            {},                                (),            {}),
    'dance':                    ('dance',                             {},                                (),            {}),
    'helix':                    ('helix',                             {},                                (),            {}),
    'show_off':                 ('show_off',                          {},                                (),            {}),
    'hello':                    ('say_hello',                         {},                                (),            {}),
}

class TestIntentDispatcher:
    def test_intent_dispatcher_init(self, dispatcher, control_interface_mock):
        """
        Test the initialization of IntentDispatcher.

        Ensures that the control_interface is assigned correctly and
        all intent handlers are properly set up.
        """
        assert dispatcher.control_interface is control_interface_mock
        assert set(dispatcher.intent_handlers.keys()) == set(INTENT_HANDLERS.keys())

        for handler in dispatcher.intent_handlers.values():
            assert callable(handler)

    @pytest.mark.parametrize(
        "intent, handler, slots, expected_args, expected_kwargs",
        [(intent, *params) for intent, params in INTENT_HANDLERS.items()]
    )
    def test_dispatch_intents(self, dispatcher, control_interface_mock, intent, handler, slots, expected_args, expected_kwargs):
        """
        Test that dispatching each intent calls the correct handler with expected arguments.
        """
        dispatcher.dispatch(intent, slots)
        getattr(control_interface_mock, handler).assert_called_once_with(*expected_args, **expected_kwargs)

    def test_dispatch_unknown_intent(self, dispatcher):
        """
        Test that dispatching an unknown intent raises NotImplementedError.
        """
        with pytest.raises(NotImplementedError):
            dispatcher.dispatch('unknown_intent', {})
