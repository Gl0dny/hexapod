import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d import Axes3D
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from unittest.mock import patch
import contextlib
import io
import csv
import argparse
from robot import Hexapod

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true", help="Clean workspace CSV file before calculations.")
    args = parser.parse_args()

    if args.clean and os.path.exists('leg_workspace.csv'):
        os.remove('leg_workspace.csv')

    # Initialize Hexapod instance with mocked serial and IMU
    with patch('robot.hexapod.MaestroUART'), \
         patch('robot.hexapod.Imu'):  # Updated patch target
        hexapod = Hexapod(
            config_path="/home/gl0dny/workspace/hexapod/src/robot/config/hexapod_config.yaml",
            calibration_data_path='/home/gl0dny/workspace/hexapod/src/robot/config/calibration.json'
        )

    # Define angle ranges based on configuration
    coxa_min = hexapod.coxa_params['angle_min']
    coxa_max = hexapod.coxa_params['angle_max']
    femur_min = hexapod.femur_params['angle_min']
    femur_max = hexapod.femur_params['angle_max']
    tibia_min = hexapod.tibia_params['angle_min']
    tibia_max = hexapod.tibia_params['angle_max']

    angle_step = 2  # Define step size for angles

    coxa_angles = range(coxa_min, coxa_max + 1, angle_step)
    femur_angles = range(femur_min, femur_max + 1, angle_step)
    tibia_angles = range(tibia_min, tibia_max + 1, angle_step)

    leg_workspace = []

    # Check if 'leg_workspace.csv' exists
    if os.path.exists('leg_workspace.csv'):
        with open('leg_workspace.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)  # Skip header
            for row in reader:
                try:
                    if len(row) == 6:
                        # coxa_deg, femur_deg, tibia_deg, x, y, z
                        c, f, t, x, y, z = map(float, row)
                    else:
                        # x, y, z only
                        x, y, z = map(float, row)
                    leg_workspace.append((x, y, z))
                except ValueError:
                    pass
    else:
        for coxa in coxa_angles:
            for femur in femur_angles:
                for tibia in tibia_angles:
                    try:
                        with contextlib.redirect_stdout(io.StringIO()):
                            x, y, z = hexapod.legs[0].compute_forward_kinematics(coxa, femur, tibia)
                        # Store angles plus computed position
                        leg_workspace.append((coxa, femur, tibia, x, y, z))
                    except ValueError:
                        pass

        # Convert to numpy array for easier plotting
        leg_workspace = np.array(leg_workspace)

        with open('leg_workspace.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['coxa_deg', 'femur_deg', 'tibia_deg', 'x', 'y', 'z'])
            writer.writerows(leg_workspace)

    # Convert to numpy array if loaded from CSV
    if not isinstance(leg_workspace, np.ndarray):
        leg_workspace = np.array(leg_workspace)

    # Extract x, y, z columns for plotting
    if leg_workspace.shape[1] == 6:
        display_points = leg_workspace[:, 3:]  # last 3 columns
    else:
        display_points = leg_workspace

    fig = plt.figure(figsize=(16, 8))
    gs = gridspec.GridSpec(nrows=3, ncols=2, width_ratios=[2, 1])

    # Add a title to the entire figure
    fig.suptitle("Hexapod Leg Reachable Workspace", fontsize=16)

    # Large isometric view spanning left column
    ax1 = fig.add_subplot(gs[:, 0], projection='3d')
    ax1.scatter(display_points[:, 0], display_points[:, 1], display_points[:, 2], s=1, c='blue')
    ax1.set_xlabel("X-axis (mm)")
    ax1.set_ylabel("Y-axis (mm)")
    ax1.set_zlabel("Z-axis (mm)")
    ax1.set_title("Isometric View")
    # Highlight origin (0,0,0) in 3D
    ax1.scatter([0], [0], [0], c='red', s=50, marker='o')
    ax1.invert_xaxis()
    ax1.invert_yaxis()
    ax1.view_init(elev=45, azim=45)

    # Y-Z Plane View (bottom-right)
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.scatter(display_points[:, 1], display_points[:, 2], s=1, c='blue')
    ax2.set_xlabel("Y-axis (mm)")
    ax2.set_ylabel("Z-axis (mm)")
    ax2.set_title("Y-Z Plane")
    ax2.grid(True)
    # Highlight origin (0,0) for Y-Z plane
    ax2.scatter(0, 0, c='red', s=50, marker='o')
    ax2.yaxis.set_label_position("right")
    ax2.yaxis.tick_right()
    ax2.invert_xaxis()

    # Y-X Plane View (middle-right)
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.scatter(display_points[:, 1], display_points[:, 0], s=1, c='blue')
    ax3.set_xlabel("Y-axis (mm)")
    ax3.set_ylabel("X-axis (mm)")
    ax3.set_title("Y-X Plane")
    ax3.grid(True)
    # Highlight origin (0,0) for Y-X plane
    ax3.scatter(0, 0, c='red', s=50, marker='o')
    ax3.yaxis.set_label_position("right")
    ax3.yaxis.tick_right()
    ax3.invert_xaxis()

    # X-Z Plane View (top-right)
    ax2 = fig.add_subplot(gs[2, 1])
    ax2.scatter(display_points[:, 0], display_points[:, 2], s=1, c='blue')
    ax2.set_xlabel("X-axis (mm)")
    ax2.set_ylabel("Z-axis (mm)")
    ax2.set_title("X-Z Plane")
    ax2.grid(True)
    # Highlight origin (0,0) for X-Z plane
    ax2.scatter(0, 0, c='red', s=50, marker='o')
    ax2.yaxis.set_label_position("right")
    ax2.yaxis.tick_right()
    
    plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust layout to make room for the title
    plt.show()

if __name__ == '__main__':
    main()