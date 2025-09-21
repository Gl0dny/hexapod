# Scripts Directory

This directory contains interactive scripts and demos for testing and demonstrating hexapod functionality.

## Interactive Scripts

### Movement & Kinematics
- `interactive_body_ik.py` - Interactive body inverse kinematics testing
- `gait_generator_tester.py` - Gait generation testing and demonstration
- `leg_workspace.py` - Leg workspace analysis and 3D visualization

### Voice Control Testing
- `test_picovoice_file.py` - Picovoice file-based testing
- `test_picovoice_raw_file.py` - Picovoice raw audio file testing
- `test_porcupine_file.py` - Porcupine wake word file testing
- `test_rhino_file.py` - Rhino intent recognition file testing

## Usage

These scripts are designed for interactive testing and demonstration purposes. They are not part of the automated test suite but provide hands-on ways to test specific functionality.

Run any script with:
```bash
python scripts/script_name.py
```

## Script Descriptions

### Movement & Kinematics Scripts

**`interactive_body_ik.py`**
- Interactive body inverse kinematics testing
- Allows real-time manipulation of hexapod body position
- Tests body positioning and orientation capabilities

**`gait_generator_tester.py`**
- Step-by-step hexapod gait testing and demonstration
- Basic hexapod initialization and setup
- Tests tripod gait generation and movement
- Educational script for understanding gait patterns

**`leg_workspace.py`**
- Leg workspace analysis and 3D visualization
- Generates comprehensive 3D plots of leg reachable workspace
- Shows multiple view projections (isometric, Y-Z, Y-X, X-Z planes)
- Saves/loads workspace data to/from CSV files
- Uses actual hexapod configuration for angle limits
- Able to run outside of target machine with mocked hardware dependencies
- Usage: `python scripts/leg_workspace.py [--clean]`

### Voice Control Testing Scripts

**`test_picovoice_file.py`**
- Picovoice file-based testing
- Tests wake word detection and intent recognition with audio files

**`test_picovoice_raw_file.py`**
- Picovoice raw audio file testing
- Tests with raw audio data formats

**`test_porcupine_file.py`**
- Porcupine wake word file testing
- Tests wake word detection specifically

**`test_rhino_file.py`**
- Rhino intent recognition file testing
- Tests intent recognition and command processing
