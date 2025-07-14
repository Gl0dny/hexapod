"""
Module: intent_dispatcher

This module defines the IntentDispatcher class, which is responsible for
dispatching intents to their corresponding handler methods. It interacts
with the TaskInterface to execute actions based on the received intents
and associated slots.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import logging
from functools import wraps

from utils import parse_percentage

if TYPE_CHECKING:
    from typing import Dict, Callable, Any

logger = logging.getLogger("kws_logger")

def handler(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(self, slots: Dict[str, Any]) -> None:
        logger.debug(f"Handling intent with {func.__name__}")
        func(self, slots)
        logger.debug(f"Handled intent with {func.__name__}")
    return wrapper

class IntentDispatcher:
    """
    Dispatches intents to their corresponding handler methods.
    """

    def __init__(self, task_interface: Any) -> None:
        """
        Initialize the IntentDispatcher with a task interface module.
        
        Args:
            task_interface (Any): The task interface module to handle intents.
        """
        self.task_interface = task_interface
        self.intent_handlers: Dict[str, Callable[[Dict[str, Any]], None]] = {
            'help': self.handle_help,
            'system_status': self.handle_system_status,
            'shut_down': self.handle_shut_down,
            'wake_up': self.handle_wake_up,
            'sleep': self.handle_sleep,
            'calibrate': self.handle_calibrate,
            'run_sequence': self.handle_run_sequence,
            'repeat': self.handle_repeat,
            'turn_lights': self.handle_turn_lights,
            'change_color': self.handle_change_color,
            'set_brightness': self.handle_set_brightness,
            'set_speed': self.handle_set_speed,
            'set_accel': self.handle_set_accel,
            # 'march_in_place': self.handle_march_in_place, #TODO train model for this command
            'idle_stance': self.handle_idle_stance,
            'move': self.handle_move,
            'stop': self.handle_stop,
            'rotate': self.handle_rotate,
            'follow': self.handle_follow,
            'sound_source_localization': self.handle_sound_source_localization,
            'stream_odas_audio': self.handle_stream_odas_audio,
            'police': self.handle_police,
            'rainbow': self.handle_rainbow,
            'sit_up': self.handle_sit_up,
            'dance': self.handle_dance,
            'helix': self.handle_helix,
            'show_off': self.handle_show_off,
            'hello': self.handle_hello
        }
        logger.debug("IntentDispatcher initialized successfully.")

    def dispatch(self, intent: str, slots: Dict[str, Any]) -> None:
        """
        Dispatch the given intent to the appropriate handler.
        
        Args:
            intent (str): The intent to handle.
            slots (Dict[str, Any]): Additional data for the intent.
        
        Raises:
            NotImplementedError: If no handler exists for the given intent.
        """
        logger.debug(f"Dispatching intent: {intent} with slots: {slots}")
        handler = self.intent_handlers.get(intent)
        if handler:
            handler(slots)
            logger.debug(f"Intent '{intent}' dispatched successfully.")
        else:
            raise NotImplementedError(f"No handler for intent: {intent}")

    def _parse_duration_in_seconds(self, value, unit):
        """Helper to convert value and time_unit to seconds."""
        if value is None or unit is None:
            return None
        try:
            value = float(value)
            unit = unit.lower()
            if unit in ["second", "seconds"]:
                return value
            elif unit in ["minute", "minutes"]:
                return value * 60
            elif unit in ["hour", "hours"]:
                return value * 3600
        except Exception:
            logger.exception(f"Invalid duration or time unit: {value}, {unit}")
        return None

    @handler
    def handle_help(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'help' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        self.task_interface.hexapod_help()
            
    @handler
    def handle_system_status(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'system_status' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        self.task_interface.system_status()
            
    @handler
    def handle_shut_down(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'shut_down' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        self.task_interface.shut_down()

    @handler
    def handle_wake_up(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'wake_up' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        self.task_interface.wake_up()

    @handler
    def handle_sleep(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'sleep' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        self.task_interface.sleep()

    @handler
    def handle_calibrate(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'calibrate' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        self.task_interface.calibrate()

    @handler
    def handle_run_sequence(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'run_sequence' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        try:
            sequence_name = slots['sequence_name']
            self.task_interface.run_sequence(sequence_name=sequence_name)
        except KeyError:
            logger.exception("No sequence_name provided for run_sequence command.")

    @handler
    def handle_repeat(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'repeat' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        self.task_interface.repeat_last_command()

    @handler
    def handle_turn_lights(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'turn_lights' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        switch_state = slots.get('switch_state')
        self.task_interface.turn_lights(switch_state)

    @handler
    def handle_change_color(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'change_color' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        color = slots.get('color')
        self.task_interface.change_color(color=color)

    @handler
    def handle_set_brightness(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'set_brightness' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        try:
            brightness_percentage = slots['brightness_percentage']
            brightness_value = parse_percentage(brightness_percentage)
            self.task_interface.set_brightness(brightness_value)
        except KeyError:
            logger.exception("No brightness_percentage provided for set_brightness command.")
        except ValueError:
            logger.exception(f"Invalid brightness_percentage value: {brightness_percentage}.")

    @handler
    def handle_set_speed(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'set_speed' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        try:
            speed_percentage = slots['speed_percentage']
            speed_value = parse_percentage(speed_percentage)
            self.task_interface.set_speed(speed_value)
        except KeyError:
            logger.exception("No speed_percentage provided for set_speed command.")
        except ValueError:
            logger.exception(f"Invalid speed_percentage value: {speed_percentage}.")

    @handler
    def handle_set_accel(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'set_accel' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        try:
            accel_percentage = slots['accel_percentage']
            accel_value = parse_percentage(accel_percentage)
            self.task_interface.set_accel(accel_value)
        except KeyError:
            logger.exception("No accel_percentage provided for set_accel command.")
        except ValueError:
            logger.exception(f"Invalid accel_percentage value: {accel_percentage}.")

    @handler
    def handle_march_in_place(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'march_in_place' intent, supporting duration and time-based marching.
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        try:
            march_time = None
            time_unit = None
            if 'march_time' in slots:
                try:
                    march_time = float(slots['march_time'])
                except Exception:
                    logger.exception(f"Invalid march_time value: {slots['march_time']}")
            if 'time_unit' in slots:
                time_unit = slots['time_unit']
            duration_seconds = self._parse_duration_in_seconds(march_time, time_unit) if march_time and time_unit else None
            if duration_seconds is not None:
                self.task_interface.march_in_place(duration=duration_seconds)
            else:
                self.task_interface.march_in_place()
        except Exception as e:
            logger.exception(f"Error handling march_in_place intent: {e}")

    @handler
    def handle_idle_stance(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'idle_stance' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        self.task_interface.idle_stance()

    @handler
    def handle_move(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'move' intent, supporting direction, cycles, and time-based movement.
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        try:
            direction = slots.get('move_direction')
            if not direction:
                logger.exception("No direction provided for move command.")
                return

            from gait_generator.base_gait import BaseGait
            if direction not in BaseGait.DIRECTION_MAP:
                logger.exception(f"Invalid direction '{direction}' for move command.")
                return

            move_cycles = None
            move_time = None
            time_unit = None
            if 'move_cycles' in slots:
                try:
                    move_cycles = int(slots['move_cycles'])
                except Exception:
                    logger.exception(f"Invalid move_cycles value: {slots['move_cycles']}")
            if 'move_time' in slots:
                try:
                    move_time = int(slots['move_time'])
                except Exception:
                    logger.exception(f"Invalid move_time value: {slots['move_time']}")
            if 'time_unit' in slots:
                time_unit = slots['time_unit']

            duration_seconds = self._parse_duration_in_seconds(move_time, time_unit) if move_time and time_unit else None

            if move_cycles is not None:
                self.task_interface.move(direction=direction, cycles=move_cycles)
            elif duration_seconds is not None:
                self.task_interface.move(direction=direction, duration=duration_seconds)
            else:
                self.task_interface.move(direction=direction)
        except Exception as e:
            logger.exception(f"Error handling move intent: {e}")

    @handler
    def handle_stop(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'stop' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        self.task_interface.stop()
            
    @handler
    def handle_rotate(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'rotate' intent, supporting direction, cycles, time, and angle-based rotation.
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        try:
            turn_direction = slots.get('turn_direction')
            angle = None
            rotate_cycles = None
            rotate_time = None
            time_unit = None

            valid_turn_directions = {'left', 'right', 'clockwise', 'counterclockwise'}
            if turn_direction and turn_direction not in valid_turn_directions:
                logger.exception(f"Invalid turn_direction '{turn_direction}' for rotate command.")
                return

            if 'rotate_angle' in slots:
                try:
                    angle = float(slots['rotate_angle'])
                except Exception:
                    logger.exception(f"Invalid rotate_angle value: {slots['rotate_angle']}")
            if 'rotate_cycles' in slots:
                try:
                    rotate_cycles = int(slots['rotate_cycles'])
                except Exception:
                    logger.exception(f"Invalid rotate_cycles value: {slots['rotate_cycles']}")
            if 'rotate_time' in slots:
                try:
                    rotate_time = int(slots['rotate_time'])
                except Exception:
                    logger.exception(f"Invalid rotate_time value: {slots['rotate_time']}")
            if 'time_unit' in slots:
                time_unit = slots['time_unit']

            duration_seconds = self._parse_duration_in_seconds(rotate_time, time_unit) if rotate_time and time_unit else None

            if angle is not None:
                self.task_interface.rotate(turn_direction=turn_direction, angle=angle)
            elif rotate_cycles is not None:
                self.task_interface.rotate(turn_direction=turn_direction, cycles=rotate_cycles)
            elif duration_seconds is not None:
                self.task_interface.rotate(turn_direction=turn_direction, duration=duration_seconds)
            else:
                self.task_interface.rotate(turn_direction=turn_direction)
        except Exception as e:
            logger.exception(f"Error handling rotate intent: {e}")

    @handler
    def handle_follow(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'follow' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        self.task_interface.follow()

    @handler
    def handle_sound_source_localization(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'sound_source_localization' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        self.task_interface.sound_source_localization()

    @handler
    def handle_stream_odas_audio(self, slots: Dict[str, Any]) -> None:
        """
        Handle the stream_odas_audio intent.

        Args:
            slots (Dict[str, Any]): Additional data for the intent.
            
        If odas_stream_type is provided, use it; otherwise use default (separated).
        """
        try:
            stream_type = slots.get("odas_stream_type", "separated")
            # Convert "post filtered" to "postfiltered" to match the expected format
            if stream_type == "post filtered":
                stream_type = "postfiltered"
            self.task_interface.stream_odas_audio(stream_type=stream_type)
        except Exception as e:
            logger.exception(f"Error handling stream_odas_audio intent: {e}")

    @handler
    def handle_police(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'police' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        self.task_interface.police()

    @handler
    def handle_rainbow(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'rainbow' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        self.task_interface.rainbow()
            
    @handler
    def handle_sit_up(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'sit_up' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        self.task_interface.sit_up()

    @handler
    def handle_dance(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'dance' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        self.task_interface.dance()

    @handler
    def handle_helix(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'helix' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        self.task_interface.helix()

    @handler
    def handle_show_off(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'show_off' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        self.task_interface.show_off()

    @handler
    def handle_hello(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'hello' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        self.task_interface.say_hello()