from maestro.maestro_uart import MaestroUART
from hexapod.leg import Leg

class Hexapod:
    def __init__(self):
        """
        Represents the hexapod robot with six legs.
        """
        self.controller = MaestroUART('/dev/ttyS0', 9600)

        self.legs = []
        for i in range(6):
            # Define joint parameters
            coxa_params = {
                'channel': i * 3,
                'angle_min': -45,
                'angle_max': 45,
                'servo_min': 992 * 4,
                'servo_max': 2000 * 4,
                'length': 30.0
            }
            femur_params = {
                'channel': i * 3 + 1,
                'angle_min': -45,
                'angle_max': 90,
                'servo_min': 992 * 4,
                'servo_max': 2000 * 4,
                'length': 50.0
            }
            tibia_params = {
                'channel': i * 3 + 2,
                'angle_min': -90,
                'angle_max': 0,
                'servo_min': 992 * 4,
                'servo_max': 2000 * 4,
                'length': 80.0
            }
            leg = Leg(coxa_params, femur_params, tibia_params, self.controller)
            self.legs.append(leg)


    def move_leg(self, leg_index, x, y, z, speed=32, accel=5):
        """
        Command a leg to move to a position.

        Args:
            leg_index (int): Index of the leg (0-5).
            x, y, z (float): Target coordinates.
            speed (int): Servo speed.
            accel (int): Servo acceleration.
        """
        self.legs[leg_index].move_to(x, y, z, speed, accel)

    def move_all_legs(self, positions, speed=32, accel=5):
        """
        Command all legs to move to specified positions.

        Args:
            positions (list): List of (x, y, z) tuples.
            speed (int): Servo speed.
            accel (int): Servo acceleration.
        """
        for i, pos in enumerate(positions):
            x, y, z = pos
            self.move_leg(i, x, y, z, speed, accel)

    # Implement gait algorithms here

# Example usage
if __name__ == '__main__':
    hexapod = Hexapod()

    # Define target positions for each leg
    positions = [
        (100.0,  50.0, -50.0),  # Leg 0
        (100.0, -50.0, -50.0),  # Leg 1
        (80.0,  60.0, -50.0),   # Leg 2
        (80.0, -60.0, -50.0),   # Leg 3
        (60.0,  70.0, -50.0),   # Leg 4
        (60.0, -70.0, -50.0),   # Leg 5
    ]

    # Move all legs to their initial positions
    hexapod.move_all_legs(positions)

    # Implement gait control loops and additional functionality