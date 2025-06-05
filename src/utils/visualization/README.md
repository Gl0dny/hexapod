# Visualization Utilities

This directory contains visualization and plotting utilities for the hexapod project. These tools help in analyzing and understanding the robot's kinematics, workspace, and other geometric properties.

## Available Tools

### Leg Workspace Visualization (`plot_leg_workspace.py`)

A tool for visualizing and analyzing the reachable workspace of a hexapod leg.

**Features:**
- Computes and visualizes the 3D workspace of a single leg
- Shows multiple 2D projections (X-Y, Y-Z, X-Z planes)
- Displays range information for each axis
- Caches results in CSV format for faster subsequent runs
- Supports angle limit configurations from the hexapod config

**Usage:**
```bash
cd src
python -m utils.visualization.plot_leg_workspace [--clean]
```

**Options:**
- `--clean`: Remove existing workspace data and recalculate

**Output:**
- Interactive 3D plot showing:
  - Isometric view of the workspace
  - Three 2D projections
  - Range information for each axis
  - Origin point highlighted in red
- CSV file (`leg_workspace.csv`) containing:
  - Joint angles (coxa, femur, tibia)
  - End-effector positions (x, y, z)

**Dependencies:**
- numpy
- matplotlib
- robot (project module)

## Notes

- The workspace visualization uses the hexapod's configuration from `src/robot/config/hexapod_config.yaml`
- Results are cached in `leg_workspace.csv` for faster subsequent runs
- The visualization assumes the leg is in its default position (leg 0)
- All measurements are in millimeters 