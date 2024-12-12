import logging

logger = logging.getLogger(__name__)

class IntentDispatcher:
    def __init__(self, control_module):
        self.control = control_module
        self.intent_handlers = {
            'move': self.handle_move,
            'turn': self.handle_turn,
            'stop': self.handle_stop,
            'mode': self.handle_mode,
            'turn_lights': self.handle_turn_lights,
            'change_color': self.handle_change_color
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
            self.control.move(direction)
        else:
            logger.error("No direction provided for move command.")

    def handle_turn(self, slots):
        turn_direction = slots.get('turn_direction')
        if turn_direction:
            logger.info(f"Handling turn command: {turn_direction}")
            self.control.turn(turn_direction)
        else:
            logger.error("No turn_direction provided for turn command.")

    def handle_stop(self, slots):
        logger.info("Handling stop command.")
        self.control.stop()

    def handle_mode(self, slots):
        mode = slots.get('mode')
        if mode:
            logger.info(f"Handling mode command: {mode}")
            self.control.change_mode(mode)
        else:
            logger.error("No mode provided for mode command.")

    def handle_turn_lights(self, slots):
        switch_state = slots.get('switch_state')
        logger.info(f"Handling turn_lights command: {switch_state}")
        self.control.turn_lights(switch_state)

    def handle_change_color(self, slots):
        color = slots.get('color')
        logger.info(f"Handling change_color command: {color}")
        self.control.change_color(color)