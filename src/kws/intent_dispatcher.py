import logging

logger = logging.getLogger(__name__)

class CentralDispatcher:
    def __init__(self, control_module):
        self.control = control_module
        self.intent_handlers = {
            'move': self.handle_move,
            'turn': self.handle_turn,
            'stop': self.handle_stop,
            'mode': self.handle_mode,
            # Add other intents here
        }

    def dispatch(self, intent, slots):
        handler = self.intent_handlers.get(intent)
        if handler:
            handler(slots)
        else:
            logger.warning(f"No handler for intent: {intent}")

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

    # Define additional handlers as needed