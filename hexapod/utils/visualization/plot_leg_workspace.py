#!/usr/bin/env python3
# type: ignore

import argparse
import contextlib
import csv
import io
import sys
from pathlib import Path
from unittest.mock import patch

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np

from hexapod.robot import Hexapod


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean workspace CSV file before calculations.",
    )
    args = parser.parse_args()

    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent.parent
    data_dir = project_root / "data" / "visualization"
    data_dir.mkdir(parents=True, exist_ok=True)
    csv_path = data_dir / "leg_workspace.csv"

    if args.clean and csv_path.exists():
        try:
            csv_path.unlink()
        except OSError as e:
            print(f"Error removing '{csv_path}': {e}")
            sys.exit(1)

    try:
        # Initialize Hexapod instance with mocked serial and IMU
        with (
            patch("hexapod.robot.hexapod.MaestroUART"),
            patch("hexapod.robot.sensors.imu.Imu"),
        ):
            hexapod = Hexapod(
                config_path=project_root
                / "hexapod"
                / "robot"
                / "config"
                / "hexapod_config.yaml",
                calibration_data_path=project_root
                / "hexapod"
                / "robot"
                / "config"
                / "calibration.json",
            )
    except Exception as e:
        print(f"Error initializing Hexapod: {e}")
        sys.exit(1)

    # Define angle ranges based on configuration
    coxa_min = hexapod.coxa_params.get("angle_limit_min") or hexapod.coxa_params.get(
        "angle_min"
    )
    coxa_max = hexapod.coxa_params.get("angle_limit_max") or hexapod.coxa_params.get(
        "angle_max"
    )
    femur_min = hexapod.femur_params.get("angle_limit_min") or hexapod.femur_params.get(
        "angle_min"
    )
    femur_max = hexapod.femur_params.get("angle_limit_max") or hexapod.femur_params.get(
        "angle_max"
    )
    tibia_min = hexapod.tibia_params.get("angle_limit_min") or hexapod.tibia_params.get(
        "angle_min"
    )
    tibia_max = hexapod.tibia_params.get("angle_limit_max") or hexapod.tibia_params.get(
        "angle_max"
    )
    print(
        f"Angle ranges: Coxa ({coxa_min}, {coxa_max}), Femur ({femur_min}, {femur_max}), Tibia ({tibia_min}, {tibia_max})"
    )

    angle_step = 2  # Define step size for angles

    coxa_angles = range(coxa_min, coxa_max + 1, angle_step)
    femur_angles = range(femur_min, femur_max + 1, angle_step)
    tibia_angles = range(tibia_min, tibia_max + 1, angle_step)

    leg_workspace = []

    # Check if 'leg_workspace.csv' exists
    if csv_path.exists():
        try:
            with open(csv_path, "r") as csvfile:
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
        except Exception as e:
            print(f"Error reading '{csv_path}': {e}")
            sys.exit(1)
    else:
        try:
            for coxa in coxa_angles:
                for femur in femur_angles:
                    for tibia in tibia_angles:
                        try:
                            with contextlib.redirect_stdout(io.StringIO()):
                                x, y, z = hexapod.legs[0].compute_forward_kinematics(
                                    coxa, femur, tibia
                                )
                            # Store angles plus computed position
                            leg_workspace.append((coxa, femur, tibia, x, y, z))
                        except ValueError:
                            pass

            # Convert to numpy array for easier plotting
            leg_workspace = np.array(leg_workspace)
        except Exception as e:
            print(f"Error computing workspace: {e}")
            sys.exit(1)

        try:
            with open(csv_path, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["coxa_deg", "femur_deg", "tibia_deg", "x", "y", "z"])
                writer.writerows(leg_workspace)
        except Exception as e:
            print(f"Error writing '{csv_path}': {e}")
            sys.exit(1)

    # Convert to numpy array if loaded from CSV
    if not isinstance(leg_workspace, np.ndarray):
        leg_workspace = np.array(leg_workspace)

    try:
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
        ax1 = fig.add_subplot(gs[:, 0], projection="3d")
        ax1.scatter(
            display_points[:, 0],
            display_points[:, 1],
            display_points[:, 2],
            s=1,
            c="blue",
        )
        ax1.set_xlabel("X-axis [mm]")
        ax1.set_ylabel("Y-axis [mm]")
        ax1.set_zlabel("Z-axis [mm]")
        ax1.set_title("Isometric View")

        # Highlight origin (0,0,0) in 3D
        ax1.scatter([0], [0], [0], c="red", s=50, marker="o")
        ax1.invert_xaxis()
        ax1.invert_yaxis()
        ax1.view_init(elev=45, azim=45)

        # Compute maxima and minima
        max_x = np.max(display_points[:, 0])
        min_x = np.min(display_points[:, 0])
        max_y = np.max(display_points[:, 1])
        min_y = np.min(display_points[:, 1])
        max_z = np.max(display_points[:, 2])
        min_z = np.min(display_points[:, 2])

        # Highlight ranges in 3D view legend
        ax1.scatter([], [], c="green", label=f"X Range ({min_x:.2f}, {max_x:.2f})")
        ax1.scatter([], [], c="blue", label=f"Y Range ({min_y:.2f}, {max_y:.2f})")
        ax1.scatter([], [], c="red", label=f"Z Range ({min_z:.2f}, {max_z:.2f})")

        # Move legend outside the plot
        ax1.legend(loc="center left", bbox_to_anchor=(-0.2, 0.1))

        # Y-Z Plane View (bottom-right)
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.scatter(display_points[:, 1], display_points[:, 2], s=1, c="blue")
        ax2.set_xlabel("Y-axis [mm]")
        ax2.set_ylabel("Z-axis [mm]")
        ax2.set_title("Y-Z Plane")
        ax2.grid(True)
        # Highlight origin (0,0) for Y-Z plane
        ax2.scatter(0, 0, c="red", s=50, marker="o")
        ax2.yaxis.set_label_position("right")
        ax2.yaxis.tick_right()
        ax2.invert_xaxis()

        # Y-X Plane View (middle-right)
        ax3 = fig.add_subplot(gs[1, 1])
        ax3.scatter(display_points[:, 1], display_points[:, 0], s=1, c="blue")
        ax3.set_xlabel("Y-axis [mm]")
        ax3.set_ylabel("X-axis [mm]")
        ax3.set_title("Y-X Plane")
        ax3.grid(True)
        # Highlight origin (0,0) for Y-X plane
        ax3.scatter(0, 0, c="red", s=50, marker="o")
        ax3.yaxis.set_label_position("right")
        ax3.yaxis.tick_right()
        ax3.invert_xaxis()

        # X-Z Plane View (top-right)
        ax2 = fig.add_subplot(gs[2, 1])
        ax2.scatter(display_points[:, 0], display_points[:, 2], s=1, c="blue")
        ax2.set_xlabel("X-axis [mm]")
        ax2.set_ylabel("Z-axis [mm]")
        ax2.set_title("X-Z Plane")
        ax2.grid(True)
        # Highlight origin (0,0) for X-Z plane
        ax2.scatter(0, 0, c="red", s=50, marker="o")
        ax2.yaxis.set_label_position("right")
        ax2.yaxis.tick_right()

        plt.tight_layout(
            rect=[0, 0, 1, 0.95]
        )  # Adjust layout to make room for the title
        plt.show()
    except Exception as e:
        print(f"Error during plotting: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
