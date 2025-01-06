import logging

logger = logging.getLogger(__name__)

class IntentDispatcher:
    def __init__(self, control_interface_module):
        self.control_interface = control_interface_module
        self.intent_handlers = {
            'move': self.handle_move,
            'stop': self.handle_stop,
            'idle_stance': self.handle_idle_stance,
            'rotate': self.handle_rotate,
            'turn_lights': self.handle_turn_lights,
            'change_color': self.handle_change_color,
            'repeat': self.handle_repeat,
            'hello': self.handle_hello,
            'show_off': self.handle_show_off,
            'dance': self.handle_dance,
            'set_speed': self.handle_set_speed,
            'set_accel': self.handle_set_accel,
            'set_brightness': self.handle_set_brightness,
            'shut_down': self.handle_shut_down,
            'wake_up': self.handle_wake_up,
            'sleep': self.handle_sleep,
            'low_profle_mode': self.handle_low_profile_mode,
            'upright_mode': self.handle_upright_mode,
            'helix': self.handle_helix,
            # 'mode': self.handle_mode,
            'calibrate': self.handle_calibrate
        }

    def dispatch(self, intent, slots):
        handler = self.intent_handlers.get(intent)
        if handler:
            handler(slots)
        else:
            raise NotImplementedError(f"No handler for intent: {intent}")

    def handle_move(self, slots):
        direction = slots.get('direction')
        if direction:
            logger.info(f"Handling move command: {direction}")
            self.control_interface.move(direction)
        else:
            logger.error("No direction provided for move command.")

    def handle_stop(self, slots):
        logger.info("Handling stop command.")
        self.control_interface.stop()

    def handle_idle_stance(self, slots):
        logger.info("Handling idle_stance command.")
        self.control_interface.idle_stance()

    def handle_rotate(self, slots):
        angle = slots.get('angle')
        turn_direction = slots.get('turn_direction')
        if angle:
            logger.info(f"Handling rotate command with angle: {angle}")
            self.control_interface.rotate(angle=angle)
        elif turn_direction:
            logger.info(f"Handling rotate command with direction: {turn_direction}")
            self.control_interface.rotate(direction=turn_direction)
        else:
            logger.error("No angle or turn_direction provided for rotate command.")

    def handle_turn_lights(self, slots):
        switch_state = slots.get('switch_state')
        logger.info(f"Handling turn_lights command: {switch_state}")
        self.control_interface.turn_lights(switch_state)

    def handle_change_color(self, slots):
        color = slots.get('color')
        logger.info(f"Handling change_color command: {color}")
        self.control_interface.change_color(color)

    def handle_repeat(self, slots):
        logger.info("Handling repeat command.")
        self.control_interface.repeat_last_command()

    def handle_hello(self, slots):
        logger.info("Handling hello command.")
        self.control_interface.say_hello()

    def handle_show_off(self, slots):
        logger.info("Handling show_off command.")
        self.control_interface.show_off()

    def handle_dance(self, slots):
        logger.info("Handling dance command.")
        self.control_interface.dance()

    def handle_set_speed(self, slots):
        speed_percentage = slots.get('speed_percentage')
        if speed_percentage:
            try:
                speed_value = parse_percentage(speed_percentage, 'speed_percentage')
                logger.info(f"Handling set_speed command: {speed_value}%")
                self.control_interface.set_speed(speed_value)
            except ValueError as e:
                logger.error(f"Invalid speed_percentage value: {speed_percentage}. Error: {e}")
                print(f"Error: {e}")
        else:
            logger.error("No speed_percentage provided for set_speed command.")

    def handle_set_accel(self, slots):
        accel_percentage = slots.get('accel_percentage')
        if accel_percentage:
            try:
                accel_value = parse_percentage(accel_percentage, 'accel_percentage')
                logger.info(f"Handling set_accel command: {accel_value}%")
                self.control_interface.set_acceleration(accel_value)
            except ValueError as e:
                logger.error(f"Invalid accel_percentage value: {accel_percentage}. Error: {e}")
                print(f"Error: {e}")
        else:
            logger.error("No accel_percentage provided for set_accel command.")

    def handle_set_brightness(self, slots):
        brightness_percentage = slots.get('brightness_percentage')
        if brightness_percentage:
            try:
                brightness_value = parse_percentage(brightness_percentage, 'brightness_percentage')
                logger.info(f"Handling set_brightness command: {brightness_value}%")
                self.control_interface.set_brightness(brightness_value)
            except ValueError as e:
                logger.error(f"Invalid brightness_percentage value: {brightness_percentage}. Error: {e}")
                print(f"Error: {e}")
        else:
            logger.error("No brightness_percentage provided for set_brightness command.")

    def handle_shut_down(self, slots):
        logger.info("Handling shut_down command.")
        self.control_interface.shut_down()

    def handle_wake_up(self, slots):
        logger.info("Handling wake_up command.")
        self.control_interface.wake_up()

    def handle_sleep(self, slots):
        logger.info("Handling sleep command.")
        self.control_interface.sleep()

    def handle_low_profile_mode(self, slots):
        logger.info("Handling low_profile_mode command.")
        self.control_interface.set_low_profile_mode()

    def handle_upright_mode(self, slots):
        logger.info("Handling upright_mode command.")
        self.control_interface.set_upright_mode()

    def handle_helix(self, slots):
        logger.info("Handling helix command.")
        self.control_interface.helix()

    # def handle_mode(self, slots):
    #     mode = slots.get('mode')
    #     if mode:
    #         logger.info(f"Handling mode command: {mode}")
    #         self.control_interface.change_mode(mode)
    #     else:
    #         logger.error("No mode provided for mode command.")

    def handle_calibrate(self, slots):
        logger.info("Handling calibrate command.")
        self.control_interface.calibrate()

def parse_percentage(value, param_name):
    if isinstance(value, str) and value.endswith('%'):
        value = value.rstrip('%')
    int_value = int(value)
    if not 0 <= int_value <= 100:
        raise ValueError(f"{param_name} must be between 0 and 100.")
    return int_value