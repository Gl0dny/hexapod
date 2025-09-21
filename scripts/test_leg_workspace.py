#!/usr/bin/env python3

import csv
import time
import os
import sys
import logging
from pathlib import Path

# Add the project root to the path so we can import hexapod modules
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from hexapod.robot import Hexapod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("test_workspace.log"), logging.StreamHandler()],
)


def main():
    config_path = "/home/hexapod/hexapod/src/robot/config/hexapod_config.yaml"
    calibration_data_path = "/home/hexapod/hexapod/src/robot/config/calibration.json"
    workspace_csv = "leg_workspace.csv"
    delay_seconds = 0.1  # Delay between each movement
    leg_index = 0  # Index of the leg to move

    hexapod = Hexapod(
        config_path=config_path, calibration_data_path=calibration_data_path
    )

    try:
        with open(workspace_csv, "r") as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)  # Skip header
            for row in reader:
                if len(row) >= 3:
                    try:
                        coxa_deg = float(row[0])
                        femur_deg = float(row[1])
                        tibia_deg = float(row[2])
                        logging.info(
                            f"Moving leg {leg_index} to angles: Coxa={coxa_deg}, Femur={femur_deg}, Tibia={tibia_deg}"
                        )
                        try:
                            hexapod.move_leg_angles(
                                leg_index, coxa_deg, femur_deg, tibia_deg
                            )
                            time.sleep(delay_seconds)
                        except Exception as e:
                            logging.exception(
                                f"Error moving leg {leg_index} to angles Coxa={coxa_deg}, Femur={femur_deg}, Tibia={tibia_deg}: {e}"
                            )
                    except ValueError:
                        logging.warning(f"Invalid data row: {row}. Skipping.")
    except FileNotFoundError:
        logging.exception(f"File {workspace_csv} not found.")


if __name__ == "__main__":
    main()
