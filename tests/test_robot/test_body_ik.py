import sys
import os
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from robot.hexapod import Hexapod

def main():
    config_path = Path('../../src/robot/config/hexapod_config.yaml')
    calibration_data_path = Path('../../src/robot/config/calibration.json')
    hexapod = Hexapod(config_path=config_path, calibration_data_path=calibration_data_path)
    
    # Example 1: Pure tz translation (20 mm)
    print("Example 1 - tz translation(20 mm):")
    hexapod.move_body(tz=20)

if __name__ == '__main__':
    main()
