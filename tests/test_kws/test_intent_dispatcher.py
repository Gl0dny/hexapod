"""
Module: test_intent_dispatcher

This module contains unit tests for the IntentDispatcher class.

It verifies that intents are correctly dispatched to their respective handlers,
and that appropriate exceptions are raised when invalid intents or slots are provided.
"""

import logging

import pytest

from control import ControlInterface
from kws.intent_dispatcher import IntentDispatcher

@pytest.fixture
def control_interface_mock(mocker):
    """
    Fixture to create a mock of the ControlInterface.

    Args:
        mocker: The pytest-mock mocker fixture.

    Returns:
        Mocked ControlInterface instance.
    """
    return mocker.Mock(spec=ControlInterface)

@pytest.fixture
def dispatcher(control_interface_mock):
    """
    Fixture to create an instance of IntentDispatcher with a mocked ControlInterface.

    Args:
        control_interface_mock (Mock): The mocked ControlInterface.

    Returns:
        IntentDispatcher instance.
    """
    return IntentDispatcher(control_interface_mock)

# INTENT_HANDLERS mapping intents to their corresponding test parameters.
# Structure:
# 'intent_name': ('handler_method', slots_dict, expected_args, expected_kwargs)
INTENT_HANDLERS = {
  # 'intent_name':              ('handler_method',                    slots_dict,                        expected_args,            expected_kwargs)
    'help':                     ('hexapod_help',                      {},                                (),                      {}),
    'system_status':            ('system_status',                     {},                                (),                      {}),
    'shut_down':                ('shut_down',                         {},                                (),                      {}),
    'emergency_stop':           ('emergency_stop',                    {},                                (),                      {}),
    'wake_up':                  ('wake_up',                           {},                                (),                      {}),
    'sleep':                    ('sleep',                             {},                                (),                      {}),
    'calibrate':                ('calibrate',                         {},                                (),                      {}),
    'run_sequence':             ('run_sequence',                      {'sequence_name': 'test_sequence'},(),                      {'sequence_name': 'test_sequence'}),
    'repeat':                   ('repeat_last_command',               {},                                (),                      {}),
    'turn_lights':              ('turn_lights',                       {'switch_state': True},            (True,),                 {}),
    'change_color':             ('change_color',                      {'color': 'blue'},                 (),                      {'color': 'blue'}),
    'set_brightness':           ('set_brightness',                    {'brightness_percentage': '50%'},  (50,),                   {}),
    'set_speed':                ('set_speed',                         {'speed_percentage': '70%'},       (70,),                   {}),
    'set_accel':                ('set_accel',                         {'accel_percentage': '30%'},       (30,),                   {}),
    'low_profile_mode':         ('set_low_profile_mode',              {},                                (),                      {}),
    'upright_mode':             ('set_upright_mode',                  {},                                (),                      {}),
    'idle_stance':              ('idle_stance',                       {},                                (),                      {}),
    'move':                     ('move',                              {'direction': 'forward'},          (),                      {'direction': 'forward'}),
    'stop':                     ('stop',                              {},                                (),                      {}),
    'rotate':                   ('rotate',                            {},                                (),                      {}),
    'follow':                   ('follow',                            {},                                (),                      {}),
    'sound_source_analysis':    ('sound_source_analysis',             {},                                (),                      {}),
    'direction_of_arrival':     ('direction_of_arrival',              {},                                (),                      {}),
    'police':                   ('police',                            {},                                (),                      {}),
    'rainbow':                  ('rainbow',                           {},                                (),                      {}),
    'sit_up':                   ('sit_up',                            {},                                (),                      {}),
    'dance':                    ('dance',                             {},                                (),                      {}),
    'helix':                    ('helix',                             {},                                (),                      {}),
    'show_off':                 ('show_off',                          {},                                (),                      {}),
    'hello':                    ('say_hello',                         {},                                (),                      {}),
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

    @pytest.mark.parametrize(
        "intent, slots, expected_exception",
        [
            ('unknown_intent', {}, NotImplementedError),
        ]
    )
    def test_dispatch_intent_exceptions(self, dispatcher, control_interface_mock, intent, slots, expected_exception):
        """
        Verify that dispatching intents with missing or invalid slots raises the appropriate exceptions.

        Args:
            dispatcher (IntentDispatcher): The dispatcher instance.
            control_interface_mock (Mock): The mocked control interface.
            intent (str): The intent to dispatch.
            slots (dict): The slots associated with the intent.
            expected_exception (Exception): The exception expected to be raised.
        """
        with pytest.raises(expected_exception):
            dispatcher.dispatch(intent, slots)

    @pytest.mark.parametrize(
        "intent, slots, expected_log",
        [
            ('run_sequence',   {},                                   "No sequence_name provided for run_sequence command."),
            ('set_brightness', {},                                   "No brightness_percentage provided for set_brightness command."),
            ('set_brightness', {'brightness_percentage': 'invalid'}, "Invalid brightness_percentage value: invalid."),
            ('set_speed',      {},                                   "No speed_percentage provided for set_speed command."),
            ('set_speed',      {'speed_percentage': 'invalid'},      "Invalid speed_percentage value: invalid."),
            ('set_accel',      {},                                   "No accel_percentage provided for set_accel command."),
            ('set_accel',      {'accel_percentage': 'invalid'},      "Invalid accel_percentage value: invalid."),
            ('move',           {},                                   "No direction provided for move command."),
        ]
    )
    def test_dispatch_intent_errors_logging(self, dispatcher, control_interface_mock, caplog, intent, slots, expected_log):
        """
        Verify that dispatching intents with missing or invalid slots logs the appropriate error messages.

        Args:
            dispatcher (IntentDispatcher): The dispatcher instance.
            control_interface_mock (Mock): The mocked ControlInterface.
            caplog: Pytest's fixture to capture log output.
            intent (str): The intent to dispatch.
            slots (dict): The slots associated with the intent.
            expected_log (str): The expected log message.
        """
        with caplog.at_level(logging.ERROR, logger="kws_logger"):
            dispatcher.dispatch(intent, slots)
            assert expected_log in caplog.text