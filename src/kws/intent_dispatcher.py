from __future__ import annotations
from typing import TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from typing import Dict, Callable, Any

logger = logging.getLogger("kws_logger")

class IntentDispatcher:
    """
    Dispatches intents to their corresponding handler methods.
    """

    def __init__(self, control_interface_module: Any) -> None:
        """
        Initialize the IntentDispatcher with a control interface module.
        
        Args:
            control_interface_module (Any): The control interface module to handle intents.
        """
        self.control_interface = control_interface_module
        self.intent_handlers: Dict[str, Callable[[Dict[str, Any]], None]] = {
            'help': self.handle_help,
            'system_status': self.handle_system_status,
            'shut_down': self.handle_shut_down,
            'emergency_stop': self.handle_emergency_stop,
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
            'low_profle_mode': self.handle_low_profile_mode,
            'upright_mode': self.handle_upright_mode,
            'idle_stance': self.handle_idle_stance,
            'move': self.handle_move,
            'stop': self.handle_stop,
            'rotate': self.handle_rotate,
            'follow': self.handle_follow,
            'sound_source_analysis': self.handle_sound_source_analysis,
            'direction_of_arrival': self.handle_direction_of_arrival,
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

    def handle_help(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'help' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'help' intent with slots: {slots}")
        self.control_interface.hexapod_help()
        logger.debug("Handled 'help' intent successfully.")
        
    def handle_system_status(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'system_status' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'system_status' intent with slots: {slots}")
        self.control_interface.system_status()
        logger.debug("Handled 'system_status' intent successfully.")
        
    def handle_shut_down(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'shut_down' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'shut_down' intent with slots: {slots}")
        self.control_interface.shut_down()
        logger.debug("Handled 'shut_down' intent successfully.")

    def handle_emergency_stop(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'emergency_stop' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'emergency_stop' intent with slots: {slots}")
        self.control_interface.emergency_stop()
        logger.debug("Handled 'emergency_stop' intent successfully.")

    def handle_wake_up(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'wake_up' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'wake_up' intent with slots: {slots}")
        self.control_interface.wake_up()
        logger.debug("Handled 'wake_up' intent successfully.")

    def handle_sleep(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'sleep' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'sleep' intent with slots: {slots}")
        self.control_interface.sleep()
        logger.debug("Handled 'sleep' intent successfully.")

    def handle_calibrate(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'calibrate' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'calibrate' intent with slots: {slots}")
        self.control_interface.calibrate()
        logger.debug("Handled 'calibrate' intent successfully.")

    def handle_run_sequence(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'run_sequence' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'run_sequence' intent with slots: {slots}")
        sequence_name = slots.get('sequence_name')
        if sequence_name:
            self.control_interface.run_sequence(sequence_name)
            logger.debug("Handled 'run_sequence' intent successfully.")
        else:
            logger.error("No sequence_name provided for run_sequence command.")

    def handle_repeat(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'repeat' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'repeat' intent with slots: {slots}")
        self.control_interface.repeat_last_command()
        logger.debug("Handled 'repeat' intent successfully.")

    def handle_turn_lights(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'turn_lights' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'turn_lights' intent with slots: {slots}")
        switch_state = slots.get('switch_state')
        self.control_interface.turn_lights(switch_state)
        logger.debug("Handled 'turn_lights' intent successfully.")

    def handle_change_color(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'change_color' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'change_color' intent with slots: {slots}")
        color = slots.get('color')
        self.control_interface.change_color(color)
        logger.debug("Handled 'change_color' intent successfully.")

    def handle_set_brightness(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'set_brightness' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'set_brightness' intent with slots: {slots}")
        brightness_percentage = slots.get('brightness_percentage')
        if brightness_percentage:
            try:
                brightness_value = parse_percentage(brightness_percentage, 'brightness_percentage')
                self.control_interface.set_brightness(brightness_value)
                logger.debug("Handled 'set_brightness' intent successfully.")
            except ValueError as e:
                logger.error(f"Invalid brightness_percentage value: {brightness_percentage}. Error: {e}")
                print(f"Error: {e}")
        else:
            logger.error("No brightness_percentage provided for set_brightness command.")

    def handle_set_speed(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'set_speed' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'set_speed' intent with slots: {slots}")
        speed_percentage = slots.get('speed_percentage')
        if speed_percentage:
            try:
                speed_value = parse_percentage(speed_percentage, 'speed_percentage')
                self.control_interface.set_speed(speed_value)
                logger.debug("Handled 'set_speed' intent successfully.")
            except ValueError as e:
                logger.error(f"Invalid speed_percentage value: {speed_percentage}. Error: {e}")
                print(f"Error: {e}")
        else:
            logger.error("No speed_percentage provided for set_speed command.")

    def handle_set_accel(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'set_accel' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'set_accel' intent with slots: {slots}")
        accel_percentage = slots.get('accel_percentage')
        if accel_percentage:
            try:
                accel_value = parse_percentage(accel_percentage, 'accel_percentage')
                self.control_interface.set_acceleration(accel_value)
                logger.debug("Handled 'set_accel' intent successfully.")
            except ValueError as e:
                logger.error(f"Invalid accel_percentage value: {accel_percentage}. Error: {e}")
                print(f"Error: {e}")
        else:
            logger.error("No accel_percentage provided for set_accel command.")

    def handle_low_profile_mode(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'low_profile_mode' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'low_profile_mode' intent with slots: {slots}")
        self.control_interface.set_low_profile_mode()
        logger.debug("Handled 'low_profile_mode' intent successfully.")

    def handle_upright_mode(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'upright_mode' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'upright_mode' intent with slots: {slots}")
        self.control_interface.set_upright_mode()
        logger.debug("Handled 'upright_mode' intent successfully.")

    def handle_idle_stance(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'idle_stance' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'idle_stance' intent with slots: {slots}")
        self.control_interface.idle_stance()
        logger.debug("Handled 'idle_stance' intent successfully.")

    def handle_move(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'move' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'move' intent with slots: {slots}")
        direction = slots.get('direction')
        if direction:
            self.control_interface.move(direction)
            logger.debug("Handled 'move' intent successfully.")
        else:
            logger.error("No direction provided for move command.")

    def handle_stop(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'stop' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'stop' intent with slots: {slots}")
        self.control_interface.stop()
        logger.debug("Handled 'stop' intent successfully.")
        
    def handle_rotate(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'rotate' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'rotate' intent with slots: {slots}")
        angle = slots.get('angle')
        turn_direction = slots.get('turn_direction')
        if angle:
            self.control_interface.rotate(angle=angle)
            logger.debug("Handled 'rotate' intent successfully.")
        elif turn_direction:
            self.control_interface.rotate(direction=turn_direction)
            logger.debug("Handled 'rotate' intent successfully.")
        else:
            logger.error("No angle or turn_direction provided for rotate command.")

    def handle_follow(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'follow' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'follow' intent with slots: {slots}")
        self.control_interface.follow()
        logger.debug("Handled 'follow' intent successfully.")

    def handle_sound_source_analysis(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'sound_source_analysis' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'sound_source_analysis' intent with slots: {slots}")
        self.control_interface.sound_source_analysis()
        logger.debug("Handled 'sound_source_analysis' intent successfully.")

    def handle_direction_of_arrival(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'direction_of_arrival' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'direction_of_arrival' intent with slots: {slots}")
        self.control_interface.direction_of_arrival()
        logger.debug("Handled 'direction_of_arrival' intent successfully.")

    def handle_police(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'police' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'police' intent with slots: {slots}")
        self.control_interface.police()
        logger.debug("Handled 'police' intent successfully.")

    def handle_rainbow(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'rainbow' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'rainbow' intent with slots: {slots}")
        self.control_interface.rainbow()
        logger.debug("Handled 'rainbow' intent successfully.")
        
    def handle_sit_up(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'sit_up' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'sit_up' intent with slots: {slots}")
        self.control_interface.sit_up()
        logger.debug("Handled 'sit_up' intent successfully.")

    def handle_dance(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'dance' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'dance' intent with slots: {slots}")
        self.control_interface.dance()
        logger.debug("Handled 'dance' intent successfully.")

    def handle_helix(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'helix' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'helix' intent with slots: {slots}")
        self.control_interface.helix()
        logger.debug("Handled 'helix' intent successfully.")

    def handle_show_off(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'show_off' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'show_off' intent with slots: {slots}")
        self.control_interface.show_off()
        logger.debug("Handled 'show_off' intent successfully.")

    def handle_hello(self, slots: Dict[str, Any]) -> None:
        """
        Handle the 'hello' intent.
        
        Args:
            slots (Dict[str, Any]): Additional data for the intent.
        """
        logger.debug(f"Handling 'hello' intent with slots: {slots}")
        self.control_interface.say_hello()
        logger.debug("Handled 'hello' intent successfully.")

def parse_percentage(value: Any, param_name: str) -> int:
    """
    Parse a percentage value ensuring it's between 0 and 100.
    
    Args:
        value (Any): The value to parse.
        param_name (str): The name of the parameter for error messages.
    
    Returns:
        int: The parsed percentage value.
    
    Raises:
        ValueError: If the value is not a valid percentage.
    """
    if isinstance(value, str) and value.endswith('%'):
        value = value.rstrip('%')
    int_value = int(value)
    if not 0 <= int_value <= 100:
        raise ValueError(f"{param_name} must be between 0 and 100.")
    return int_value