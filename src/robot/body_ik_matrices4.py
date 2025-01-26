import numpy as np

def create_rotation_matrix(roll, pitch, yaw):
    """
    Create a combined rotation matrix from roll, pitch, and yaw angles.
    """
    roll_rad = np.radians(roll)
    pitch_rad = np.radians(pitch)
    yaw_rad = np.radians(yaw)
    
    R_x = np.array([
        [1, 0, 0],
        [0, np.cos(roll_rad), -np.sin(roll_rad)],
        [0, np.sin(roll_rad), np.cos(roll_rad)]
    ])
    
    R_y = np.array([
        [np.cos(pitch_rad), 0, np.sin(pitch_rad)],
        [0, 1, 0],
        [-np.sin(pitch_rad), 0, np.cos(pitch_rad)]
    ])
    
    R_z = np.array([
        [np.cos(yaw_rad), -np.sin(yaw_rad), 0],
        [np.sin(yaw_rad), np.cos(yaw_rad), 0],
        [0, 0, 1]
    ])
    
    return R_z @ R_y @ R_x

def create_transformation_matrix(tx=0, ty=0, tz=0, roll=0, pitch=0, yaw=0):
    """
    Create a homogeneous transformation matrix from translation and rotation parameters.
    """
    # Create rotation matrix
    R = create_rotation_matrix(roll, pitch, yaw)
    
    # Create homogeneous transformation matrix
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = [tx, ty, tz]
    
    return T

def compute_body_inverse_kinematics(tx=0, ty=0, tz=0, roll=0, pitch=0, yaw=0):
    """
    Calculate leg position deltas using homogeneous transformations
    Inputs in mm and degrees
    Returns: 6x3 array of (Δx, Δy, Δz) for each leg
    """

    # Parameters from initial problem
    HEX_SIDE_LENGTH = 137.0
    COXA_LENGTH = 27.5
    FEMUR_LENGTH = 52.5
    TIBIA_LENGTH = 162.5

    # Calculate total horizontal extension from body center
    BODY_RADIUS = HEX_SIDE_LENGTH  # For regular hexagon, side length = radius
    EXTENSION_LENGTH = COXA_LENGTH + FEMUR_LENGTH
    TOTAL_RADIUS = BODY_RADIUS + EXTENSION_LENGTH

    # Calculate initial end effector positions
    compute_hexagon_angles = lambda: [i * 60 for i in range(6)]
    leg_angles = compute_hexagon_angles()
    initial_positions = np.array([
        [
            TOTAL_RADIUS * np.cos(theta),
            TOTAL_RADIUS * np.sin(theta),
            -TIBIA_LENGTH  # Tibia points downward
        ] for theta in leg_angles
    ])

    # Create homogeneous transformation matrix
    T = create_transformation_matrix(tx, ty, tz, roll, pitch, yaw)
    
    # Apply transformation
    homogenous_pos = np.hstack((initial_positions, np.ones((6, 1))))
    transformed = (homogenous_pos @ T.T)[:, :3]
    
    # Calculate deltas relative to initial positions
    deltas = transformed - initial_positions
    return np.round(deltas, 2)

def transform_deltas_to_local_frames(deltas):
    """
    Transform deltas from global frame to each leg's local frame.
    Each leg's local frame is rotated -90° relative to its mounting angle.
    """
    # Leg mounting angles (in degrees)
    leg_orientations = np.radians([0, 60, 120, 180, 240, 300])
    
    # Initialize array for local deltas
    local_deltas = np.zeros_like(deltas)
    
    for i, theta in enumerate(leg_orientations):
        # Create rotation matrix for leg's local frame (-90° relative to mounting angle)
        R_local = np.array([
            [np.sin(theta), -np.cos(theta), 0],  # X-axis: perpendicular to mounting angle
            [np.cos(theta), np.sin(theta), 0],   # Y-axis: along mounting angle
            [0, 0, 1]                            # Z-axis: unchanged
        ])
        
        # Transform delta to local frame
        local_deltas[i] = R_local @ deltas[i]
    
    return np.round(local_deltas, 2)

# Example 1: Pure Yaw rotation (10 degrees)
# print("Example 1 - Yaw Rotation (10°):")
# global_deltas = compute_body_inverse_kinematics(yaw=10)
# local_deltas = transform_deltas_to_local_frames(global_deltas)
# print("Global Deltas:")
# print(global_deltas)
# print("Local Deltas:")
# print(local_deltas)

# # Example 2: Combined movement with your Excel parameters
# print("\nExample 2 - Combined Transformation (ty=10, roll=10°):")
# global_deltas = compute_body_inverse_kinematics(ty=10, roll=10)
# local_deltas = transform_deltas_to_local_frames(global_deltas)
# print("Global Deltas:")
# print(global_deltas)
# print("Local Deltas:")
# print(local_deltas)

# Example 3: Pure translation
print("\nExample 3 - Pure Translation (tx=10):")
global_deltas = compute_body_inverse_kinematics(tx=10)
local_deltas = transform_deltas_to_local_frames(global_deltas)
print("Global Deltas:")
print(global_deltas)
print("Local Deltas:")
print(local_deltas)
