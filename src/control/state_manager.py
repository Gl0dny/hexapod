from enum import Enum, auto

class RobotState(Enum):
    IDLE = auto()
    MOVING = auto()
    TURNING = auto()
    CHANGING_MODE = auto()
    # Add other states as needed

class StateManager:
    def __init__(self):
        self.state = RobotState.IDLE

    def set_state(self, new_state):
        print(f"State changed from {self.state} to {new_state}")
        self.state = new_state

    def can_execute(self, intent):
        # Define rules for state transitions
        # Example: Allow any command if idle
        if self.state == RobotState.IDLE:
            return True
        # Example: Prevent new commands while moving
        if self.state == RobotState.MOVING and intent not in ['stop']:
            return False
        # Add more conditions as needed
        return True