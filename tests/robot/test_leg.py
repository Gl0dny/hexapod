import math

class RobotLeg:
    def __init__(self, coxa_length, femur_length, tibia_length, end_effector_offset):
        self.coxa = self.Joint(coxa_length)
        self.femur = self.Joint(femur_length)
        self.tibia = self.Joint(tibia_length)
        self.end_effector_offset = end_effector_offset

    class Joint:
        def __init__(self, length):
            self.length = length

    def compute_inverse_kinematics(self, x, y, z):
        """
        Compute the joint angles for the desired foot position.

        Args:
            x (float): X coordinate of the foot position.
            y (float): Y coordinate of the foot position.
            z (float): Z coordinate of the foot position.

        Returns:
            tuple: (theta1, theta2, theta3) in degrees.
        """
        # Calculate the horizontal distance to the target using coxa length
        horizontal_distance = math.hypot(x, y) - self.coxa.length

        # Angle for the coxa joint
        theta1 = math.atan2(x, y)

        # Distance from femur joint to foot position
        r = math.hypot(horizontal_distance, z)
        if r > (self.femur.length + self.tibia.length):
            raise ValueError("Target is out of reach.")

        # Inverse kinematics calculations
        cos_theta3 = (self.femur.length**2 + self.tibia.length**2 - r**2) / (2 * self.femur.length * self.tibia.length)
        theta3 = math.acos(cos_theta3)

        cos_theta2 = (self.femur.length**2 + r**2 - self.tibia.length**2) / (2 * self.femur.length * r)
        theta2 = math.atan2(z, horizontal_distance) - math.acos(cos_theta2)

        theta1_deg, theta2_deg, theta3_deg = map(math.degrees, [theta1, theta2, theta3])

            # Clamp to motor range [-45, 45]
        # if not (-45 <= theta1_deg <= 45):
        #     raise ValueError(f"Coxa angle {theta1_deg}° is out of range.")
        # if not (-45 <= theta2_deg <= 45):
        #     raise ValueError(f"Femur angle {theta2_deg}° is out of range.")
        # if not (-45 <= theta3_deg <= 45):
        #     raise ValueError(f"Tibia angle {theta3_deg}° is out of range.")
    
        return theta1_deg, theta2_deg, theta3_deg


def test_inverse_kinematics():
    # Define robot dimensions
    coxa_length = 5.0
    femur_length = 10.0
    tibia_length = 15.0

    # Define end effector offset
    end_effector_offset = {
        'x': 0,  # Set appropriate values
        'y': 0,
        'z': 0
    }

    # Initialize the robot leg
    leg = RobotLeg(coxa_length, femur_length, tibia_length, end_effector_offset)

    # Test cases
    test_cases = [
        {"x": 10, "y": 0, "z": 0, "desc": "Straight forward"},
        {"x": 0, "y": 10, "z": 0, "desc": "Straight to the side"},
        {"x": 5, "y": 5, "z": 5, "desc": "Diagonal in 3D space"},
        {"x": 5, "y": 5, "z": -5, "desc": "Below the plane"},
        {"x": 0, "y": 0, "z": 10, "desc": "Vertical"},
        {"x": 20, "y": 0, "z": 0, "desc": "Out of reach"}  # Expect error
    ]

    # Run tests
    for case in test_cases:
        try:
            angles = leg.compute_inverse_kinematics(case["x"], case["y"], case["z"])
            print(f"Test '{case['desc']}': (x={case['x']}, y={case['y']}, z={case['z']}) -> Angles: {angles}")
        except ValueError as e:
            print(f"Test '{case['desc']}': (x={case['x']}, y={case['y']}, z={case['z']}) -> Error: {e}")

    # Edge case: very close to the origin
    try:
        angles = leg.compute_inverse_kinematics(0.1, 0.1, 0.1)
        print(f"Edge case near origin -> Angles: {angles}")
    except ValueError as e:
        print(f"Edge case near origin -> Error: {e}")

if __name__ == "__main__":
    print("Testing inverse kinematics calculations...\n")
    test_inverse_kinematics()
